from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ClassBase(BaseModel):
    name: str

class ClassCreate(ClassBase):
    pass

class ClassUpdate(ClassBase):
    pass

class ClassResponse(ClassBase):
    id: int
    teacher_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
