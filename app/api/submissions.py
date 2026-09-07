from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.submission import SubmissionCreate, SubmissionResponse, GradeSubmissionRequest
from app.services.submission import create_submission, grade_submission, get_student_submissions, get_teacher_submissions
from app.dependencies.auth import get_current_teacher, get_current_student, get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=SubmissionResponse)
def submit_exam(
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    return create_submission(db, submission_in=submission_in, student_id=current_user.id)

@router.get("/my-submissions", response_model=List[SubmissionResponse])
def read_my_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    submissions = get_student_submissions(db, student_id=current_user.id)
    # Never expose teacher/AI feedback before the teacher explicitly publishes it.
    sanitized = []
    for submission in submissions:
        payload = SubmissionResponse.model_validate(submission).model_dump()
        if not submission.feedback_published:
            payload.update({"teacher_score": None, "teacher_comment": None,
                            "teacher_improvement_note": None, "feedback_published": False,
                            "status": "Submitted"})
            payload["answers"] = [{**answer, "score": None} for answer in payload["answers"]]
        sanitized.append(payload)
    return sanitized


@router.get("/teacher-submissions", response_model=List[SubmissionResponse])
def read_teacher_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    return get_teacher_submissions(db, teacher_id=current_user.id)

@router.post("/{submission_id}/grade", response_model=SubmissionResponse)
def grade_exam_submission(
    submission_id: int,
    request: GradeSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    submission = grade_submission(
        db,
        submission_id=submission_id,
        scores_in=request.scores,
        teacher_id=current_user.id,
        teacher_comment=request.teacher_comment,
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission
