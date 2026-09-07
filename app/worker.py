"""AI grading worker.

Run once from a scheduler or continuously under systemd:
``python -m app.worker --once`` / ``python -m app.worker``.
"""
import argparse
import asyncio
import logging
import time
from datetime import datetime, timezone

from app.database.session import SessionLocal
from app.models.ai import AIGradingJob
from app.services.ai_grading import complete_job
from app.services.ai_providers import GradingRequest, QuestionSpec, build_provider
from app.services.ai_settings import decrypt_api_key, get_settings
from app.schemas.ai import AIGradingResultInput, AIGradingAnswerInput

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s ai-worker %(message)s")
log = logging.getLogger("ai-worker")
MAX_ATTEMPTS = 3


async def process_one() -> bool:
    db = SessionLocal()
    try:
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
        db.commit()
        db.refresh(job)
        setting = get_settings(db, job.submission.practice_exam.teacher_id if job.submission.exam_type == "Practice" else job.submission.mock_exam.teacher_id)
        provider = build_provider(provider=job.provider, model=job.model, api_key=decrypt_api_key(setting.api_key_encrypted), base_url=setting.base_url)
        submission = job.submission
        questions = submission.practice_exam.questions if submission.exam_type == "Practice" else submission.mock_exam.questions
        specs = tuple(QuestionSpec(f"q{q.id}", q.max_score) for q in questions)
        text = "\n".join(f"q{q.id}: {a.student_answer}" for q, a in zip(questions, submission.answers))
        response = await provider.grade(GradingRequest(rubric=job.rubric.content_text, submission=text, questions=specs))
        answers = []
        for item in response.answers:
            question_id = int(item.question_key[1:])
            answers.append(AIGradingAnswerInput(
                practice_question_id=question_id if submission.exam_type == "Practice" else None,
                mock_question_id=question_id if submission.exam_type == "Mock" else None,
                ai_score=item.score, ai_question_comment=item.comment,
            ))
        complete_job(db, job.id, setting.teacher_id, AIGradingResultInput(
            total_score=response.total_score, overall_comment=response.overall_comment,
            improvement_suggestion=response.improvement_suggestion, confidence=response.confidence,
            answers=answers,
        ))
        db.commit()
        log.info("completed job=%s attempt=%s", job.id, job.attempt_count)
        return True
    except Exception as exc:
        db.rollback()
        if 'job' in locals() and job:
            job.status = "failed" if job.attempt_count >= MAX_ATTEMPTS else "pending"
            job.error_message = str(exc)[:2000]
            db.commit()
            log.warning("job=%s failed attempt=%s: %s", job.id, job.attempt_count, exc)
        return True
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=5)
    args = parser.parse_args()
    while True:
        found = asyncio.run(process_one())
        if args.once or not found:
            return
        time.sleep(max(args.interval, 1))


if __name__ == "__main__":
    main()
