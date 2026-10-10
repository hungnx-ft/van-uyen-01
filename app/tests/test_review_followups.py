import asyncio
import socket
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from sqlalchemy.orm import sessionmaker

from app import worker
from app.core.config import settings
from app.models import PracticeExam, PracticeQuestion, Submission, SubmissionAnswer
from app.models.ai import AIGradingJob, AISetting, ExamRubric
from app.services import ai_settings
from app.services.ai_providers import GradingAnswer, GradingResponse
from app.tests.conftest import bearer, login


def _graded_setup(db, accounts, teacher="teacher_one", status="pending", max_score=2):
    teacher = accounts[teacher]
    exam = PracticeExam(title="Đề", teacher_id=teacher.id)
    db.add(exam); db.flush()
    question = PracticeQuestion(exam_id=exam.id, content="Câu", max_score=max_score)
    db.add(question); db.flush()
    submission = Submission(student_id=accounts["student_one"].id, exam_type="Practice",
                            practice_exam_id=exam.id, status="Submitted")
    db.add(submission); db.flush()
    answer = SubmissionAnswer(submission_id=submission.id, practice_question_id=question.id, student_answer="x")
    rubric = ExamRubric(teacher_id=teacher.id, exam_type="Practice", practice_exam_id=exam.id, content_text="Barem")
    db.add_all([answer, rubric]); db.flush()
    if db.query(AISetting).filter(AISetting.teacher_id == teacher.id).first() is None:
        db.add(AISetting(teacher_id=teacher.id, provider="openai", model="m",
                         api_key_encrypted=ai_settings.encrypt_api_key("k"), is_enabled=True))
    job = AIGradingJob(submission_id=submission.id, rubric_id=rubric.id, provider="openai", model="m",
                       rubric_version=1, status=status)
    db.add(job); db.commit()
    return job, submission, question, answer


def test_job_list_is_scoped_to_the_teacher_and_filters_by_status(client, db, accounts):
    mine, *_ = _graded_setup(db, accounts)
    _graded_setup(db, accounts, teacher="teacher_two")
    failed, *_ = _graded_setup(db, accounts, status="failed")
    headers = bearer(login(client, "teacher_one"))
    assert {job["id"] for job in client.get("/api/v1/ai/jobs", headers=headers).json()} == {mine.id, failed.id}
    assert [job["id"] for job in client.get("/api/v1/ai/jobs?status=failed", headers=headers).json()] == [failed.id]
    assert client.get("/api/v1/ai/usage", headers=headers).json()["total_jobs"] == 2


def test_retry_resets_attempts(client, db, accounts):
    job, *_ = _graded_setup(db, accounts, status="failed")
    job.attempt_count = worker.MAX_ATTEMPTS
    db.commit()
    response = client.post(f"/api/v1/ai/jobs/{job.id}/retry", headers=bearer(login(client, "teacher_one")))
    assert response.status_code == 200, response.text
    db.refresh(job)
    assert job.status == "pending" and job.attempt_count == 0


def _run_worker(db_engine, monkeypatch, grade):
    class FakeProvider:
        async def grade(self, request):
            return await grade(request)

    monkeypatch.setattr(worker, "SessionLocal", sessionmaker(bind=db_engine))
    monkeypatch.setattr(worker, "build_provider", lambda **_: FakeProvider())
    return asyncio.run(worker.process_one())


def test_cancelling_a_processing_job_discards_the_late_result(db_engine, db, accounts, monkeypatch):
    job, *_ = _graded_setup(db, accounts)

    async def grade(request):
        # The teacher cancels while the provider call is in flight.
        with sessionmaker(bind=db_engine)() as other:
            other.get(AIGradingJob, job.id).status = "failed"
            other.commit()
        return GradingResponse(total_score=1, confidence=1, answers=[
            GradingAnswer(question_key=request.questions[0].key, score=1)])

    assert _run_worker(db_engine, monkeypatch, grade) is True
    db.expire_all()
    cancelled = db.get(AIGradingJob, job.id)
    assert cancelled.status == "failed" and cancelled.result is None


def test_stale_processing_jobs_are_returned_to_the_queue(db_engine, db, accounts):
    job, *_ = _graded_setup(db, accounts, status="processing")
    exhausted, *_ = _graded_setup(db, accounts, status="processing")
    recent, *_ = _graded_setup(db, accounts, status="processing")
    old = datetime.now(timezone.utc) - timedelta(hours=1)
    job.started_at, job.attempt_count = old, 1
    exhausted.started_at, exhausted.attempt_count = old, worker.MAX_ATTEMPTS
    recent.started_at, recent.attempt_count = datetime.now(timezone.utc), 1
    db.commit()
    with sessionmaker(bind=db_engine)() as session:
        assert worker.reclaim_stale_jobs(session) == 2
    db.expire_all()
    assert [db.get(AIGradingJob, j.id).status for j in (job, exhausted, recent)] == ["pending", "failed", "processing"]


def test_scores_above_question_maximum_are_rejected(client, db, accounts):
    job, submission, question, answer = _graded_setup(db, accounts, max_score=2)
    headers = bearer(login(client, "teacher_one"))
    too_high = client.post(f"/api/v1/submissions/{submission.id}/grade", headers=headers,
                           json={"scores": [{"answer_id": answer.id, "score": 3}]})
    assert too_high.status_code == 422
    ai_result = {"total_score": 2, "answers": [{"practice_question_id": question.id, "ai_score": 2.5}]}
    assert client.post(f"/api/v1/ai/jobs/{job.id}/result", headers=headers, json=ai_result).status_code == 422
    ai_result = {"total_score": 5, "answers": [{"practice_question_id": question.id, "ai_score": 2}]}
    assert client.post(f"/api/v1/ai/jobs/{job.id}/result", headers=headers, json=ai_result).status_code == 422
    ok = client.post(f"/api/v1/submissions/{submission.id}/grade", headers=headers,
                     json={"scores": [{"answer_id": answer.id, "score": 2}]})
    assert ok.status_code == 200, ok.text


def test_dedicated_encryption_key_still_decrypts_legacy_values(monkeypatch):
    legacy = ai_settings.encrypt_api_key("sk-legacy")
    monkeypatch.setattr(settings, "AI_KEY_ENCRYPTION_KEY", Fernet.generate_key().decode())
    fresh = ai_settings.encrypt_api_key("sk-new")
    assert ai_settings.decrypt_api_key(legacy) == "sk-legacy"
    # Rotating SECRET_KEY no longer breaks values encrypted with the dedicated key.
    monkeypatch.setattr(settings, "SECRET_KEY", "a-completely-different-secret-key-value")
    assert ai_settings.decrypt_api_key(fresh) == "sk-new"


def test_unsupported_providers_are_rejected(client, accounts):
    headers = bearer(login(client, "teacher_one"))
    response = client.put("/api/v1/ai/settings", headers=headers,
                          json={"provider": "anthropic", "model": "m", "is_enabled": False})
    assert response.status_code == 422


@pytest.mark.parametrize("address,allowed", [
    ("127.0.0.1", False), ("10.0.0.5", False), ("169.254.169.254", False), ("::1", False), ("8.8.8.8", True),
])
def test_production_base_url_must_resolve_to_a_public_host(monkeypatch, address, allowed):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, port: [(None, None, None, None, (address, 0))])
    if allowed:
        ai_settings.ensure_public_base_url("https://llm.example.com/v1")
    else:
        with pytest.raises(HTTPException):
            ai_settings.ensure_public_base_url("https://llm.example.com/v1")
