"""OCR capability detection (Tesseract through PyMuPDF). Free, local, no external API."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import pymupdf

LANG_LABELS = {"eng": "English", "ben": "Bangla (বাংলা)"}


def _tessdata_dir() -> str | None:
    env = os.getenv("TESSDATA_PREFIX")
    if env and Path(env).is_dir():
        return env
    try:
        d = pymupdf.get_tessdata()
        if d and Path(d).is_dir():
            return d
    except Exception:
        pass
    for p in Path("/usr/share").glob("tesseract-ocr/*/tessdata"):
        return str(p)
    for p in ("/usr/share/tessdata", "/usr/local/share/tessdata", "/opt/homebrew/share/tessdata"):
        if Path(p).is_dir():
            return p
    return None


def ocr_status() -> dict:
    """Which OCR languages are really installed on this server right now."""
    if not shutil.which("tesseract"):
        return {"available": False, "languages": [], "tessdata": None, "reason": "tesseract binary not found"}
    d = _tessdata_dir()
    if not d:
        return {"available": False, "languages": [], "tessdata": None, "reason": "tessdata directory not found"}
    langs = sorted(p.stem for p in Path(d).glob("*.traineddata") if p.stem in LANG_LABELS)
    return {"available": bool(langs), "languages": langs, "tessdata": d,
            "reason": None if langs else "no English/Bangla language data installed"}


def resolve_languages(requested: str, status: dict) -> tuple[str | None, list[str]]:
    """Map 'eng' | 'ben' | 'eng+ben' to installed languages. Returns (tess_lang, warnings)."""
    warnings: list[str] = []
    wanted = [x for x in requested.lower().replace(",", "+").split("+") if x in LANG_LABELS] or ["eng"]
    have = [x for x in wanted if x in status.get("languages", [])]
    missing = [x for x in wanted if x not in have]
    if missing:
        warnings.append(
            "OCR language data not installed on this server: "
            + ", ".join(LANG_LABELS[m] for m in missing)
            + (". Using the remaining languages." if have else ". OCR was skipped.")
        )
    return ("+".join(have) if have else None), warnings
