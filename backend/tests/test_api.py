import io
import time

import pytest
from docx import Document
from fastapi.testclient import TestClient


def make_client(monkeypatch, tmp_path, **env):
    monkeypatch.setenv("RUDRIX_WORK_DIR", str(tmp_path / "jobs"))
    for k, v in env.items():
        monkeypatch.setenv(k, str(v))
    from app.main import create_app
    app = create_app()
    return TestClient(app), app


def post(c, data, name="a.pdf", **form):
    return c.post("/api/convert", files={"file": (name, data, "application/pdf")}, data=form)


def test_health_and_capabilities(monkeypatch, tmp_path):
    c, _ = make_client(monkeypatch, tmp_path)
    assert c.get("/health").json()["status"] == "ok"
    cap = c.get("/api/capabilities").json()
    assert cap["modes"] == ["editable", "preserve"] and "available" in cap["ocr"]
    assert c.get("/health").headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("mode", ["editable", "preserve"])
def test_convert_and_download_then_cleanup(monkeypatch, tmp_path, text_pdf, mode):
    c, app = make_client(monkeypatch, tmp_path)
    r = post(c, text_pdf.read_bytes(), name="My Report.pdf", mode=mode)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["filename"] == "My Report.docx" and j["report"]["disclaimer"]
    d = c.get(j["download_url"])
    assert d.status_code == 200 and "wordprocessingml" in d.headers["content-type"]
    assert "Quarterly Report" in "\n".join(p.text for p in Document(io.BytesIO(d.content)).paragraphs) or mode == "preserve"
    job_dir = tmp_path / "jobs" / j["job_id"]
    assert not (job_dir / "input.pdf").exists()  # uploaded PDF deleted after conversion
    assert c.delete(f"/api/jobs/{j['job_id']}").json()["deleted"] is True
    assert c.get(j["download_url"]).status_code == 404


def test_rejects_non_pdf(monkeypatch, tmp_path):
    c, _ = make_client(monkeypatch, tmp_path)
    r = post(c, b"just text", name="x.pdf")
    assert r.status_code == 415 and r.json()["error"]["code"] == "not_pdf"
    assert post(c, b"", name="x.pdf").status_code == 400


def test_rejects_encrypted(monkeypatch, tmp_path, encrypted_pdf):
    c, _ = make_client(monkeypatch, tmp_path)
    assert post(c, encrypted_pdf.read_bytes()).json()["error"]["code"] == "encrypted"


def test_size_limit_enforced_while_streaming(monkeypatch, tmp_path, text_pdf):
    c, _ = make_client(monkeypatch, tmp_path, RUDRIX_MAX_UPLOAD_MB=1)
    big = text_pdf.read_bytes() + b"0" * (2 * 1024 * 1024)
    assert post(c, big).status_code == 413


def test_bad_params(monkeypatch, tmp_path, text_pdf):
    c, _ = make_client(monkeypatch, tmp_path)
    assert post(c, text_pdf.read_bytes(), mode="hack").status_code == 400
    assert post(c, text_pdf.read_bytes(), ocr_lang="../etc").status_code == 400


def test_download_path_traversal_blocked(monkeypatch, tmp_path):
    c, _ = make_client(monkeypatch, tmp_path)
    for bad in ["..%2f..%2fetc%2fpasswd", "../x", "A" * 32, "zz"]:
        assert c.get(f"/api/download/{bad}").status_code in (404, 422)


def test_rate_limit(monkeypatch, tmp_path):
    c, _ = make_client(monkeypatch, tmp_path, RUDRIX_RATE_LIMIT_PER_MIN=2)
    codes = [post(c, b"x").status_code for _ in range(3)]
    assert codes[-1] == 429


def test_expired_jobs_are_purged(monkeypatch, tmp_path, text_pdf):
    c, app = make_client(monkeypatch, tmp_path, RUDRIX_FILE_TTL_SECONDS=1)
    j = post(c, text_pdf.read_bytes()).json()
    assert (tmp_path / "jobs" / j["job_id"]).exists()
    time.sleep(1.2)
    assert app.state.purge() == 1
    assert c.get(j["download_url"]).status_code == 404


def test_timeout_kills_conversion(monkeypatch, tmp_path, text_pdf):
    c, _ = make_client(monkeypatch, tmp_path, RUDRIX_TIMEOUT_SECONDS=0)
    r = post(c, text_pdf.read_bytes())
    assert r.status_code == 504
    assert not any((tmp_path / "jobs").iterdir())  # job dir cleaned after failure
