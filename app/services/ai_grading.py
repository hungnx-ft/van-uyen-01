from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.ai import AIGradingAnswer, AIGradingJob, AIGradingResult
from app.models.submission import Submission, SubmissionScore
from app.schemas.ai import AIGradingResultInput
from app.services.ai_settings import get_settings
from app.services.rubric import latest_rubric


def owned_submission(db: Session, submission_id: int, teacher_id: int) -> Submission:
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(404, "Submission not found")
    exam = submission.practice_exam if submission.exam_type == "Practice" else submission.mock_exam
    if not exam or exam.teacher_id != teacher_id:
        raise HTTPException(404, "Submission not found")
    return submission


def create_job(db: Session, submission_id: int, teacher_id: int) -> AIGradingJob:
    submission = owned_submission(db, submission_id, teacher_id)
    ai = get_settings(db, teacher_id)
    if not ai or not ai.is_enabled:
        raise HTTPException(409, "AI grading is not enabled")
    if not ai.api_key_encrypted:
        raise HTTPException(409, "AI API key is not configured")
    rubric = latest_rubric(db, submission.exam_type, submission.practice_exam_id or submission.mock_exam_id, teacher_id)
    if not rubric:
        raise HTTPException(409, "This exam has no rubric")
    job = AIGradingJob(submission_id=submission.id, rubric_id=rubric.id, provider=ai.provider,
                       model=ai.model, rubric_version=rubric.version, status="pending")
    db.add(job)
    db.flush()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: int, teacher_id: int) -> AIGradingJob:
    job = db.get(AIGradingJob, job_id)
    if not job:
        raise HTTPException(404, "AI grading job not found")
    owned_submission(db, job.submission_id, teacher_id)
    return job


def list_history(db: Session, submission_id: int, teacher_id: int) -> list[AIGradingJob]:
    owned_submission(db, submission_id, teacher_id)
    return (db.query(AIGradingJob)
            .filter(AIGradingJob.submission_id == submission_id)
            .order_by(AIGradingJob.created_at.desc(), AIGradingJob.id.desc()).all())


def list_jobs(db: Session, teacher_id: int, status: str | None = None) -> list[AIGradingJob]:
    query = db.query(AIGradingJob).join(Submission, AIGradingJob.submission_id == Submission.id)
    # Ownership is checked per submission so jobs cannot leak across teachers.
    jobs = query.order_by(AIGradingJob.created_at.desc(), AIGradingJob.id.desc()).all()
    visible = [job for job in jobs if _is_owned_submission(db, job.submission_id, teacher_id)]
    return [job for job in visible if status is None or job.status == status]


def _is_owned_submission(db: Session, submission_id: int, teacher_id: int) -> bool:
    try:
        owned_submission(db, submission_id, teacher_id)
        return True
    except HTTPException:
        return False


def create_bulk_jobs(db: Session, submission_ids: list[int], teacher_id: int) -> tuple[list[AIGradingJob], list[dict[str, str | int]]]:
    jobs: list[AIGradingJob] = []
    failed: list[dict[str, str | int]] = []
    for submission_id in dict.fromkeys(submission_ids):
        try:
            jobs.append(create_job(db, submission_id, teacher_id))
        except HTTPException as exc:
            failed.append({"submission_id": submission_id, "detail": str(exc.detail)})
    return jobs, failed


def retry_job(db: Session, job_id: int, teacher_id: int) -> AIGradingJob:
    job = get_job(db, job_id, teacher_id)
    if job.status != "failed":
        raise HTTPException(409, "Only failed jobs can be retried")
    job.status = "pending"
    job.error_message = None
    job.started_at = None
    job.completed_at = None
    db.flush()
    db.refresh(job)
    return job


def cancel_job(db: Session, job_id: int, teacher_id: int) -> None:
    job = get_job(db, job_id, teacher_id)
    if job.status not in {"pending", "processing"}:
        raise HTTPException(409, "Only pending or processing jobs can be cancelled")
    job.status = "failed"
    job.error_message = "Cancelled by teacher"
    job.completed_at = datetime.now(timezone.utc)
    db.flush()


