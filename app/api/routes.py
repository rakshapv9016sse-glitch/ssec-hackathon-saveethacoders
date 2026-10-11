import datetime
import json
import time
import uuid
import xml.etree.ElementTree as ET

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from resvg_py import svg_to_bytes

from ..config import IMAGE_DIR
from ..database import db
from ..models.generation_record import GenerationRecord
from ..schemas import (
    BenchmarkResponse,
    ClassificationResponse,
    ClassifyRequest,
    GenerateRequest,
    GenerationResponse,
    HealthResponse,
    MetricsResponse,
    PipelineResponse,
    PurposeInfo,
    QualityChecks,
)
from ..services.benchmark import run_benchmark
from ..services.classifier import classify
from ..services.fallback_renderer import render_fallback_png
from ..services.image_optimizer import optimize_png
from ..services.optional_diffusion import status as diffusion_status
from ..services.quality_checker import check_png
from ..services.router import PIPELINES, choose_pipeline
from ..services.svg_generator import generate_svg
from ..services.purpose_engine import evaluate_request

router = APIRouter(prefix="/api")
PURPOSES = [
    {"id": "coloring_worksheet", "name": "Coloring worksheet", "recommended": "Black outlines, white background, print-friendly"},
    {"id": "educational_flashcard", "name": "Educational flashcard", "recommended": "Color illustration with separate label"},
    {"id": "classroom_poster", "name": "Classroom poster", "recommended": "Layered composition with title and supporting text"},
    {"id": "official_publication", "name": "Official publication poster", "recommended": "High-resolution vector layout; human editorial review required"},
]


def _performance_snapshot():
    try:
        with db() as con:
            rows = con.execute(
                "SELECT selected_pipeline, AVG(elapsed_ms) AS elapsed_ms FROM generations WHERE status='success' GROUP BY selected_pipeline"
            ).fetchall()
        return {row["selected_pipeline"]: {"elapsed_ms": row["elapsed_ms"]} for row in rows}
    except Exception:
        return {}


@router.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "pipelines": list(PIPELINES), "optional_diffusion": diffusion_status()}


@router.get("/purposes", response_model=list[PurposeInfo])
def purposes():
    return PURPOSES


@router.get("/pipelines", response_model=list[PipelineResponse])
def pipelines():
    return [
        PipelineResponse(pipeline=name, available=name != "optional_local_diffusion", description=description)
        for name, description in {**PIPELINES, "optional_local_diffusion": "Disabled by default; startup does not require model weights."}.items()
    ]


@router.post("/classify", response_model=ClassificationResponse)
def classify_route(req: ClassifyRequest):
    return classify(req.prompt)


@router.post("/generate", response_model=GenerationResponse)
def generate(req: GenerateRequest):
    evaluated = evaluate_request(
        req.prompt, req.purpose, req.grade_group, req.complexity,
        req.color_requirement, req.width, req.height, req.usage,
        req.quality_preference, _performance_snapshot(),
    )
    classification = evaluated.get("classification")
    if not evaluated.get("valid"):
        raise HTTPException(422, evaluated.get("message") or "The prompt needs clarification.")
    if classification.get("inferred_purpose") and classification["inferred_purpose"] != req.purpose:
        raise HTTPException(422, f"The prompt suggests {classification['inferred_purpose']}; confirm or change the requested purpose.")
    if not evaluated.get("color_requirement_satisfied", True):
        raise HTTPException(422, evaluated["message"])

    route = choose_pipeline(
        req.purpose, req.complexity, req.width, req.height,
        req.usage, req.quality_preference, _performance_snapshot(),
    )
    image_id = str(uuid.uuid4())
    start = time.perf_counter()
    fallback_used = False
    fallback_pipeline = None
    try:
        svg, subject = generate_svg(req.prompt, req.purpose, req.width, req.height, req.grade_group, req.complexity)
        try:
            root = ET.fromstring(svg)
            if root.tag.rsplit("}", 1)[-1] != "svg":
                raise ValueError("Generated document is not an SVG.")
            png = svg_to_bytes(svg_string=svg, width=req.width, height=req.height)
        except Exception:
            subject = evaluated["detected_concept"]
            png = render_fallback_png(subject, req.purpose, req.width, req.height, req.grade_group)
            fallback_used = True
            fallback_pipeline = "pillow_fallback"
        png = optimize_png(png, req.width, req.height, grayscale=req.purpose == "coloring_worksheet")
        filename = f"{image_id}.png"
        path = IMAGE_DIR / filename
        path.write_bytes(png)
        checks = check_png(png, req.width, req.height, req.purpose, path)
        if not checks["passed"]:
            path.unlink(missing_ok=True)
            raise RuntimeError("Generated PNG failed objective quality checks.")
        elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
        created_at = datetime.datetime.now(datetime.timezone.utc)
        reason = route["reason"]
        if fallback_used:
            reason += " The SVG renderer failed, so a local Pillow fallback produced the requested PNG."
        record = {
            "id": image_id,
            "created_at": created_at.isoformat(),
            "prompt": req.prompt,
            "detected_concept": subject,
            "purpose": req.purpose,
            "grade_group": req.grade_group,
            "complexity": req.complexity,
            "color_requirement": req.color_requirement,
            "width": req.width,
            "height": req.height,
            "actual_dimensions": {"width": req.width, "height": req.height},
            "selected_pipeline": route["selected_pipeline"],
            "elapsed_ms": elapsed_ms,
            "output_file": filename,
            "output_size_bytes": len(png),
            "status": "success",
            "quality_checks_json": json.dumps(checks),
            "fallback_used": int(fallback_used),
            "fallback_pipeline": fallback_pipeline,
            "reason": reason,
        }
        record["created_at"] = created_at
        persisted_record = GenerationRecord(**record).model_dump(mode="json")
        columns = tuple(persisted_record)
        with db() as con:
            con.execute(
                f"INSERT INTO generations ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                tuple(persisted_record[column] for column in columns),
            )
        return {
            "id": image_id,
            "created_at": created_at,
            "prompt": req.prompt,
            "detected_concept": subject,
            "purpose": req.purpose,
            "grade_group": req.grade_group,
            "complexity": req.complexity,
            "color_requirement": req.color_requirement,
            "width": req.width,
            "height": req.height,
            "actual_dimensions": {"width": req.width, "height": req.height},
            "selected_pipeline": route["selected_pipeline"],
            "reason": reason,
            "elapsed_ms": elapsed_ms,
            "output_size_bytes": len(png),
            "status": "success",
            "download_url": f"/api/images/{image_id}/download",
            "preview_url": f"/api/images/{image_id}",
            "quality_checks": checks,
            "fallback_used": fallback_used,
            "fallback_pipeline": fallback_pipeline,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, f"Image generation failed: {exc}") from exc


