from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.schemas.user import AccountCreate, FullName, Password, UserCreate, UserResponse, Username


class StudentCreate(UserCreate):
    password: Password | None = None

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value):
        return AccountCreate.password_bytes(value) if value is not None else None


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
    username: Username | None = None
    full_name: FullName
    password: Password | None = None
    school_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None


class BulkStudentCreate(BaseModel):
    class_id: int = Field(gt=0)
    students: list[BulkStudentItem] = Field(min_length=1, max_length=500)


class BulkStudentFailure(BaseModel):
    row: int
    username: str | None = None
    detail: str


class BulkStudentResult(BaseModel):
    created: list[StudentCredentials]
    failed: list[BulkStudentFailure]
