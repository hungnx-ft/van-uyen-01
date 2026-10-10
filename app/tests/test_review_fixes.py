import asyncio

from sqlalchemy.orm import sessionmaker

from app import worker
from app.models import MockExam, MockQuestion, PracticeExam, PracticeQuestion, Submission, SubmissionAnswer
from app.models.ai import AIGradingJob, AISetting, ExamRubric
from app.services.ai_providers import GradingAnswer, GradingResponse
from app.services.ai_settings import encrypt_api_key
from app.tests.conftest import bearer, login


def _exam(db, teacher, model=PracticeExam, question_model=PracticeQuestion, count=2, **question_fields):
    exam = model(title="Đề", teacher_id=teacher.id)
    db.add(exam); db.flush()
    questions = [question_model(exam_id=exam.id, content=f"Câu {i}", max_score=1, answer_key=f"Đáp án {i}",
                                **question_fields) for i in range(count)]
    db.add_all(questions); db.commit()
    return exam, questions


def test_students_get_answer_keys_only_through_their_own_practice_submission(client, db, accounts):
    exam, questions = _exam(db, accounts["teacher_one"])
    student = bearer(login(client))
    listed = client.get("/api/v1/exams/practice", headers=student).json()
    assert [q["answer_key"] for q in listed[0]["questions"]] == ["", ""]
    teacher = bearer(login(client, "teacher_one"))
    assert client.get("/api/v1/exams/practice", headers=teacher).json()[0]["questions"][0]["answer_key"] == "Đáp án 0"

    submitted = client.post("/api/v1/submissions/", headers=student, json={
        "exam_type": "Practice", "practice_exam_id": exam.id,
        "answers": [{"practice_question_id": q.id, "student_answer": "x"} for q in questions]})
    assert submitted.status_code == 200, submitted.text
    assert sorted(a["answer_key"] for a in submitted.json()["answers"]) == ["Đáp án 0", "Đáp án 1"]


def test_mock_answer_keys_stay_hidden_until_feedback_is_published(client, db, accounts):
    exam, questions = _exam(db, accounts["teacher_one"], MockExam, MockQuestion, section=1)
    student = bearer(login(client))
    submitted = client.post("/api/v1/submissions/", headers=student, json={
        "exam_type": "Mock", "mock_exam_id": exam.id,
        "answers": [{"mock_question_id": q.id, "student_answer": "x"} for q in questions]})
    assert submitted.status_code == 200, submitted.text
    assert all(a["answer_key"] is None for a in submitted.json()["answers"])

    submission = db.get(Submission, submitted.json()["id"])
    submission.teacher_score = 1
    submission.feedback_published = True
    db.commit()
    mine = client.get("/api/v1/submissions/my-submissions", headers=student).json()
    assert sorted(a["answer_key"] for a in mine[0]["answers"]) == ["Đáp án 0", "Đáp án 1"]


def test_exam_with_submissions_is_edited_in_place(client, db, accounts):
    exam, questions = _exam(db, accounts["teacher_one"])
    submission = Submission(student_id=accounts["student_one"].id, exam_type="Practice",
                            practice_exam_id=exam.id, status="Submitted")
    db.add(submission); db.flush()
    db.add(SubmissionAnswer(submission_id=submission.id, practice_question_id=questions[0].id, student_answer="x"))
    db.commit()
    headers = bearer(login(client, "teacher_one"))
    body = {"title": "Đề đã sửa", "questions": [
        {"content": "Câu mới", "max_score": 2, "answer_key": "Mới"},
        {"content": "Câu mới 2", "max_score": 2, "answer_key": "Mới 2"}]}
    updated = client.put(f"/api/v1/exams/practice/{exam.id}", headers=headers, json=body)
    assert updated.status_code == 200, updated.text
    assert [q["id"] for q in updated.json()["questions"]] == [q.id for q in questions]
    assert updated.json()["questions"][0]["answer_key"] == "Mới"

    body["questions"].append({"content": "Câu thêm", "max_score": 1})
    assert client.put(f"/api/v1/exams/practice/{exam.id}", headers=headers, json=body).status_code == 409


def test_login_attempts_are_rate_limited_per_account(client, accounts):
    for _ in range(10):
        response = client.post("/api/v1/auth/login", data={"username": "student_one", "password": "wrong-password"})
        assert response.status_code == 401
    blocked = client.post("/api/v1/auth/login", data={"username": "student_one", "password": "initial-password"})
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "300"
    login(client, "student_two")


def test_worker_matches_answers_to_questions_by_id(db_engine, db, accounts, monkeypatch):
    teacher = accounts["teacher_one"]
    exam, questions = _exam(db, teacher, count=3)
    submission = Submission(student_id=accounts["student_one"].id, exam_type="Practice",
                            practice_exam_id=exam.id, status="Submitted")
    db.add(submission); db.flush()
    # Stored out of question order, with the middle question left unanswered.
    db.add_all([
        SubmissionAnswer(submission_id=submission.id, practice_question_id=questions[2].id, student_answer="trả lời 2"),
        SubmissionAnswer(submission_id=submission.id, practice_question_id=questions[0].id, student_answer="trả lời 0"),
    ])
    rubric = ExamRubric(teacher_id=teacher.id, exam_type="Practice", practice_exam_id=exam.id, content_text="Barem")
    db.add_all([rubric, AISetting(teacher_id=teacher.id, provider="openai", model="m",
                                  api_key_encrypted=encrypt_api_key("k"), is_enabled=True)])
    db.flush()
    job = AIGradingJob(submission_id=submission.id, rubric_id=rubric.id, provider="openai", model="m",
                       rubric_version=1, status="pending")
    db.add(job); db.commit()

    seen = {}

    class FakeProvider:
        async def grade(self, request):
            seen["text"] = request.submission
            seen["keys"] = [q.key for q in request.questions]
            return GradingResponse(total_score=1, confidence=0.9, answers=[
                GradingAnswer(question_key=key, score=0.5) for key in seen["keys"]])

    monkeypatch.setattr(worker, "SessionLocal", sessionmaker(bind=db_engine))
    monkeypatch.setattr(worker, "build_provider", lambda **_: FakeProvider())
    assert asyncio.run(worker.process_one()) is True
    assert seen["keys"] == [f"q{questions[0].id}", f"q{questions[2].id}"]
    assert seen["text"] == f"q{questions[0].id}: trả lời 0\nq{questions[2].id}: trả lời 2"
    db.expire_all()
    assert db.get(AIGradingJob, job.id).status == "completed"
