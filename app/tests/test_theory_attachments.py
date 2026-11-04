import io
import zipfile

import pytest

from app.core.config import settings
from app.models import Class, TheoryArticle, TheoryAttachment
from app.services import theory as theory_service
from app.tests.conftest import bearer, login

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
GIF = b"GIF89a" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 64
AVIF = b"\x00\x00\x00\x1cftypavif" + b"\x00" * 64
PDF = b"%PDF-1.7\n" + b"\x00" * 64


def _docx():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", "<w:document/>")
    return buffer.getvalue()


def _zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("evil.txt", "x")
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


def _stored(upload_dir):
    return sorted(p.name for p in upload_dir.iterdir())


def _article(client, headers, **fields):
    body = {"title": "Bài thơ", "content": "<p>Nội dung dài</p>" * 2000, "main_category": "doc-hieu",
            "sub_category": "doc-hieu-tho", **fields}
    response = client.post("/api/v1/theory/", headers=headers, json=body)
    assert response.status_code == 200, response.text
    return response.json()


def _upload(client, headers, article_id, data, name="file.bin", content_type="application/octet-stream"):
    return client.post(f"/api/v1/theory/{article_id}/attachments", headers=headers,
                       files={"file": (name, data, content_type)})


def test_post_combines_long_text_images_links_and_files(client, accounts, upload_dir):
    teacher = bearer(login(client, "teacher_one"))
    article = _article(client, teacher)
    assert article["content_type"] == "mixed"
    assert len(article["content"]) > 30000

    image = _upload(client, teacher, article["id"], PNG, "ảnh minh họa.png", "image/png")
    assert image.status_code == 201, image.text
    assert image.json()["kind"] == "image"
    assert image.json()["mime_type"] == "image/png"
    second = _upload(client, teacher, article["id"], JPEG, "b.jpg")
    pdf = _upload(client, teacher, article["id"], PDF, "tai-lieu.pdf")
    docx = _upload(client, teacher, article["id"], _docx(), "giao-an.docx")
    assert [r.json()["kind"] for r in (second, pdf, docx)] == ["image", "file", "file"]
    assert docx.json()["mime_type"] == theory_service.DOCX_MIME
    link = client.post(f"/api/v1/theory/{article['id']}/links", headers=teacher,
                       json={"url": "https://vi.wikipedia.org/wiki/Truyện_Kiều", "title": "Truyện Kiều"})
    assert link.status_code == 201, link.text
    assert link.json()["kind"] == "link"
    assert link.json()["original_name"] == "Truyện Kiều"

    listed = client.get("/api/v1/theory/", headers=teacher).json()
    attachments = listed[0]["attachments"]
    assert [a["kind"] for a in attachments] == ["image", "image", "file", "file", "link"]
    assert [a["position"] for a in attachments] == [0, 1, 2, 3, 4]
    assert len(_stored(upload_dir)) == 4

    download = client.get(f"/api/v1/theory/attachments/{image.json()['id']}", headers=teacher)
    assert download.status_code == 200
    assert download.content == PNG
    assert download.headers["content-type"] == "image/png"
    assert download.headers["x-content-type-options"] == "nosniff"
    assert download.headers["content-disposition"].startswith("inline;")
    assert "%E1%BA%A3nh" in download.headers["content-disposition"]
    docx_download = client.get(f"/api/v1/theory/attachments/{docx.json()['id']}", headers=teacher)
    assert docx_download.headers["content-disposition"].startswith("attachment;")


@pytest.mark.parametrize("data,mime", [(PNG, "image/png"), (JPEG, "image/jpeg"), (GIF, "image/gif"),
                                       (WEBP, "image/webp"), (AVIF, "image/avif"), (PDF, "application/pdf")])
def test_file_type_comes_from_content(client, accounts, data, mime):
    teacher = bearer(login(client, "teacher_one"))
    article = _article(client, teacher)
    # A misleading client name and type must not matter.
    response = _upload(client, teacher, article["id"], data, "x.txt", "text/plain")
    assert response.status_code == 201, response.text
    assert response.json()["mime_type"] == mime


