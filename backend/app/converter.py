"""Conversion orchestration. `run_job` executes inside a child process so it can be killed on timeout."""
from __future__ import annotations

import json
import multiprocessing as mp
import traceback
from pathlib import Path

from .analyzer import analyze_pdf
from .editable import build_editable
from .ocr import ocr_status, resolve_languages
from .quality import assess

MODES = ("editable", "preserve")


class ConversionTimeout(Exception):
    pass


def convert_preserve(pdf_path: str, out_path: str) -> list[str]:
    """Maximum Layout Preservation: pdf2docx reconstructs positions, fonts, tables and images."""
    from pdf2docx import Converter
    notes: list[str] = []
    cv = Converter(pdf_path)
    try:
        cv.convert(out_path, start=0, end=None, multi_processing=False)
    finally:
        cv.close()
    return notes


def run_job(pdf_path: str, out_path: str, mode: str, ocr_enabled: bool, ocr_lang: str, ocr_max_pages: int) -> dict:
    analysis = analyze_pdf(pdf_path)
    warnings: list[str] = []
    ocr_pages: list[int] = []
    stats: dict = {}
    scanned = analysis["scanned_pages"]
    tess_lang, tessdata = None, None

    if scanned:
        status = ocr_status()
        if ocr_enabled and mode == "editable":
            tess_lang, w = resolve_languages(ocr_lang, status)
            warnings += w
            tessdata = status.get("tessdata")
            if not status["available"]:
                warnings.append(f"OCR is not available on this server ({status['reason']}). Scanned pages become images.")
                tess_lang = None
        elif mode == "preserve":
            warnings.append("Scanned pages are kept as page images in Maximum Layout Preservation mode (exact look, but not editable). Use Editable Word + OCR to get text.")
        else:
            warnings.append("OCR is turned off; scanned pages become images.")

    if mode == "editable":
        info = build_editable(pdf_path, out_path, ocr_lang=tess_lang, ocr_tessdata=tessdata,
                              ocr_max_pages=ocr_max_pages, scanned_pages=scanned)
        warnings += info["warnings"]; ocr_pages = info["ocr_pages"]; stats = info["stats"]
    else:
        warnings += convert_preserve(pdf_path, out_path)

    if not Path(out_path).exists() or Path(out_path).stat().st_size < 1000:
        raise RuntimeError("Conversion produced no output file.")
    report = assess(pdf_path, out_path, analysis=analysis, ocr_pages=ocr_pages, warnings=warnings)
    report["mode"] = mode
    report["source"] = {"pages": analysis["page_count"], "scanned_pages": scanned,
                        "tables_detected": analysis["tables"], "images": analysis["images"]}
    report["ocr"] = {"used": bool(ocr_pages), "pages": ocr_pages, "language": tess_lang}
    if stats:
        report["build"] = stats
    return report


def _child(result_path: str, args: tuple) -> None:
    try:
        res = {"ok": True, "report": run_job(*args)}
    except Exception as exc:  # noqa: BLE001
        res = {"ok": False, "error": f"{type(exc).__name__}: {exc}", "trace": traceback.format_exc()[-1500:]}
    Path(result_path).write_text(json.dumps(res), encoding="utf-8")


def run_isolated(pdf_path: str, out_path: str, mode: str, ocr_enabled: bool, ocr_lang: str,
                 ocr_max_pages: int, timeout: int) -> dict:
    """Run the conversion in a separate process with a hard timeout. Blocking; call from a thread."""
    if mode not in MODES:
        raise ValueError("invalid mode")
    result_path = out_path + ".result.json"
    ctx = mp.get_context("spawn")
    p = ctx.Process(target=_child, args=(result_path, (pdf_path, out_path, mode, ocr_enabled, ocr_lang, ocr_max_pages)), daemon=True)
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.kill(); p.join(5)
        raise ConversionTimeout()
    rp = Path(result_path)
    if not rp.exists():
        raise RuntimeError("The conversion process crashed. The PDF may be malformed.")
    res = json.loads(rp.read_text(encoding="utf-8"))
    rp.unlink(missing_ok=True)
    if not res["ok"]:
        raise RuntimeError(res["error"])
    return res["report"]
