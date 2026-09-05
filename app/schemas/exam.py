from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class PracticeQuestionBase(BaseModel):
    content: str
    max_score: float = 0.8
    answer_key: str = ""

class PracticeQuestionCreate(PracticeQuestionBase):
    pass

class PracticeQuestionResponse(PracticeQuestionBase):
    id: int
    exam_id: int
    model_config = ConfigDict(from_attributes=True)

class PracticeExamBase(BaseModel):
    title: str
    target_group: Optional[str] = None
    passage: str = ""
    genre: Optional[str] = None

class PracticeExamCreate(PracticeExamBase):
    questions: List[PracticeQuestionCreate]

class PracticeExamResponse(PracticeExamBase):
    id: int
    teacher_id: int
    created_at: datetime
    questions: List[PracticeQuestionResponse]
    model_config = ConfigDict(from_attributes=True)

class MockQuestionBase(BaseModel):
    section: int
    content: str
    max_score: float
    answer_key: str = ""

class MockQuestionCreate(MockQuestionBase):
    pass

class MockQuestionResponse(MockQuestionBase):
    id: int
    exam_id: int
    model_config = ConfigDict(from_attributes=True)

class MockExamBase(BaseModel):
    title: str
    target_group: Optional[str] = None
    passage: str = ""
    genre: Optional[str] = None

class MockExamCreate(MockExamBase):
    questions: List[MockQuestionCreate]

class MockExamResponse(MockExamBase):
    id: int
    teacher_id: int
    created_at: datetime
    questions: List[MockQuestionResponse]
    model_config = ConfigDict(from_attributes=True)
