from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.models.exam import MockExam, MockQuestion, PracticeExam, PracticeQuestion
from app.repositories.exam import practice_exam_repo, mock_exam_repo
from app.schemas.exam import PracticeExamCreate, MockExamCreate

def create_practice_exam(db: Session, exam_in: PracticeExamCreate, teacher_id: int):
    _validate_practice(exam_in)
    return practice_exam_repo.create_with_teacher(db, obj_in=exam_in, teacher_id=teacher_id)

def create_mock_exam(db: Session, exam_in: MockExamCreate, teacher_id: int):
    _validate_mock(exam_in)
    return mock_exam_repo.create_with_teacher(db, obj_in=exam_in, teacher_id=teacher_id)


def update_practice_exam(db: Session, exam_id: int, exam_in: PracticeExamCreate, teacher_id: int):
    _validate_practice(exam_in)
    exam = db.get(PracticeExam, exam_id)
    if exam is None or exam.teacher_id != teacher_id:
        raise HTTPException(404, "Exam not found")
    exam.title, exam.target_group, exam.passage, exam.genre, exam.duration_minutes = (
        exam_in.title, exam_in.target_group, exam_in.passage, exam_in.genre, exam_in.duration_minutes
    )
    exam.questions = [PracticeQuestion(content=q.content, max_score=q.max_score, answer_key=q.answer_key) for q in exam_in.questions]
    db.flush()
    db.refresh(exam)
    return exam


def update_mock_exam(db: Session, exam_id: int, exam_in: MockExamCreate, teacher_id: int):
    _validate_mock(exam_in)
    exam = db.get(MockExam, exam_id)
    if exam is None or exam.teacher_id != teacher_id:
        raise HTTPException(404, "Exam not found")
    exam.title, exam.target_group, exam.passage, exam.genre, exam.duration_minutes = (
        exam_in.title, exam_in.target_group, exam_in.passage, exam_in.genre, exam_in.duration_minutes
    )
    exam.questions = [MockQuestion(section=q.section, content=q.content, max_score=q.max_score, answer_key=q.answer_key) for q in exam_in.questions]
    db.flush()
    db.refresh(exam)
    return exam


def _validate_practice(exam_in: PracticeExamCreate):
    if any(q.max_score < 0 for q in exam_in.questions):
        raise HTTPException(422, "Question scores must be non-negative")


def _validate_mock(exam_in: MockExamCreate):
    if any(q.max_score < 0 for q in exam_in.questions):
        raise HTTPException(422, "Question scores must be non-negative")


def delete_exam(db: Session, exam_type: str, exam_id: int, teacher_id: int):
    model = PracticeExam if exam_type == "Practice" else MockExam
    exam = db.get(model, exam_id)
    if exam is None or exam.teacher_id != teacher_id:
        raise HTTPException(404, "Exam not found")
    if db.query(Assignment).filter((Assignment.practice_exam_id == exam_id) if exam_type == "Practice" else (Assignment.mock_exam_id == exam_id)).first() or exam.submissions:
        raise HTTPException(409, "Exam cannot be deleted after assignment or submission")
    db.delete(exam)
    db.flush()
