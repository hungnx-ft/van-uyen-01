from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AssignmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    class_id: int = Field(gt=0)
    exam_type: Literal["Practice", "Mock"]
    practice_exam_id: int | None = Field(default=None, gt=0)
    mock_exam_id: int | None = Field(default=None, gt=0)
    exam_title: str = Field(min_length=1, max_length=300)
    instructions: str = ""


class AssignmentResponse(AssignmentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    teacher_id: int
    created_at: datetime
