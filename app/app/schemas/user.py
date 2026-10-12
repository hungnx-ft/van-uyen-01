from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Username = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=100,
                                            pattern=r"^[a-zA-Z0-9_.@+-]+$")]
FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Password = Annotated[str, Field(min_length=8, max_length=72)]


class AccountCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Username
    password: Password
    full_name: FullName
    school_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value


class RegisterRequest(AccountCreate):
    """Public registration cannot supply role, status, or class membership."""


class UserCreate(AccountCreate):
    # Kept for the existing teacher-created student endpoint.
    role: Literal["Student"] = "Student"
    class_id: int = Field(gt=0)


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=72)
    new_password: Password

    @field_validator("new_password")
    @classmethod
    def password_bytes(cls, value):
        return AccountCreate.password_bytes(value)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: Password

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value):
        return AccountCreate.password_bytes(value)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    school_name: str | None
    role: Literal["Teacher", "Student"]
    class_id: int | None
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str = Field(min_length=32, max_length=256)