@pytest.mark.parametrize("data", [b"<svg xmlns='http://www.w3.org/2000/svg'/>", b"<html><script>",
                                  b"MZ\x90\x00", _zip(), b"PK\x03\x04broken"])
def test_disallowed_or_disguised_files_are_rejected(client, accounts, upload_dir, data):
    teacher = bearer(login(client, "teacher_one"))
    article = _article(client, teacher)
    response = _upload(client, teacher, article["id"], data, "image.png", "image/png")
    assert response.status_code == 415
    assert _stored(upload_dir) == []


def test_empty_and_oversized_files_are_rejected(client, accounts, upload_dir, monkeypatch):
    teacher = bearer(login(client, "teacher_one"))
    article = _article(client, teacher)
    assert _upload(client, teacher, article["id"], b"").status_code == 422
    monkeypatch.setattr(theory_service, "MAX_ATTACHMENT_BYTES", 100)
    assert _upload(client, teacher, article["id"], PNG + b"\x00" * 100).status_code == 413
    assert _stored(upload_dir) == []


def test_attachment_count_is_limited(client, accounts, monkeypatch):
    monkeypatch.setattr(theory_service, "MAX_ATTACHMENTS_PER_ARTICLE", 2)
    teacher = bearer(login(client, "teacher_one"))
    article = _article(client, teacher)
    assert _upload(client, teacher, article["id"], PNG).status_code == 201
    assert client.post(f"/api/v1/theory/{article['id']}/links", headers=teacher,
                       json={"url": "https://example.com"}).status_code == 201
    assert _upload(client, teacher, article["id"], PNG).status_code == 409
    assert client.post(f"/api/v1/theory/{article['id']}/links", headers=teacher,
                       json={"url": "https://example.org"}).status_code == 409


@pytest.mark.parametrize("url", ["javascript:alert(1)", "ftp://example.com/a", "not a url", ""])
def test_links_must_be_http(client, accounts, url):
    teacher = bearer(login(client, "teacher_one"))
    article = _article(client, teacher)
    assert client.post(f"/api/v1/theory/{article['id']}/links", headers=teacher,
                       json={"url": url}).status_code == 422


def test_only_the_owner_can_change_attachments(client, accounts, upload_dir):
    owner = bearer(login(client, "teacher_one"))
    other = bearer(login(client, "teacher_two"))
    student = bearer(login(client, "student_one"))
    article = _article(client, owner)
    image = _upload(client, owner, article["id"], PNG).json()
    assert _upload(client, other, article["id"], PNG).status_code == 404
    assert _upload(client, student, article["id"], PNG).status_code == 403
    assert client.post(f"/api/v1/theory/{article['id']}/links", headers=other,
                       json={"url": "https://example.com"}).status_code == 404
    assert client.delete(f"/api/v1/theory/{article['id']}/attachments/{image['id']}", headers=other).status_code == 404
    assert client.delete(f"/api/v1/theory/{article['id']}/attachments/{image['id']}", headers=student).status_code == 403
    assert len(_stored(upload_dir)) == 1


def test_download_follows_article_visibility(client, db, accounts):
    owner = bearer(login(client, "teacher_one"))
    article = _article(client, owner)
    image = _upload(client, owner, article["id"], PNG).json()
    path = f"/api/v1/theory/attachments/{image['id']}"

    room = Class(name="9A", teacher_id=accounts["teacher_two"].id)
    db.add(room)
    db.flush()
    accounts["student_two"].class_id = room.id
    db.commit()

    # Free students see every teacher's library; class students only their teacher's.
    assert client.get(path, headers=bearer(login(client, "student_one"))).status_code == 200
    assert client.get(path, headers=bearer(login(client, "student_two"))).status_code == 404
    assert client.get(path, headers=bearer(login(client, "teacher_two"))).status_code == 404
    assert client.get(path).status_code == 401

    db.query(TheoryArticle).filter_by(id=article["id"]).update({"is_published": False})
    db.commit()
    assert client.get(path, headers=bearer(login(client, "student_one"))).status_code == 404
    assert client.get(path, headers=owner).status_code == 200


