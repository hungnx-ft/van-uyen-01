from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class SubmissionAnswerCreate(BaseModel):
    practice_question_id: Optional[int] = None
    mock_question_id: Optional[int] = None
    student_answer: str

class SubmissionCreate(BaseModel):
    exam_type: str
    practice_exam_id: Optional[int] = None
    mock_exam_id: Optional[int] = None
    answers: List[SubmissionAnswerCreate]
    attempt: int = 1
    submitted_at: Optional[datetime] = None

class AntiCheatEvent(BaseModel):
    submission_id: int
    event_type: str

class SubmissionScoreCreate(BaseModel):
    answer_id: int
    score: float
    teacher_comment: Optional[str] = None

class SubmissionScoreResponse(BaseModel):
    id: int
    answer_id: int
    score: float
    teacher_comment: Optional[str] = None
    teacher_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SubmissionAnswerResponse(BaseModel):
    id: int
    practice_question_id: Optional[int]
    mock_question_id: Optional[int]
    student_answer: str
    score: Optional[SubmissionScoreResponse] = None
    model_config = ConfigDict(from_attributes=True)

class SubmissionResponse(BaseModel):
    id: int
    student_id: int
    student_name: str = ""
    exam_type: str
    practice_exam_id: Optional[int]
    mock_exam_id: Optional[int]
    leave_tab_count: int
    status: str
    created_at: datetime
    attempt: int
    submitted_at: Optional[datetime] = None
    self_score: Optional[float] = None
    teacher_score: Optional[float] = None
    teacher_comment: Optional[str] = None
    answers: List[SubmissionAnswerResponse]
    model_config = ConfigDict(from_attributes=True)

class GradeSubmissionRequest(BaseModel):
    scores: List[SubmissionScoreCreate]
    teacher_comment: Optional[str] = None
