from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_teacher
from app.models.user import User
from app.repositories.class_ import class_repo
from app.schemas.class_ import ClassCreate, ClassDetail, ClassResponse, ClassUpdate
from app.schemas.student import StudentPage, StudentResponse
from app.services.class_ import archive_class, assign_student, class_detail, create_class, update_class
from app.services.student import list_students

router = APIRouter()


@router.post("/", response_model=ClassResponse, status_code=201)
def create_new_class(request: ClassCreate, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_teacher)):
    return create_class(db, class_in=request, teacher_id=current_user.id)


@router.get("/", response_model=list[ClassResponse])
def read_classes(response: Response, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100),
                 q: str = Query("", max_length=100), year: str | None = Query(None, pattern=r"^\d{4}-\d{4}$"),
                 include_archived: bool = False, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_teacher)):
    query = class_repo.for_teacher(db, current_user.id, q=q, year=year, include_archived=include_archived)
    response.headers["X-Total-Count"] = str(query.order_by(None).count())
    return query.offset(skip).limit(limit).all()


@router.get("/{class_id}", response_model=ClassDetail)
def read_class(class_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return class_detail(db, class_id, current_user.id)


@router.patch("/{class_id}", response_model=ClassResponse)
def edit_class(class_id: int, request: ClassUpdate, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_teacher)):
    return update_class(db, class_id, current_user.id, request)


@router.post("/{class_id}/archive", response_model=ClassResponse)
def archive(class_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return archive_class(db, class_id, current_user.id, True)


@router.post("/{class_id}/restore", response_model=ClassResponse)
def restore(class_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return archive_class(db, class_id, current_user.id, False)


@router.get("/{class_id}/students", response_model=StudentPage)
def read_class_students(class_id: int, q: str = Query("", max_length=100), is_active: bool | None = None,
                        skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                        db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return list_students(db, current_user.id, class_id=class_id, q=q, is_active=is_active,
                         include_archived=True, skip=skip, limit=limit)


@router.put("/{class_id}/students/{student_id}", response_model=StudentResponse)
def add_student_to_class(class_id: int, student_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_teacher)):
    return assign_student(db, class_id=class_id, student_id=student_id, teacher_id=current_user.id)
