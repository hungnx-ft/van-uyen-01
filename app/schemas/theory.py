from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class TheoryArticleBase(BaseModel):
    title: str
    content_type: str
    content: str

class TheoryArticleCreate(TheoryArticleBase):
    pass

class TheoryArticleUpdate(BaseModel):
    title: Optional[str] = None
    content_type: Optional[str] = None
    content: Optional[str] = None

class TheoryArticleResponse(TheoryArticleBase):
    id: int
    teacher_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
