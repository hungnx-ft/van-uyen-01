from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.schemas.user import FullName, UserResponse


class StudentCreate(BaseModel):
    """The server generates the username and default password; extra fields are ignored."""
    full_name: FullName
    school_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None
    class_id: int = Field(gt=0)


class StudentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: FullName | None = None
    school_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None

    @field_validator("full_name")
    @classmethod
    def name_not_null(cls, value):
        if value is None:
            raise ValueError("Full name cannot be null")
        return value


class StudentStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_active: bool = Field(strict=True)


class StudentResponse(UserResponse):
    class_name: str | None
    class_year: str | None


class StudentCredentials(StudentResponse):
    temporary_password: str


class StudentPage(BaseModel):
    items: list[StudentResponse]
    total: int
    skip: int
    limit: int


class BulkStudentItem(BaseModel):
    full_name: FullName
    school_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None


class BulkStudentCreate(BaseModel):
    class_id: int = Field(gt=0)
    students: list[BulkStudentItem] = Field(min_length=1, max_length=500)


class BulkStudentFailure(BaseModel):
    row: int
    full_name: str | None = None
    detail: str


class BulkStudentResult(BaseModel):
    created: list[StudentCredentials]
    failed: list[BulkStudentFailure]
