from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.models.exam import MockExam, MockQuestion, PracticeExam, PracticeQuestion
from app.repositories.exam import practice_exam_repo, mock_exam_repo
from app.schemas.exam import PracticeExamCreate, MockExamCreate

def create_practice_exam(db: Session, exam_in: PracticeExamCreate, teacher_id: int):
    # Validate exactly 5 questions
    if len(exam_in.questions) != 5:
        raise ValueError("Practice exam must have exactly 5 questions.")
    
    # Check total score
    if any(q.max_score < 0 for q in exam_in.questions):
        raise ValueError("Question scores must be non-negative.")
    total_score = sum(q.max_score for q in exam_in.questions)
    if abs(total_score - 4.0) > 0.01:
        raise ValueError("Practice exam total score must be 4.0.")
        
    return practice_exam_repo.create_with_teacher(db, obj_in=exam_in, teacher_id=teacher_id)

def create_mock_exam(db: Session, exam_in: MockExamCreate, teacher_id: int):
    # Validate section 1: 5 questions, section 2: 2 questions
    section_1 = [q for q in exam_in.questions if q.section == 1]
    section_2 = [q for q in exam_in.questions if q.section == 2]
    
    if len(section_1) != 5 or len(section_2) != 2:
        raise ValueError("Mock exam must have exactly 5 questions in Section 1 and 2 questions in Section 2.")
        
    # Check total score
    if any(q.max_score < 0 for q in exam_in.questions):
        raise ValueError("Question scores must be non-negative.")
    total_score = sum(q.max_score for q in exam_in.questions)
    if abs(total_score - 10.0) > 0.01:
        raise ValueError("Mock exam total score must be 10.0.")

    return mock_exam_repo.create_with_teacher(db, obj_in=exam_in, teacher_id=teacher_id)


def update_practice_exam(db: Session, exam_id: int, exam_in: PracticeExamCreate, teacher_id: int):
    _validate_practice(exam_in)
    exam = db.get(PracticeExam, exam_id)
    if exam is None or exam.teacher_id != teacher_id:
        raise HTTPException(404, "Exam not found")
    exam.title, exam.target_group, exam.passage, exam.genre = exam_in.title, exam_in.target_group, exam_in.passage, exam_in.genre
    exam.questions = [PracticeQuestion(content=q.content, max_score=q.max_score, answer_key=q.answer_key) for q in exam_in.questions]
    db.flush()
    db.refresh(exam)
    return exam


def update_mock_exam(db: Session, exam_id: int, exam_in: MockExamCreate, teacher_id: int):
    _validate_mock(exam_in)
    exam = db.get(MockExam, exam_id)
    if exam is None or exam.teacher_id != teacher_id:
        raise HTTPException(404, "Exam not found")
    exam.title, exam.target_group, exam.passage, exam.genre = exam_in.title, exam_in.target_group, exam_in.passage, exam_in.genre
    exam.questions = [MockQuestion(section=q.section, content=q.content, max_score=q.max_score, answer_key=q.answer_key) for q in exam_in.questions]
    db.flush()
    db.refresh(exam)
    return exam


def _validate_practice(exam_in: PracticeExamCreate):
    if len(exam_in.questions) != 5 or any(q.max_score < 0 for q in exam_in.questions) or abs(sum(q.max_score for q in exam_in.questions) - 4.0) > 0.01:
        raise HTTPException(422, "Practice exam must have exactly 5 questions and total score 4.0")


def _validate_mock(exam_in: MockExamCreate):
    if len([q for q in exam_in.questions if q.section == 1]) != 5 or len([q for q in exam_in.questions if q.section == 2]) != 2 or any(q.max_score < 0 for q in exam_in.questions) or abs(sum(q.max_score for q in exam_in.questions) - 10.0) > 0.01:
        raise HTTPException(422, "Mock exam must have 5 section 1 questions, 2 section 2 questions and total score 10.0")


def delete_exam(db: Session, exam_type: str, exam_id: int, teacher_id: int):
    model = PracticeExam if exam_type == "Practice" else MockExam
    exam = db.get(model, exam_id)
    if exam is None or exam.teacher_id != teacher_id:
        raise HTTPException(404, "Exam not found")
    if db.query(Assignment).filter((Assignment.practice_exam_id == exam_id) if exam_type == "Practice" else (Assignment.mock_exam_id == exam_id)).first() or exam.submissions:
        raise HTTPException(409, "Exam cannot be deleted after assignment or submission")
    db.delete(exam)
    db.flush()
