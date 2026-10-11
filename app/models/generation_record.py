from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class GenerationRecord(BaseModel):
    id: str
    created_at: datetime
    prompt: str
    detected_concept: str
    purpose: str
    grade_group: str
    complexity: str
    color_requirement: str
    width: int
    height: int
    selected_pipeline: str
    elapsed_ms: float
    output_file: str
    output_size_bytes: int
    status: Literal["success", "failed"]
    quality_checks_json: str
    fallback_used: bool = False
    fallback_pipeline: str | None = None
    reason: str | None = None