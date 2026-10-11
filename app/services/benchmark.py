import datetime
import json
import time
import uuid

from resvg_py import svg_to_bytes

from ..database import db
from .fallback_renderer import render_fallback_png
from .image_optimizer import optimize_png
from .quality_checker import check_png
from .router import choose_pipeline
from .svg_generator import generate_svg


def reduction_percent(baseline, optimized):
    if baseline is None or baseline <= 0:
        return None
    return round((baseline - optimized) / baseline * 100, 2)


CASES = [
    ("b01", "elephant coloring worksheet", "coloring_worksheet"),
    ("b02", "cat coloring worksheet", "coloring_worksheet"),
    ("b03", "dog flashcard", "educational_flashcard"),
    ("b04", "butterfly flashcard", "educational_flashcard"),
    ("b05", "fish classroom poster", "classroom_poster"),
    ("b06", "bird classroom poster", "classroom_poster"),
    ("b07", "flower coloring worksheet", "coloring_worksheet"),
    ("b08", "tree flashcard", "educational_flashcard"),
    ("b09", "sun classroom poster", "classroom_poster"),
    ("b10", "fruit official publication", "official_publication"),
]


def _measure_render(svg, width, height, subject, purpose, prompt):
    started = time.perf_counter()
    fallback_used = False
    try:
        png = svg_to_bytes(svg_string=svg, width=width, height=height)
    except Exception:
        png = render_fallback_png(subject, purpose, width, height)
        fallback_used = True
    png = optimize_png(png, width, height, grayscale=purpose == "coloring_worksheet")
    elapsed_ms = (time.perf_counter() - started) * 1000
    checks = check_png(png, width, height, purpose)
    return {
        "elapsed_ms": round(elapsed_ms, 3),
        "size_bytes": len(png),
        "width": width,
        "height": height,
        "quality_checks": checks,
        "success": checks["passed"],
        "fallback_used": fallback_used,
    }


def run_benchmark():
    results = []
    for case_id, prompt, purpose in CASES:
        try:
            svg, subject = generate_svg(prompt, purpose, 800, 1000)
            baseline = _measure_render(svg, 1200, 1500, subject, purpose, prompt)
            started = time.perf_counter()
            fallback_used = False
            try:
                optimized = svg_to_bytes(svg_string=svg, width=800, height=1000)
            except Exception:
                optimized = render_fallback_png(subject, purpose, 800, 1000)
                fallback_used = True
            optimized = optimize_png(optimized, 800, 1000, grayscale=purpose == "coloring_worksheet")
            optimized_elapsed = round((time.perf_counter() - started) * 1000, 3)
            optimized_checks = check_png(optimized, 800, 1000, purpose)
            optimized_measurement = {
                "elapsed_ms": optimized_elapsed,
                "size_bytes": len(optimized),
                "width": 800,
                "height": 1000,
                "quality_checks": optimized_checks,
                "success": optimized_checks["passed"],
                "fallback_used": fallback_used,
            }
            chosen = choose_pipeline(purpose)
            result = {
                "test_case_id": case_id,
                "prompt": prompt,
                "purpose": purpose,
                "baseline_pipeline": "fixed_settings_svg_1200x1500",
                "optimized_pipeline": chosen["selected_pipeline"],
                "baseline": baseline,
                "optimized": optimized_measurement,
                "baseline_elapsed_ms": baseline["elapsed_ms"],
                "optimized_elapsed_ms": optimized_elapsed,
                "baseline_size_bytes": baseline["size_bytes"],
                "optimized_size_bytes": len(optimized),
                "baseline_dimensions": [baseline["width"], baseline["height"]],
                "optimized_dimensions": [800, 1000],
                "baseline_quality_status": baseline["success"],
                "optimized_quality_status": optimized_checks["passed"],
                "time_reduction_percent": reduction_percent(baseline["elapsed_ms"], optimized_elapsed),
                "size_reduction_percent": reduction_percent(baseline["size_bytes"], len(optimized)),
                "fallback_count": int(baseline["fallback_used"]) + int(fallback_used),
                "notes": "Same subject SVG and purpose; fixed baseline is 1200x1500, optimized output is 800x1000 and applies worksheet grayscale/PNG optimization. Runtime is local rendering, not model inference.",
            }
        except Exception as exc:
            result = {
                "test_case_id": case_id,
                "prompt": prompt,
                "purpose": purpose,
                "baseline_pipeline": "fixed_settings_svg_1200x1500",
                "optimized_pipeline": choose_pipeline(purpose)["selected_pipeline"],
                "success": False,
                "error": str(exc),
                "baseline_elapsed_ms": None,
                "optimized_elapsed_ms": None,
                "baseline_size_bytes": None,
                "optimized_size_bytes": None,
                "baseline_dimensions": None,
                "optimized_dimensions": None,
                "baseline_quality_status": False,
                "optimized_quality_status": False,
                "time_reduction_percent": None,
                "size_reduction_percent": None,
                "fallback_count": 0,
                "notes": "Case failed before valid measurements were available.",
            }
        with db() as con:
            con.execute(
                """INSERT INTO benchmark_runs (
                    id,created_at,test_case_id,baseline_pipeline,optimized_pipeline,
                    baseline_elapsed_ms,optimized_elapsed_ms,baseline_size_bytes,optimized_size_bytes,
                    baseline_quality_status,optimized_quality_status,estimated_cost,cost_assumptions,notes,
                    baseline_width,baseline_height,optimized_width,optimized_height,fallback_count
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()), datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    case_id, result["baseline_pipeline"], result["optimized_pipeline"],
                    result.get("baseline_elapsed_ms") or 0, result.get("optimized_elapsed_ms") or 0,
                    result.get("baseline_size_bytes") or 0, result.get("optimized_size_bytes") or 0,
                    json.dumps(result.get("baseline_quality_status")),
                    json.dumps(result.get("optimized_quality_status")), None,
                    "No cloud prices, energy use, or financial savings are estimated.",
                    result["notes"],
                    *(result.get("baseline_dimensions") or [None, None]),
                    *(result.get("optimized_dimensions") or [None, None]),
                    result.get("fallback_count", 0),
                ),
            )
        results.append(result)
    return results
