"""Upload validation, filename safety and a small in-memory rate limiter."""
from __future__ import annotations

import re
import time
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass

import pymupdf

JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")


class ValidationError(Exception):
    def __init__(self, message: str, status: int = 400, code: str = "invalid_file"):
        super().__init__(message)
        self.message, self.status, self.code = message, status, code


@dataclass
class PdfInfo:
    page_count: int


def safe_stem(filename: str | None) -> str:
    """Return a harmless file stem usable in Content-Disposition."""
    name = (filename or "document").replace("\\", "/").split("/")[-1]
    stem = re.sub(r"\.pdf$", "", name, flags=re.I)
    # keep letters, digits and combining marks (Bangla vowel signs are marks, which \w would drop)
    stem = "".join(ch for ch in stem if ch.isalnum() or ch in "-_ " or unicodedata.category(ch).startswith("M")).strip()[:80]
    return stem or "document"


def validate_pdf_bytes(data: bytes, *, max_pages: int, max_bytes: int) -> PdfInfo:
    if not data:
        raise ValidationError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise ValidationError(f"File is larger than the {max_bytes // (1024 * 1024)} MB limit.", 413, "too_large")
    # Real PDFs have the %PDF- header within the first 1024 bytes.
    if b"%PDF-" not in data[:1024]:
        raise ValidationError("This does not look like a PDF file (missing %PDF header).", 415, "not_pdf")
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception:
        raise ValidationError("The PDF is damaged or could not be opened.", 422, "corrupt_pdf")
    try:
        if doc.needs_pass or doc.is_encrypted:
            raise ValidationError("Password-protected PDFs are not supported. Remove the password first.", 422, "encrypted")
        n = doc.page_count
        if n < 1:
            raise ValidationError("The PDF has no pages.", 422, "no_pages")
        if n > max_pages:
            raise ValidationError(f"The PDF has {n} pages; the limit is {max_pages}.", 413, "too_many_pages")
        return PdfInfo(page_count=n)
    finally:
        doc.close()


class RateLimiter:
    """Sliding-window limiter, per client key. In-memory: fine for one instance."""

    def __init__(self, limit: int, window_s: int = 60):
        self.limit, self.window = limit, window_s
        self.hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        if self.limit <= 0:
            return True
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        if len(self.hits) > 5000:  # bound memory
            for k in [k for k, v in self.hits.items() if not v]:
                self.hits.pop(k, None)
        return True
