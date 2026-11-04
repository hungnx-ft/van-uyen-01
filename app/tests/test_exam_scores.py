import pytest

from app.models import MockExam, MockQuestion, PracticeExam, PracticeQuestion, Submission, SubmissionAnswer
from app.models.submission import SubmissionScore
from app.tests.conftest import bearer, login


def _practice(scores):
    return {"title": "Đề", "passage": "Ngữ liệu",
            "questions": [{"content": f"Câu {i}", "max_score": s, "answer_key": "A"} for i, s in enumerate(scores)]}


def _mock(scores):
    return {"title": "Đề thi", "passage": "Ngữ liệu",
            "questions": [{"section": 1 if i < 2 else 2, "content": f"Câu {i}", "max_score": s, "answer_key": "A"}
                          for i, s in enumerate(scores)]}


def test_custom_question_scores_are_stored_per_question(client, accounts):
    headers = bearer(login(client, "teacher_one"))
    created = client.post("/api/v1/exams/practice", headers=headers, json=_practice([0.8, 1.5, 3, 0.25, 4.45]))
    assert created.status_code == 200, created.text
    assert [q["max_score"] for q in created.json()["questions"]] == [0.8, 1.5, 3, 0.25, 4.45]
    mock = client.post("/api/v1/exams/mock", headers=headers, json=_mock([0.5, 1, 2.5, 6]))
    assert mock.status_code == 200, mock.text
    assert sum(q["max_score"] for q in mock.json()["questions"]) == 10


def test_question_scores_are_rounded_to_two_decimals(client, accounts):
    headers = bearer(login(client, "teacher_one"))
    created = client.post("/api/v1/exams/practice", headers=headers, json=_practice([1.234, 0.005 + 1]))
    assert created.status_code == 200, created.text
    assert [q["max_score"] for q in created.json()["questions"]] == [1.23, 1.0]


@pytest.mark.parametrize("score", [0, -1, 0.001, 20.5, "abc", None])
@pytest.mark.parametrize("kind", ["practice", "mock"])
def test_invalid_question_scores_are_rejected(client, accounts, score, kind):
    headers = bearer(login(client, "teacher_one"))
    body = _practice([1, score]) if kind == "practice" else _mock([1, 1, score])
    assert client.post(f"/api/v1/exams/{kind}", headers=headers, json=body).status_code == 422


@pytest.mark.parametrize("kind", ["practice", "mock"])
def test_question_score_is_required(client, accounts, kind):
    headers = bearer(login(client, "teacher_one"))
    body = _practice([1]) if kind == "practice" else _mock([1])
    del body["questions"][0]["max_score"]
    assert client.post(f"/api/v1/exams/{kind}", headers=headers, json=body).status_code == 422


@pytest.mark.parametrize("model,question_model,answer_field,kind,section", [
    (PracticeExam, PracticeQuestion, "practice_question_id", "practice", None),
    (MockExam, MockQuestion, "mock_question_id", "mock", 1),
])
def test_scores_cannot_drop_below_awarded_grades(client, db, accounts, model, question_model,
                                                 answer_field, kind, section):
    teacher = accounts["teacher_one"]
    exam = model(title="Đề", teacher_id=teacher.id)
    db.add(exam); db.flush()
    extra = {"section": section} if section else {}
    questions = [question_model(exam_id=exam.id, content=f"Câu {i}", max_score=2, **extra) for i in range(2)]
    db.add_all(questions); db.flush()
    submission = Submission(student_id=accounts["student_one"].id, exam_type=kind.capitalize(),
                            **{f"{kind}_exam_id": exam.id}, status="Graded")
    db.add(submission); db.flush()
    answer = SubmissionAnswer(submission_id=submission.id, student_answer="x", **{answer_field: questions[0].id})
    db.add(answer); db.flush()
    db.add(SubmissionScore(submission_id=submission.id, answer_id=answer.id, score=1.5, teacher_id=teacher.id))
    db.commit()
    headers = bearer(login(client, "teacher_one"))

    def body(first, second):
        qs = [{"content": "Câu", "max_score": first, **extra}, {"content": "Câu", "max_score": second, **extra}]
        return {"title": "Đề", "questions": qs}

    rejected = client.put(f"/api/v1/exams/{kind}/{exam.id}", headers=headers, json=body(1, 2))
    assert rejected.status_code == 409
    assert "1.5" in rejected.json()["error"]["message"]
    # Ungraded questions can be lowered freely; graded ones down to the awarded score.
    ok = client.put(f"/api/v1/exams/{kind}/{exam.id}", headers=headers, json=body(1.5, 0.5))
    assert ok.status_code == 200, ok.text
    assert [q["max_score"] for q in ok.json()["questions"]] == [1.5, 0.5]
    raised = client.put(f"/api/v1/exams/{kind}/{exam.id}", headers=headers, json=body(5, 5))
    assert raised.status_code == 200
