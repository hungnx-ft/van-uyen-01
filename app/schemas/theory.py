from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from typing import Literal, Optional
from datetime import datetime


class TheoryArticleBase(BaseModel):
    title: str
    # 'mixed' for combined posts; legacy values are kept for old rows.
    content_type: str = "mixed"
    content: str = ""
    main_category: Optional[str] = None
    sub_category: Optional[str] = None
    description: str = ""
    icon: str = "📚"

class TheoryArticleCreate(TheoryArticleBase):
    pass

class TheoryArticleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = None
    content_type: Optional[str] = None
    content: Optional[str] = None
    main_category: Optional[str] = None
    sub_category: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None


class TheoryLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: HttpUrl
    title: str = Field(default="", max_length=255)


class TheoryAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: Literal["image", "file", "link"]
    url: Optional[str] = None
    original_name: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    position: int


class TheoryArticleResponse(TheoryArticleBase):
    id: int
    teacher_id: int
    created_at: datetime
    attachments: list[TheoryAttachmentResponse] = []
    model_config = ConfigDict(from_attributes=True)
