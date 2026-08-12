import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeProcessRequest(BaseModel):
    process_name: str = Field(..., min_length=3, max_length=200)
    value_chain_id: uuid.UUID
    process_context: str | None = Field(None, max_length=1000)


class AnalysisJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_type: str
    input_name: str
    input_context: str | None
    status: str
    current_stage: str | None
    model_used: str | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    result_entity_id: uuid.UUID | None
    error_message: str | None
    stage_log: list
