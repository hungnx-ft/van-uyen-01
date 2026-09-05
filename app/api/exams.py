from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.exam import PracticeExamCreate, PracticeExamResponse, MockExamCreate, MockExamResponse
from app.services.exam import create_practice_exam, create_mock_exam, delete_exam, update_mock_exam, update_practice_exam
from app.repositories.exam import practice_exam_repo, mock_exam_repo
from app.dependencies.auth import get_current_teacher, get_current_user
from app.models.user import User
from app.models.exam import PracticeExam, MockExam
from app.dependencies.permissions import visible_content

router = APIRouter()

@router.post("/practice", response_model=PracticeExamResponse)
def create_new_practice_exam(
    exam_in: PracticeExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    try:
        return create_practice_exam(db, exam_in=exam_in, teacher_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/practice", response_model=List[PracticeExamResponse])
def read_practice_exams(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return visible_content(db, PracticeExam, current_user).offset(max(skip, 0)).limit(min(max(limit, 1), 100)).all()

@router.post("/mock", response_model=MockExamResponse)
def create_new_mock_exam(
    exam_in: MockExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    try:
        return create_mock_exam(db, exam_in=exam_in, teacher_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/mock", response_model=List[MockExamResponse])
def read_mock_exams(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return visible_content(db, MockExam, current_user).offset(max(skip, 0)).limit(min(max(limit, 1), 100)).all()


@router.put("/practice/{exam_id}", response_model=PracticeExamResponse)
def edit_practice_exam(exam_id: int, exam_in: PracticeExamCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return update_practice_exam(db, exam_id, exam_in, current_user.id)


@router.put("/mock/{exam_id}", response_model=MockExamResponse)
def edit_mock_exam(exam_id: int, exam_in: MockExamCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return update_mock_exam(db, exam_id, exam_in, current_user.id)


@router.delete("/practice/{exam_id}", status_code=204)
def remove_practice_exam(exam_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    delete_exam(db, "Practice", exam_id, current_user.id)
    return Response(status_code=204)


@router.delete("/mock/{exam_id}", status_code=204)
def remove_mock_exam(exam_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    delete_exam(db, "Mock", exam_id, current_user.id)
    return Response(status_code=204)
