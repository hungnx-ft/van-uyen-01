from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from typing import Annotated, List, Optional
from datetime import datetime

MAX_QUESTION_SCORE = 20


def _two_decimals(value: float) -> float:
    value = round(value, 2)
    if value <= 0:
        raise ValueError("Question score must be at least 0.01")
    return value


# Each question carries its own score; the exam total is their sum.
QuestionScore = Annotated[float, Field(gt=0, le=MAX_QUESTION_SCORE, allow_inf_nan=False),
                          AfterValidator(_two_decimals)]


class PracticeQuestionBase(BaseModel):
    content: str
    max_score: float
    answer_key: str = ""

class PracticeQuestionCreate(PracticeQuestionBase):
    max_score: QuestionScore

class PracticeQuestionResponse(PracticeQuestionBase):
    id: int
    exam_id: int
    model_config = ConfigDict(from_attributes=True)

class PracticeExamBase(BaseModel):
    title: str
    target_group: Optional[str] = None
    passage: str = ""
    genre: Optional[str] = None
    duration_minutes: int = Field(default=45, ge=1, le=1440)

class PracticeExamCreate(PracticeExamBase):
    questions: List[PracticeQuestionCreate] = Field(min_length=1, max_length=100)

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
    max_score: QuestionScore

class MockQuestionResponse(MockQuestionBase):
    id: int
    exam_id: int
    model_config = ConfigDict(from_attributes=True)

class MockExamBase(BaseModel):
    title: str
    target_group: Optional[str] = None
    passage: str = ""
    genre: Optional[str] = None
    duration_minutes: int = Field(default=120, ge=1, le=1440)

class MockExamCreate(MockExamBase):
    questions: List[MockQuestionCreate] = Field(min_length=1, max_length=100)

class MockExamResponse(MockExamBase):
    id: int
    teacher_id: int
    created_at: datetime
    questions: List[MockQuestionResponse]
    model_config = ConfigDict(from_attributes=True)
