from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.dependencies.permissions import owned_class
from app.models.assignment import Assignment
from app.models.exam import MockExam, PracticeExam
from app.models.user import User
from app.schemas.assignment import AssignmentCreate


def create_assignment(db: Session, request: AssignmentCreate, teacher_id: int) -> Assignment:
    owned_class(db, request.class_id, teacher_id, require_active=True)
    is_practice = request.exam_type == "Practice"
    if (is_practice and (request.practice_exam_id is None or request.mock_exam_id is not None)) or (
        not is_practice and (request.mock_exam_id is None or request.practice_exam_id is not None)
    ):
        raise HTTPException(422, "Exactly one matching exam ID is required")
    exam_model = PracticeExam if is_practice else MockExam
    exam_id = request.practice_exam_id if is_practice else request.mock_exam_id
    exam = db.get(exam_model, exam_id)
    if exam is None or exam.teacher_id != teacher_id:
        raise HTTPException(404, "Exam not found")
    assignment = Assignment(
        teacher_id=teacher_id,
        class_id=request.class_id,
        exam_type=request.exam_type,
        practice_exam_id=request.practice_exam_id,
        mock_exam_id=request.mock_exam_id,
        exam_title=request.exam_title,
        instructions=request.instructions,
    )
    db.add(assignment)
    db.flush()
    db.refresh(assignment)
    return assignment


def list_teacher_assignments(db: Session, teacher_id: int):
    return db.query(Assignment).filter(Assignment.teacher_id == teacher_id).order_by(Assignment.created_at.desc()).all()


def list_student_assignments(db: Session, student: User):
    if student.class_id is None:
        return []
    return (
        db.query(Assignment)
        .filter(Assignment.class_id == student.class_id, Assignment.teacher_id != student.id)
        .order_by(Assignment.created_at.desc())
        .all()
    )