@router.get("/history", response_model=list[GenerationResponse])
def history(limit: int = Query(default=100, ge=1, le=500)):
    with db() as con:
        rows = con.execute("SELECT * FROM generations ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    items = []
    for row in rows:
        data = dict(row)
        items.append({
            "id": data["id"],
            "created_at": data["created_at"],
            "prompt": data["prompt"],
            "detected_concept": data["detected_concept"],
            "purpose": data["purpose"],
            "grade_group": data["grade_group"],
            "complexity": data["complexity"],
            "color_requirement": data["color_requirement"],
            "width": data["width"],
            "height": data["height"],
            "actual_dimensions": {"width": data["width"], "height": data["height"]},
            "selected_pipeline": data["selected_pipeline"],
            "reason": data["reason"] or "Purpose-aware local pipeline selected.",
            "elapsed_ms": data["elapsed_ms"],
            "output_size_bytes": data["output_size_bytes"],
            "status": "success",
            "download_url": f"/api/images/{data['id']}/download",
            "preview_url": f"/api/images/{data['id']}",
            "quality_checks": json.loads(data["quality_checks_json"]),
            "fallback_used": bool(data["fallback_used"]),
            "fallback_pipeline": data["fallback_pipeline"],
        })
    return items


@router.get("/metrics", response_model=MetricsResponse)
def metrics():
    with db() as con:
        total = con.execute("SELECT COUNT(*) FROM generations WHERE status='success'").fetchone()[0]
        by = con.execute("SELECT purpose,COUNT(*) n FROM generations WHERE status='success' GROUP BY purpose").fetchall()
        elapsed = con.execute("SELECT COALESCE(SUM(elapsed_ms),0) FROM generations WHERE status='success'").fetchone()[0]
        size = con.execute("SELECT COALESCE(SUM(output_size_bytes),0) FROM generations WHERE status='success'").fetchone()[0]
        bench = con.execute("SELECT COUNT(*) FROM benchmark_runs").fetchone()[0]
        fallback_count = con.execute("SELECT COUNT(*) FROM generations WHERE fallback_used=1").fetchone()[0]
    return {
        "successful_generations": total,
        "worksheet_images": sum(row["n"] for row in by if row["purpose"] == "coloring_worksheet"),
        "flashcards": sum(row["n"] for row in by if row["purpose"] == "educational_flashcard"),
        "posters": sum(row["n"] for row in by if row["purpose"] in ("classroom_poster", "official_publication")),
        "total_processing_ms": round(elapsed, 3),
        "total_output_size_bytes": size,
        "fallback_count": fallback_count,
        "pipeline_usage": [{"purpose": row["purpose"], "count": row["n"]} for row in by],
        "benchmark_records": bench,
    }


@router.post("/benchmark", response_model=BenchmarkResponse)
def benchmark():
    return {
        "results": run_benchmark(),
        "cost_note": "No hypothetical cloud price is configured. Results report measured local runtime and output size only.",
        "assumptions": "Baseline and optimized runs use the same generated SVG concept and purpose; output dimensions are reported per result. Timing excludes model inference because no model is used.",
    }


def _safe_image(image_id: str):
    try:
        uuid.UUID(image_id)
    except ValueError as exc:
        raise HTTPException(404, "Image not found") from exc
    with db() as con:
        row = con.execute("SELECT output_file FROM generations WHERE id=? AND status='success'", (image_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Image not found")
    path = (IMAGE_DIR / row["output_file"]).resolve()
    if path.parent != IMAGE_DIR.resolve() or not path.is_file():
        raise HTTPException(404, "Image not found")
    return path


@router.get("/images/{image_id}")
def get_image(image_id: str):
    return FileResponse(_safe_image(image_id), media_type="image/png")


@router.get("/images/{image_id}/download")
def download_image(image_id: str):
    return FileResponse(_safe_image(image_id), media_type="image/png", filename=f"smartgen-{image_id[:8]}.png")
