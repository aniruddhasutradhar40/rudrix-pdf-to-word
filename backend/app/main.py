"""Rudrix PDF to Word - FastAPI application."""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
import threading
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from . import __version__
from .config import get_settings
from .converter import ConversionTimeout, run_isolated
from .ocr import LANG_LABELS, ocr_status
from .security import JOB_ID_RE, RateLimiter, ValidationError, safe_stem, validate_pdf_bytes

log = logging.getLogger("rudrix")
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def create_app() -> FastAPI:
    settings = get_settings()
    settings.work_dir.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title="Rudrix PDF to Word API", version=__version__, docs_url="/docs", redoc_url=None)
    limiter = RateLimiter(settings.rate_limit_per_min)
    semaphore = asyncio.Semaphore(settings.max_concurrent)

    app.add_middleware(
        CORSMiddleware, allow_origins=settings.allowed_origins, allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"], expose_headers=["Content-Disposition"], max_age=600)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        resp = await call_next(request)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["X-Frame-Options"] = "DENY"
        return resp

    # ---- cleanup ---------------------------------------------------------
    def purge(force_all: bool = False) -> int:
        removed, now = 0, time.time()
        for d in settings.work_dir.iterdir():
            try:
                if d.is_dir() and JOB_ID_RE.match(d.name) and (force_all or now - d.stat().st_mtime > settings.file_ttl_s):
                    shutil.rmtree(d, ignore_errors=True); removed += 1
            except OSError:
                pass
        return removed

    def janitor():
        while True:
            time.sleep(60)
            try:
                purge()
            except Exception:  # noqa: BLE001
                log.exception("cleanup failed")

    purge()  # drop leftovers from a previous run
    threading.Thread(target=janitor, daemon=True, name="rudrix-janitor").start()
    app.state.purge = purge
    app.state.settings = settings

    def client_ip(request: Request) -> str:
        if settings.trust_proxy:
            fwd = request.headers.get("x-forwarded-for")
            if fwd:
                return fwd.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def err(status: int, code: str, message: str) -> JSONResponse:
        return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})

    # ---- routes ----------------------------------------------------------
    @app.get("/health")
    def health():
        return {"status": "ok", "version": __version__}

    @app.get("/api/capabilities")
    def capabilities():
        o = ocr_status()
        return {
            "version": __version__,
            "modes": ["editable", "preserve"],
            "limits": {"max_upload_mb": settings.max_upload_mb, "max_pages": settings.max_pages,
                       "ocr_max_pages": settings.ocr_max_pages, "file_ttl_seconds": settings.file_ttl_s},
            "ocr": {"available": o["available"], "reason": o["reason"],
                    "languages": [{"code": c, "label": LANG_LABELS[c]} for c in o["languages"]]},
        }

    @app.post("/api/convert")
    async def convert(request: Request, file: UploadFile = File(...), mode: str = Form("editable"),
                      ocr: str = Form("true"), ocr_lang: str = Form("eng")):
        if not limiter.allow(client_ip(request)):
            return err(429, "rate_limited", "Too many requests. Please wait a minute and try again.")
        if mode not in ("editable", "preserve"):
            return err(400, "bad_mode", "Mode must be 'editable' or 'preserve'.")
        if ocr_lang.lower().replace(",", "+") not in ("eng", "ben", "eng+ben", "ben+eng"):
            return err(400, "bad_language", "OCR language must be eng, ben or eng+ben.")
        # Read with a hard size cap, never trusting Content-Length.
        buf = bytearray()
        while chunk := await file.read(1024 * 1024):
            buf.extend(chunk)
            if len(buf) > settings.max_upload_bytes:
                return err(413, "too_large", f"File is larger than the {settings.max_upload_mb} MB limit.")
        try:
            validate_pdf_bytes(bytes(buf), max_pages=settings.max_pages, max_bytes=settings.max_upload_bytes)
        except ValidationError as e:
            return err(e.status, e.code, e.message)

        job_id = uuid.uuid4().hex
        job_dir = settings.work_dir / job_id
        job_dir.mkdir(parents=True)
        pdf_path, out_path = job_dir / "input.pdf", job_dir / "output.docx"
        pdf_path.write_bytes(bytes(buf))
        del buf
        stem = safe_stem(file.filename)
        try:
            async with semaphore:
                report = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: run_isolated(str(pdf_path), str(out_path), mode, ocr.lower() == "true",
                                               ocr_lang.lower().replace(",", "+"), settings.ocr_max_pages,
                                               settings.conversion_timeout_s))
        except ConversionTimeout:
            shutil.rmtree(job_dir, ignore_errors=True)
            return err(504, "timeout", "Conversion took too long and was stopped. Try a smaller file or Editable mode.")
        except Exception as exc:  # noqa: BLE001
            log.exception("conversion failed")
            shutil.rmtree(job_dir, ignore_errors=True)
            return err(500, "conversion_failed", "Conversion failed. The PDF may use features that cannot be converted.")
        finally:
            pdf_path.unlink(missing_ok=True)  # original is deleted right after processing
        (job_dir / "meta.json").write_text(json.dumps({"stem": stem}), encoding="utf-8")
        return {"job_id": job_id, "filename": f"{stem}.docx", "download_url": f"/api/download/{job_id}",
                "size_bytes": out_path.stat().st_size, "expires_in_seconds": settings.file_ttl_s, "report": report}

    def _job_file(job_id: str):
        if not JOB_ID_RE.match(job_id):
            return None, None
        d = settings.work_dir / job_id
        f = d / "output.docx"
        return (d, f) if f.is_file() else (None, None)

    @app.get("/api/download/{job_id}")
    def download(job_id: str):
        d, f = _job_file(job_id)
        if not f:
            return err(404, "not_found", "File not found or it has expired. Please convert again.")
        try:
            stem = json.loads((d / "meta.json").read_text(encoding="utf-8")).get("stem", "document")
        except Exception:  # noqa: BLE001
            stem = "document"
        return FileResponse(f, media_type=DOCX_MIME, filename=f"{stem}.docx")

    @app.delete("/api/jobs/{job_id}")
    def delete_job(job_id: str):
        d, f = _job_file(job_id)
        if d:
            shutil.rmtree(d, ignore_errors=True)
        return {"deleted": bool(d)}

    return app


app = create_app()
