from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Purpose = Literal["coloring_worksheet", "educational_flashcard", "classroom_poster", "official_publication"]
Complexity = Literal["simple", "moderate", "detailed"]
ColorRequirement = Literal["black_white", "color", "auto"]


class ClassifyRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)

    @field_validator("prompt")
    @classmethod
    def trim_prompt(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Prompt cannot be blank.")
        return value


class GenerateRequest(ClassifyRequest):
    purpose: Purpose
    grade_group: str = Field(default="Grade 2", min_length=1, max_length=60)
    complexity: Complexity = "simple"
    color_requirement: ColorRequirement = "auto"
    width: int = Field(default=800, ge=256, le=2400)
    height: int = Field(default=1000, ge=256, le=2400)
    usage: Literal["print", "screen"] = "print"
    quality_preference: Literal["standard", "high"] = "standard"

    @field_validator("grade_group")
    @classmethod
    def trim_grade_group(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Grade group cannot be blank.")
        return value


class QualityChecks(BaseModel):
    passed: bool
    file_exists: bool | None = None
    readable: bool | None = None
    valid_png: bool | None = None
    dimensions_match: bool | None = None
    white_background: bool | None = None
    black_outlines: bool | None = None
    color_treatment: bool | None = None
    purpose_layout: bool | None = None
    notes: list[str] = Field(default_factory=list)


class ClassificationResponse(BaseModel):
    normalized_prompt: str
    supported: bool
    detected_concept: str | None
    ambiguous: bool
    inferred_purpose: Purpose | None = None
    requires_confirmation: bool = False
    suggested_purposes: list[Purpose] = Field(default_factory=list)
    message: str | None = None


class OptionalDiffusionStatus(BaseModel):
    enabled: bool
    available: bool
    message: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    pipelines: list[str]
    optional_diffusion: OptionalDiffusionStatus


class PurposeInfo(BaseModel):
    id: Purpose
    name: str
    recommended: str


class PipelineResponse(BaseModel):
    pipeline: str
    available: bool
    description: str


class PipelineUsage(BaseModel):
    purpose: Purpose
    count: int


class MetricsResponse(BaseModel):
    successful_generations: int
    worksheet_images: int
    flashcards: int
    posters: int
    total_processing_ms: float
    total_output_size_bytes: int
    fallback_count: int
    pipeline_usage: list[PipelineUsage]
    benchmark_records: int


class Dimensions(BaseModel):
    width: int
    height: int


class GenerationResponse(BaseModel):
    id: str
    created_at: datetime
    prompt: str
    detected_concept: str
    purpose: Purpose
    grade_group: str
    complexity: Complexity
    color_requirement: ColorRequirement
    width: int
    height: int
    actual_dimensions: Dimensions
    selected_pipeline: str
    reason: str
    elapsed_ms: float
    output_size_bytes: int
    status: Literal["success"]
    download_url: str
    preview_url: str
    quality_checks: QualityChecks
    fallback_used: bool
    fallback_pipeline: str | None = None


class ImageCheck(BaseModel):
    pipeline: str
    available: bool
    description: str


class BenchmarkResponse(BaseModel):
    results: list[dict[str, Any]]
    cost_note: str
    assumptions: str


class HistoryResponse(BaseModel):
    items: list[GenerationResponse]