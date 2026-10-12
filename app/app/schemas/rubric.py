from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RubricResponse(BaseModel):
    id: int
    teacher_id: int
    exam_type: str
    practice_exam_id: int | None
    mock_exam_id: int | None
    content_text: str
    original_filename: str | None
    mime_type: str | None
    version: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RubricTextUpdate(BaseModel):
    content_text: str = Field(min_length=1, max_length=500_000)
