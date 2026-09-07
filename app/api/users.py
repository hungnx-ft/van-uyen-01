from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_teacher
from app.dependencies.permissions import managed_student
from app.models.user import User
from app.schemas.student import (BulkStudentCreate, BulkStudentFailure, BulkStudentResult,
                                 StudentCreate, StudentCredentials, StudentPage, StudentResponse,
                                 StudentStatus, StudentUpdate)
from app.schemas.user import UserResponse, UserUpdate
from app.services.student import change_student_status, delete_student, list_students, update_student
from app.services.user import create_student_credentials, reset_password, reset_student_credentials
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

router = APIRouter()


@router.post("/students", response_model=StudentCredentials, status_code=201)
def create_new_student(student_in: StudentCreate, response: Response,
                       db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    student, password = create_student_credentials(db, student_in, current_user.id)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return StudentCredentials(
        **StudentResponse.model_validate(student).model_dump(), temporary_password=password
    )


@router.post("/students/bulk", response_model=BulkStudentResult, status_code=201)
def create_students_bulk(request: BulkStudentCreate, response: Response,
                         db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    # Validate the destination once, then isolate each row so one duplicate
    # does not prevent the rest of the spreadsheet from being imported.
    from app.dependencies.permissions import owned_class
    owned_class(db, request.class_id, current_user.id, require_active=True)
    created: list[StudentCredentials] = []
    failed: list[BulkStudentFailure] = []
    for row, item in enumerate(request.students, start=2):
        try:
            with db.begin_nested():
                student, password = create_student_credentials(
                    db,
                    StudentCreate(
                        username=item.username or f"student_{row}",
                        password=item.password,
                        full_name=item.full_name,
                        school_name=item.school_name,
                        class_id=request.class_id,
                        role="Student",
                    ),
                    current_user.id,
                )
                created.append(StudentCredentials(
                    **StudentResponse.model_validate(student).model_dump(),
                    temporary_password=password,
                ))
        except (HTTPException, IntegrityError, ValueError) as exc:
            detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
            failed.append(BulkStudentFailure(row=row, username=item.username, detail=str(detail)))
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return BulkStudentResult(created=created, failed=failed)


@router.get("/students", response_model=StudentPage)
def read_students(class_id: int | None = Query(None, gt=0), q: str = Query("", max_length=100),
                  is_active: bool | None = None, include_archived: bool = False,
                  skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                  db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return list_students(db, current_user.id, class_id=class_id, q=q, is_active=is_active,
                         include_archived=include_archived, skip=skip, limit=limit)


@router.get("/students/{student_id}", response_model=StudentResponse)
def read_student(student_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return managed_student(db, student_id, current_user.id)


@router.patch("/students/{student_id}", response_model=StudentResponse)
def edit_student(student_id: int, request: StudentUpdate, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_teacher)):
    return update_student(db, student_id, current_user.id, request)


@router.patch("/students/{student_id}/status", response_model=StudentResponse)
def set_student_status(student_id: int, request: StudentStatus, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_teacher)):
    return change_student_status(db, student_id, current_user.id, request.is_active)


@router.delete("/students/{student_id}", status_code=204)
def remove_student(student_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    delete_student(db, student_id, current_user.id)
    return Response(status_code=204)


@router.put("/students/{student_id}/password", response_model=UserResponse)
def reset_student_password(student_id: int, user_in: UserUpdate, db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_teacher)):
    return reset_password(db, student_id=student_id, new_password=user_in.password, teacher_id=current_user.id)


@router.post("/students/{student_id}/password/reset", response_model=StudentCredentials)
def generate_student_password(student_id: int, response: Response,
                              db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    student, password = reset_student_credentials(db, student_id, current_user.id)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return StudentCredentials(
        **StudentResponse.model_validate(student).model_dump(), temporary_password=password
    )
