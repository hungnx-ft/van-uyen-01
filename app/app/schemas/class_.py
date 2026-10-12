from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

ClassName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
SchoolYear = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{4}$")]


class ClassCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: ClassName
    year: SchoolYear | None = None

    @field_validator("year")
    @classmethod
    def consecutive_years(cls, value):
        if value is not None and int(value[5:]) != int(value[:4]) + 1:
            raise ValueError("School year must contain two consecutive years, e.g. 2025-2026")
        return value


class ClassUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: ClassName | None = None
    year: SchoolYear | None = None

    @field_validator("name")
    @classmethod
    def name_not_null(cls, value):
        if value is None:
            raise ValueError("Class name cannot be null")
        return value

    @field_validator("year")
    @classmethod
    def consecutive_years(cls, value):
        return ClassCreate.consecutive_years(value)


class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    year: str | None
    teacher_id: int
    is_archived: bool
    archived_at: datetime | None
    created_at: datetime


class ClassDetail(ClassResponse):
    student_count: int
