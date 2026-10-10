from app.models import Class, User
from app.tests.conftest import bearer, login


def _practice_exam(title="Bài luyện tập", duration_minutes=50, question_count=5):
    return {
        "title": title,
        "target_group": "Lớp 9",
        "passage": "Đoạn văn",
        "genre": "Nghị luận",
        "duration_minutes": duration_minutes,
        "questions": [
            {"content": f"Câu {index}", "max_score": 0.8, "answer_key": "A"}
            for index in range(1, question_count + 1)
        ],
    }


def test_theory_crud_is_owned_and_persists(client, accounts):
    teacher_one = bearer(login(client, "teacher_one"))
    teacher_two = bearer(login(client, "teacher_two"))
    created = client.post(
        "/api/v1/theory/",
        headers=teacher_one,
        json={
            "title": "Ngữ pháp câu",
            "content_type": "Lý thuyết",
            "content": "Nội dung ban đầu",
            "main_category": "Tiếng Việt",
            "sub_category": "Câu",
            "description": "Mô tả",
            "icon": "📚",
        },
    )
    assert created.status_code == 200, created.text
    article_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/theory/{article_id}",
        headers=teacher_one,
        json={"title": "Ngữ pháp câu nâng cao", "description": "Đã cập nhật"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Ngữ pháp câu nâng cao"
    assert client.patch(f"/api/v1/theory/{article_id}", headers=teacher_two, json={"title": "Sửa trái phép"}).status_code == 404
    assert client.delete(f"/api/v1/theory/{article_id}", headers=teacher_one).status_code == 204


def test_exam_crud_and_delete_protects_assigned_exam(client, db, accounts):
    headers = bearer(login(client, "teacher_one"))
    created = client.post("/api/v1/exams/practice", headers=headers, json=_practice_exam())
    assert created.status_code == 200, created.text
    exam_id = created.json()["id"]
    assert created.json()["duration_minutes"] == 50
    assert len(created.json()["questions"]) == 5
    updated = client.put(
        f"/api/v1/exams/practice/{exam_id}",
        headers=headers,
        json=_practice_exam("Bài luyện tập đã sửa"),
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Bài luyện tập đã sửa"
    assert updated.json()["duration_minutes"] == 50
    dynamic = client.put(
        f"/api/v1/exams/practice/{exam_id}",
        headers=headers,
        json=_practice_exam("Bài luyện tập 8 câu", question_count=8),
    )
    assert dynamic.status_code == 200, dynamic.text
    assert len(dynamic.json()["questions"]) == 8
    assert client.delete(f"/api/v1/exams/practice/{exam_id}", headers=headers).status_code == 204

    assigned = client.post("/api/v1/exams/practice", headers=headers, json=_practice_exam("Bài đã giao"))
    assigned_id = assigned.json()["id"]
    classroom = Class(name="9A", teacher_id=accounts["teacher_one"].id)
    db.add(classroom)
    db.commit()
    assignment = client.post(
        "/api/v1/assignments/",
        headers=headers,
        json={
            "class_id": classroom.id,
            "exam_type": "Practice",
            "practice_exam_id": assigned_id,
            "exam_title": "Bài đã giao",
            "instructions": "Làm bài",
        },
    )
    assert assignment.status_code == 201, assignment.text
    assert client.delete(f"/api/v1/exams/practice/{assigned_id}", headers=headers).status_code == 409


def test_student_status_and_delete_are_owner_scoped(client, db, accounts):
    classroom = Class(name="9A", teacher_id=accounts["teacher_one"].id)
    db.add(classroom)
    db.flush()
    accounts["student_one"].class_id = classroom.id
    db.commit()
    teacher_one = bearer(login(client, "teacher_one"))
    teacher_two = bearer(login(client, "teacher_two"))
    student_id = accounts["student_one"].id

    response = client.patch(f"/api/v1/users/students/{student_id}/status", headers=teacher_one, json={"is_active": False})
    assert response.status_code == 200 and response.json()["is_active"] is False
    assert client.post("/api/v1/auth/login", data={"username": "student_one", "password": "password-123"}).status_code == 401
    assert client.delete(f"/api/v1/users/students/{student_id}", headers=teacher_two).status_code == 404
    assert client.delete(f"/api/v1/users/students/{student_id}", headers=teacher_one).status_code == 204
    db.expire_all()
    assert db.get(User, student_id) is None


def test_student_sees_assignments_for_own_class(client, db, accounts):
    classroom = Class(name="9A", teacher_id=accounts["teacher_one"].id)
    db.add(classroom)
    db.flush()
    accounts["student_one"].class_id = classroom.id
    db.commit()
    teacher_headers = bearer(login(client, "teacher_one"))
    exam = client.post("/api/v1/exams/practice", headers=teacher_headers, json=_practice_exam("Bài của lớp 9A")).json()
    created = client.post(
        "/api/v1/assignments/",
        headers=teacher_headers,
        json={
            "class_id": classroom.id,
            "exam_type": "Practice",
            "practice_exam_id": exam["id"],
            "exam_title": exam["title"],
            "instructions": "Ôn tập",
        },
    )
    assert created.status_code == 201
    student_headers = bearer(login(client, "student_one"))
    assignments = client.get("/api/v1/assignments/", headers=student_headers)
    assert assignments.status_code == 200
    assert [item["exam_title"] for item in assignments.json()] == ["Bài của lớp 9A"]
