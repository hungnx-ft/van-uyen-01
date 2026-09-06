import pytest

from app.models import Class, PracticeExam, PracticeQuestion, Submission, SubmissionAnswer, User
from app.tests.conftest import bearer, login


@pytest.fixture
def classrooms(db, accounts):
    first = Class(name="9A", teacher_id=accounts["teacher_one"].id)
    second = Class(name="9B", teacher_id=accounts["teacher_two"].id)
    db.add_all([first, second]); db.flush()
    accounts["student_one"].class_id = first.id
    accounts["student_two"].class_id = second.id
    db.commit()
    return first, second


def test_students_cannot_create_classes_or_accounts(client, accounts):
    headers = bearer(login(client))
    assert client.post("/api/v1/classes/", headers=headers, json={"name": "9A"}).status_code == 403
    assert client.post("/api/v1/users/students", headers=headers, json={"username": "another", "password": "password-123", "full_name": "Another", "class_id": 1}).status_code == 403


def test_teacher_only_sees_own_classes_and_creates_students_in_own_class(client, db, accounts, classrooms):
    headers = bearer(login(client, "teacher_one"))
    first, second = classrooms
    assert [c["id"] for c in client.get("/api/v1/classes/", headers=headers).json()] == [first.id]
    body = {"username": "new_class_student", "password": "password-123", "full_name": "Học sinh mới", "class_id": second.id}
    assert client.post("/api/v1/users/students", headers=headers, json=body).status_code == 404
    assert db.query(User).filter_by(username=body["username"]).first() is None
    body["class_id"] = first.id
    response = client.post("/api/v1/users/students", headers=headers, json=body)
    assert response.status_code == 201, response.text
    assert response.json()["class_id"] == first.id
    assert login(client, body["username"], body["password"])


def test_teacher_can_manage_free_student_but_not_other_teacher_students(client, db, accounts, classrooms):
    headers = bearer(login(client, "teacher_one"))
    free = client.post("/api/v1/auth/register", json={"username": "free_student", "password": "password-123", "full_name": "Tự do"}).json()
    for user_id in (accounts["teacher_two"].id, accounts["student_two"].id, 999999):
        assert client.put(f"/api/v1/users/students/{user_id}/password", headers=headers, json={"password": "new-password"}).status_code == 404
    response = client.put(f'/api/v1/users/students/{free["id"]}/password', headers=headers, json={"password": "new-password"})
    assert response.status_code == 200
    assert login(client, "free_student", "new-password")


def test_teacher_student_list_includes_self_registered_students(client, accounts):
    headers = bearer(login(client, "teacher_one"))
    registered = client.post(
        "/api/v1/auth/register",
        json={"username": "free_visible", "password": "password-123", "full_name": "Học sinh tự do"},
    )
    assert registered.status_code == 201
    response = client.get("/api/v1/users/students?limit=100", headers=headers)
    assert response.status_code == 200, response.text
    assert any(item["id"] == registered.json()["id"] and item["class_id"] is None
               for item in response.json()["items"])
    old = login(client)
    response = client.put(f'/api/v1/users/students/{accounts["student_one"].id}/password', headers=headers, json={"password": "new-password"})
    assert response.status_code == 200
    assert "password_hash" not in response.json()
    assert client.get("/api/v1/auth/me", headers=bearer(old)).status_code == 401
    assert login(client, password="new-password")


def test_class_move_requires_both_source_and_destination_ownership(client, accounts, classrooms):
    headers = bearer(login(client, "teacher_one"))
    first, second = classrooms
    assert client.put(f'/api/v1/classes/{first.id}/students/{accounts["student_two"].id}', headers=headers).status_code == 404
    assert client.put(f'/api/v1/classes/{second.id}/students/{accounts["student_one"].id}', headers=headers).status_code == 404
    own = client.post("/api/v1/classes/", headers=headers, json={"name": "9C"}).json()
    response = client.put(f'/api/v1/classes/{own["id"]}/students/{accounts["student_one"].id}', headers=headers)
    assert response.status_code == 200 and response.json()["class_id"] == own["id"]


def test_submission_and_event_cannot_reference_another_students_resources(client, db, accounts, classrooms):
    exam = PracticeExam(title="Teacher two exam", teacher_id=accounts["teacher_two"].id)
    db.add(exam); db.flush()
    question = PracticeQuestion(exam_id=exam.id, content="Q", max_score=4)
    db.add(question); db.flush()
    submission = Submission(student_id=accounts["student_two"].id, exam_type="Practice", practice_exam_id=exam.id, status="Submitted")
    db.add(submission); db.flush()
    answer = SubmissionAnswer(submission_id=submission.id, practice_question_id=question.id, student_answer="Answer")
    db.add(answer); db.commit()
    student_headers = bearer(login(client))
    assert client.get("/api/v1/exams/practice", headers=student_headers).json() == []
    assert client.get("/api/v1/submissions/my-submissions", headers=student_headers).json() == []
    assert client.post("/api/v1/submissions/", headers=student_headers, json={"exam_type": "Practice", "practice_exam_id": exam.id, "answers": []}).status_code == 404
    assert client.post("/api/v1/anti-cheat/event", headers=student_headers, json={"submission_id": submission.id, "event_type": "tab_switch"}).status_code == 404
    teacher_headers = bearer(login(client, "teacher_one"))
    assert client.post(f"/api/v1/submissions/{submission.id}/grade", headers=teacher_headers, json={"scores": [{"answer_id": answer.id, "score": 1}]}).status_code == 404
    db.refresh(submission)
    assert submission.leave_tab_count == 0 and submission.status == "Submitted"