def complete_job(db: Session, job_id: int, teacher_id: int, request: AIGradingResultInput) -> AIGradingJob:
    job = get_job(db, job_id, teacher_id)
    if job.result:
        raise HTTPException(409, "AI grading result already exists")
    submission = owned_submission(db, job.submission_id, teacher_id)
    valid_ids = {answer.practice_question_id or answer.mock_question_id for answer in submission.answers}
    seen: set[int] = set()
    for item in request.answers:
        question_id = item.practice_question_id or item.mock_question_id
        if (item.practice_question_id is None) == (item.mock_question_id is None) or question_id not in valid_ids:
            raise HTTPException(422, "AI result references an invalid question")
        if question_id in seen:
            raise HTTPException(422, "AI result contains duplicate questions")
        seen.add(question_id)
    result = AIGradingResult(job_id=job.id, submission_id=submission.id, total_score=request.total_score,
                             overall_comment=request.overall_comment, improvement_suggestion=request.improvement_suggestion,
                             confidence=request.confidence, raw_response=request.raw_response)
    result.answers = [AIGradingAnswer(practice_question_id=item.practice_question_id,
                                      mock_question_id=item.mock_question_id, ai_score=item.ai_score,
                                      ai_question_comment=item.ai_question_comment) for item in request.answers]
    job.result = result
    job.status = "completed"
    job.prompt_tokens = request.prompt_tokens
    job.completion_tokens = request.completion_tokens
    job.total_tokens = (request.prompt_tokens or 0) + (request.completion_tokens or 0) if request.prompt_tokens is not None or request.completion_tokens is not None else None
    job.estimated_cost_usd = request.estimated_cost_usd
    job.completed_at = datetime.now(timezone.utc)
    db.add(job)
    db.flush()
    db.refresh(job)
    return job


def usage_summary(db: Session, teacher_id: int) -> dict:
    jobs = list_jobs(db, teacher_id)
    completed = [job for job in jobs if job.status == "completed"]
    low_confidence = [job for job in completed if job.result and job.result.confidence is not None and job.result.confidence < 0.65]
    deviations = [abs(job.result.total_score - job.submission.teacher_score) for job in completed
                  if job.result and job.result.total_score is not None and job.submission.teacher_score is not None]
    return {
        "total_jobs": len(jobs), "completed_jobs": len(completed),
        "failed_jobs": sum(job.status == "failed" for job in jobs),
        "total_tokens": sum(job.total_tokens or 0 for job in completed),
        "estimated_cost_usd": round(sum(job.estimated_cost_usd or 0 for job in completed), 6),
        "low_confidence_jobs": len(low_confidence),
        "average_score_deviation": round(sum(deviations) / len(deviations), 4) if deviations else None,
    }


def apply_result(db: Session, job_id: int, teacher_id: int) -> Submission:
    job = get_job(db, job_id, teacher_id)
    if job.status != "completed" or not job.result:
        raise HTTPException(409, "AI grading job has no completed result")
    submission = owned_submission(db, job.submission_id, teacher_id)
    for ai_answer in job.result.answers:
        question_id = ai_answer.practice_question_id or ai_answer.mock_question_id
        target = next((answer for answer in submission.answers
                       if (answer.practice_question_id or answer.mock_question_id) == question_id), None)
        if not target:
            raise HTTPException(409, "AI result references an answer outside this submission")
        score = target.score
        if score is None:
            score = SubmissionScore(submission_id=submission.id, answer_id=target.id, teacher_id=teacher_id,
                                    score=ai_answer.ai_score, teacher_comment=ai_answer.ai_question_comment)
            db.add(score)
        else:
            score.score = ai_answer.ai_score
            score.teacher_comment = ai_answer.ai_question_comment
    submission.teacher_score = job.result.total_score
    submission.status = "Graded"
    db.flush()
    db.refresh(submission)
    return submission


def update_feedback(db: Session, submission_id: int, teacher_id: int, *, teacher_comment: str | None,
                    teacher_improvement_note: str | None, publish: bool) -> Submission:
    submission = owned_submission(db, submission_id, teacher_id)
    submission.teacher_comment = teacher_comment.strip() if teacher_comment else None
    submission.teacher_improvement_note = teacher_improvement_note.strip() if teacher_improvement_note else None
    if publish:
        if submission.teacher_score is None:
            raise HTTPException(409, "A teacher score is required before publishing feedback")
        submission.feedback_published = True
        submission.feedback_published_at = datetime.now(timezone.utc)
    else:
        submission.feedback_published = False
        submission.feedback_published_at = None
    db.flush()
    db.refresh(submission)
    return submission
