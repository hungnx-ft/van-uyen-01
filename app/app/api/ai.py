from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_teacher
from app.models.user import User
from app.schemas.ai import (AIBulkJobCreate, AIBulkJobResponse, AIConnectionResponse, AIFeedbackResponse,
                            AIFeedbackUpdate, AIGradingJobResponse, AIGradingResultInput, AIUsageResponse,
                            AISettingsResponse, AISettingsUpdate)
from app.services.ai_settings import clear_api_key, get_settings, save_settings, test_connection, to_response
from app.services.ai_grading import (apply_result, cancel_job, complete_job, create_bulk_jobs, create_job,
                                     get_job, list_history, list_jobs, retry_job, update_feedback, usage_summary)

router = APIRouter()


@router.get("/settings", response_model=AISettingsResponse)
def read_ai_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return to_response(get_settings(db, current_user.id))


@router.put("/settings", response_model=AISettingsResponse)
def update_ai_settings(request: AISettingsUpdate, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_teacher)):
    return to_response(save_settings(db, current_user.id, request))


@router.delete("/settings/key", response_model=AISettingsResponse)
def delete_ai_key(db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return to_response(clear_api_key(db, current_user.id))


@router.post("/test-connection", response_model=AIConnectionResponse)
async def check_ai_connection(db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    ok, message = await test_connection(db, current_user.id)
    return {"ok": ok, "message": message}


@router.post("/submissions/{submission_id}/jobs", response_model=AIGradingJobResponse, status_code=201)
def create_grading_job(submission_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_teacher)):
    return create_job(db, submission_id, current_user.id)


@router.post("/submissions/bulk-jobs", response_model=AIBulkJobResponse, status_code=201)
def create_bulk_grading_jobs(request: AIBulkJobCreate, db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_teacher)):
    jobs, failed = create_bulk_jobs(db, request.submission_ids, current_user.id)
    return {"jobs": jobs, "failed": failed}


@router.get("/jobs", response_model=list[AIGradingJobResponse])
def read_jobs(status: str | None = Query(None, pattern="^(pending|processing|completed|failed)$"),
              db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return list_jobs(db, current_user.id, status)


@router.get("/usage", response_model=AIUsageResponse)
def read_ai_usage(db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return usage_summary(db, current_user.id)


@router.post("/jobs/{job_id}/retry", response_model=AIGradingJobResponse)
def retry_grading_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return retry_job(db, job_id, current_user.id)


@router.delete("/jobs/{job_id}", status_code=204)
def cancel_grading_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    cancel_job(db, job_id, current_user.id)
    return Response(status_code=204)


@router.get("/jobs/{job_id}", response_model=AIGradingJobResponse)
def read_grading_job(job_id: int, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_teacher)):
    return get_job(db, job_id, current_user.id)


@router.get("/submissions/{submission_id}/history", response_model=list[AIGradingJobResponse])
def read_grading_history(submission_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_teacher)):
    return list_history(db, submission_id, current_user.id)


@router.post("/jobs/{job_id}/result", response_model=AIGradingJobResponse)
def complete_grading_job(job_id: int, request: AIGradingResultInput, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_teacher)):
    return complete_job(db, job_id, current_user.id, request)


@router.post("/jobs/{job_id}/apply", response_model=AIGradingJobResponse)
def apply_grading_job(job_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_teacher)):
    # Applying is intentionally separate from running a provider: teachers
    # can review a completed result before copying scores into the submission.
    apply_result(db, job_id, current_user.id)
    return get_job(db, job_id, current_user.id)


@router.patch("/submissions/{submission_id}/feedback", response_model=AIFeedbackResponse)
def save_submission_feedback(submission_id: int, request: AIFeedbackUpdate,
                             db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    submission = update_feedback(db, submission_id, current_user.id, teacher_comment=request.teacher_comment,
                                 teacher_improvement_note=request.teacher_improvement_note, publish=request.publish)
    return {
        "submission_id": submission.id,
        "teacher_score": submission.teacher_score,
        "teacher_comment": submission.teacher_comment,
        "teacher_improvement_note": submission.teacher_improvement_note,
        "feedback_published": submission.feedback_published,
        "feedback_published_at": submission.feedback_published_at,
    }
