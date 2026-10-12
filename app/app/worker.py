"""AI grading worker.

Run once from a scheduler or continuously under systemd:
``python -m app.worker --once`` / ``python -m app.worker``.
"""
import argparse
import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone

from app.database.session import SessionLocal
from app.models.ai import AIGradingJob
from app.services.ai_grading import complete_job
from app.services.ai_providers import GradingRequest, QuestionSpec, build_provider
from app.services.ai_settings import decrypt_api_key, ensure_public_base_url, get_settings
from app.schemas.ai import AIGradingResultInput, AIGradingAnswerInput

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s ai-worker %(message)s")
log = logging.getLogger("ai-worker")
MAX_ATTEMPTS = 3
# Longer than the provider timeout, so only jobs whose worker died are reclaimed.
STALE_PROCESSING = timedelta(minutes=10)


def _finish_attempt(job: AIGradingJob, error: str):
    job.status = "failed" if job.attempt_count >= MAX_ATTEMPTS else "pending"
    job.error_message = error[:2000]


def reclaim_stale_jobs(db) -> int:
    """Return jobs left in ``processing`` by a crashed worker to the queue."""
    cutoff = datetime.now(timezone.utc) - STALE_PROCESSING
    stale = (db.query(AIGradingJob)
             .filter(AIGradingJob.status == "processing", AIGradingJob.started_at < cutoff)
             .with_for_update(skip_locked=True).all())
    for job in stale:
        _finish_attempt(job, "Worker stopped while processing this job")
        log.warning("reclaimed stale job=%s attempt=%s", job.id, job.attempt_count)
    db.commit()
    return len(stale)


def _lock_if_processing(db, job_id: int) -> AIGradingJob | None:
    """Re-read the job under lock; a teacher may have cancelled it meanwhile."""
    job = (db.query(AIGradingJob).filter(AIGradingJob.id == job_id)
           .with_for_update().populate_existing().first())
    return job if job and job.status == "processing" else None


async def process_one() -> bool:
    db = SessionLocal()
    job_id = None
    try:
        reclaim_stale_jobs(db)
        # Multiple worker replicas may poll concurrently.  Lock only the job
        # being claimed and skip rows another worker is already processing.
        job = (db.query(AIGradingJob)
               .filter(AIGradingJob.status == "pending")
               .order_by(AIGradingJob.id)
               .with_for_update(skip_locked=True)
               .first())
        if not job:
            return False
        job.status = "processing"
        job.attempt_count += 1
        job.started_at = datetime.now(timezone.utc)
        job_id = job.id
        db.commit()
        db.refresh(job)
        setting = get_settings(db, job.submission.practice_exam.teacher_id if job.submission.exam_type == "Practice" else job.submission.mock_exam.teacher_id)
        ensure_public_base_url(setting.base_url)
        provider = build_provider(provider=job.provider, model=job.model, api_key=decrypt_api_key(setting.api_key_encrypted), base_url=setting.base_url)
        submission = job.submission
        questions = submission.practice_exam.questions if submission.exam_type == "Practice" else submission.mock_exam.questions
        # Match answers by question ID: answer rows are not guaranteed to be in
        # question order, and a student may leave questions out entirely.
        answers_by_question = {answer.question_id: answer.student_answer for answer in submission.answers}
        answered = [q for q in sorted(questions, key=lambda q: q.id) if q.id in answers_by_question]
        specs = tuple(QuestionSpec(f"q{q.id}", q.max_score) for q in answered)
        text = "\n".join(f"q{q.id}: {answers_by_question[q.id]}" for q in answered)
        response = await provider.grade(GradingRequest(rubric=job.rubric.content_text, submission=text, questions=specs))
        answers = []
        for item in response.answers:
            question_id = int(item.question_key[1:])
            answers.append(AIGradingAnswerInput(
                practice_question_id=question_id if submission.exam_type == "Practice" else None,
                mock_question_id=question_id if submission.exam_type == "Mock" else None,
                ai_score=item.score, ai_question_comment=item.comment,
            ))
        if _lock_if_processing(db, job_id) is None:
            db.rollback()
            log.info("job=%s was cancelled while processing; result discarded", job_id)
            return True
        complete_job(db, job_id, setting.teacher_id, AIGradingResultInput(
            total_score=response.total_score, overall_comment=response.overall_comment,
            improvement_suggestion=response.improvement_suggestion, confidence=response.confidence,
            answers=answers,
        ))
        db.commit()
        log.info("completed job=%s", job_id)
        return True
    except Exception as exc:
        db.rollback()
        job = _lock_if_processing(db, job_id) if job_id is not None else None
        if job:
            _finish_attempt(job, str(exc))
            log.warning("job=%s failed attempt=%s: %s", job.id, job.attempt_count, exc)
        db.commit()
        return True
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=5)
    args = parser.parse_args()
    while True:
        asyncio.run(process_one())
        if args.once:
            return
        # Keep polling when the queue is empty; the pause also spaces out retries of a failing job.
        time.sleep(max(args.interval, 1))


if __name__ == "__main__":
    main()