def test_links_are_not_downloadable(client, accounts):
    owner = bearer(login(client, "teacher_one"))
    article = _article(client, owner)
    link = client.post(f"/api/v1/theory/{article['id']}/links", headers=owner,
                       json={"url": "https://example.com"}).json()
    assert client.get(f"/api/v1/theory/attachments/{link['id']}", headers=owner).status_code == 404


def test_deleting_removes_files_after_commit(client, db, accounts, upload_dir):
    owner = bearer(login(client, "teacher_one"))
    article = _article(client, owner)
    first = _upload(client, owner, article["id"], PNG).json()
    _upload(client, owner, article["id"], PDF)
    assert len(_stored(upload_dir)) == 2

    assert client.delete(f"/api/v1/theory/{article['id']}/attachments/{first['id']}", headers=owner).status_code == 204
    assert len(_stored(upload_dir)) == 1
    assert client.delete(f"/api/v1/theory/{article['id']}/attachments/{first['id']}", headers=owner).status_code == 404

    assert client.delete(f"/api/v1/theory/{article['id']}", headers=owner).status_code == 204
    assert _stored(upload_dir) == []
    assert db.query(TheoryAttachment).count() == 0


def _then_fail(real):
    def wrapper(*args, **kwargs):
        real(*args, **kwargs)
        raise RuntimeError("database failed later in the request")
    return wrapper


def test_rolled_back_requests_leave_disk_consistent(client, accounts, upload_dir, monkeypatch):
    from app.api import theory as theory_api
    owner = bearer(login(client, "teacher_one"))
    article = _article(client, owner)
    kept = _upload(client, owner, article["id"], PNG).json()

    # An upload whose transaction rolls back leaves no orphan file behind.
    monkeypatch.setattr(theory_api, "add_file_attachment", _then_fail(theory_service.add_file_attachment))
    assert _upload(client, owner, article["id"], PDF).status_code == 500
    assert len(_stored(upload_dir)) == 1

    # A delete whose transaction rolls back keeps the file the row still points to.
    monkeypatch.setattr(theory_api, "delete_attachment", _then_fail(theory_service.delete_attachment))
    assert client.delete(f"/api/v1/theory/{article['id']}/attachments/{kept['id']}", headers=owner).status_code == 500
    monkeypatch.setattr(theory_api, "delete_theory_article", _then_fail(theory_service.delete_theory_article))
    assert client.delete(f"/api/v1/theory/{article['id']}", headers=owner).status_code == 500
    assert len(_stored(upload_dir)) == 1
    assert client.get(f"/api/v1/theory/attachments/{kept['id']}", headers=owner).content == PNG


def test_legacy_and_partial_updates_keep_working(client, db, accounts):
    owner = bearer(login(client, "teacher_one"))
    legacy = TheoryArticle(title="Cũ", content_type="image", content="data:image/png;base64,AAAA",
                           teacher_id=accounts["teacher_one"].id)
    db.add(legacy)
    db.commit()
    listed = client.get("/api/v1/theory/", headers=owner).json()
    assert listed[0]["content_type"] == "image"
    assert listed[0]["content"].startswith("data:image/png")
    assert listed[0]["attachments"] == []

    article = _article(client, owner, content="")
    assert article["content"] == ""
    updated = client.patch(f"/api/v1/theory/{article['id']}", headers=owner, json={"content": "<p>Mới</p>"})
    assert updated.status_code == 200
    assert updated.json()["content"] == "<p>Mới</p>"


def test_old_upload_endpoint_is_gone(client, accounts):
    owner = bearer(login(client, "teacher_one"))
    response = client.post("/api/v1/theory/upload", headers=owner,
                           data={"title": "x", "content_type": "Image"}, files={"file": ("a.png", PNG)})
    assert response.status_code in (404, 405, 422)
