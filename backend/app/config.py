"""Configuration, read from environment variables (see .env.example)."""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _list(name: str, default: str) -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    max_upload_mb: int = field(default_factory=lambda: _int("RUDRIX_MAX_UPLOAD_MB", 25))
    max_pages: int = field(default_factory=lambda: _int("RUDRIX_MAX_PAGES", 100))
    ocr_max_pages: int = field(default_factory=lambda: _int("RUDRIX_OCR_MAX_PAGES", 30))
    conversion_timeout_s: int = field(default_factory=lambda: _int("RUDRIX_TIMEOUT_SECONDS", 240))
    file_ttl_s: int = field(default_factory=lambda: _int("RUDRIX_FILE_TTL_SECONDS", 900))
    max_concurrent: int = field(default_factory=lambda: _int("RUDRIX_MAX_CONCURRENT", 2))
    rate_limit_per_min: int = field(default_factory=lambda: _int("RUDRIX_RATE_LIMIT_PER_MIN", 10))
    allowed_origins: list[str] = field(
        default_factory=lambda: _list("RUDRIX_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500")
    )
    work_dir: Path = field(
        default_factory=lambda: Path(os.getenv("RUDRIX_WORK_DIR", str(Path(tempfile.gettempdir()) / "rudrix_jobs")))
    )
    trust_proxy: bool = field(default_factory=lambda: os.getenv("RUDRIX_TRUST_PROXY", "false").lower() == "true")

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def get_settings() -> Settings:
    return Settings()
