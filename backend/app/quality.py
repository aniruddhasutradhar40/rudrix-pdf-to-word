"""Heuristic quality checks comparing the source PDF with the produced DOCX.

These are automated sanity checks. They do NOT prove that the document looks identical
in Microsoft Word; always review the output.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

import pymupdf
from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WORD_RE = re.compile(r"\w+", re.UNICODE)


def docx_stats(docx_path: str) -> dict:
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml")
        media = [n for n in z.namelist() if n.startswith("word/media/")]
    root = etree.fromstring(xml)
    ns = {"w": W_NS}
    text = " ".join(t.text or "" for t in root.iterfind(".//w:t", ns))
    return {
        "text": text,
        "tables": len(root.findall(".//w:tbl", ns)),
        "images": len(media),
        "paragraphs": len(root.findall(".//w:p", ns)),
        "sections": len(root.findall(".//w:sectPr", ns)),
    }


def _words(text: str) -> Counter:
    return Counter(w.lower() for w in WORD_RE.findall(text))


def render_page_count(docx_path: str, timeout: int = 90) -> int | None:
    """Optional: page count via LibreOffice (an approximation of Word, not Word itself)."""
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe or os.getenv("RUDRIX_QUALITY_RENDER", "true").lower() != "true":
        return None
    with tempfile.TemporaryDirectory() as tmp:
        try:
            subprocess.run(
                [exe, f"-env:UserInstallation=file://{tmp}/profile", "--headless", "--convert-to", "pdf", "--outdir", tmp, docx_path],
                capture_output=True, timeout=timeout, check=True)
            pdf = Path(tmp) / (Path(docx_path).stem + ".pdf")
            if not pdf.exists():
                return None
            with pymupdf.open(pdf) as d:
                return d.page_count
        except Exception:
            return None


def assess(pdf_path: str, docx_path: str, *, analysis: dict, ocr_pages: list[int], warnings: list[str]) -> dict:
    d = docx_stats(docx_path)
    out_words = _words(d["text"])
    ocr_set = set(ocr_pages)
    image_only = set(analysis["scanned_pages"]) - ocr_set

    pdf_text_parts = []
    with pymupdf.open(pdf_path) as doc:
        for i, page in enumerate(doc, 1):
            if i in analysis["scanned_pages"]:
                continue  # no reliable source text to compare against
            pdf_text_parts.append(page.get_text("text"))
    src_words = _words(" ".join(pdf_text_parts))
    src_total = sum(src_words.values())

    checks: list[dict] = []
    if src_total:
        matched = sum(min(c, out_words.get(w, 0)) for w, c in src_words.items())
        coverage = matched / src_total
        out_total = sum(out_words.values()) or 1
        extra = max(0.0, 1 - matched / out_total) if not analysis["scanned_pages"] else None
        checks.append({"name": "text_coverage", "value": round(coverage * 100, 1), "unit": "%",
                       "status": "pass" if coverage >= 0.97 else "warn" if coverage >= 0.85 else "fail",
                       "detail": "Share of source words (digital pages) found in the Word file."})
        if extra is not None:
            checks.append({"name": "extra_text", "value": round(extra * 100, 1), "unit": "%",
                           "status": "pass" if extra <= 0.05 else "warn",
                           "detail": "Words in the Word file that are not in the PDF."})
    else:
        coverage = None
        checks.append({"name": "text_coverage", "value": None, "unit": "%", "status": "skip",
                       "detail": "No selectable text in the source (scanned/image-only PDF); cannot be verified automatically."})

    src_images, src_tables = analysis["images"], analysis["tables"]
    checks.append({"name": "images", "value": f'{d["images"]} in Word / {src_images} in PDF', "unit": "",
                   "status": "pass" if (src_images == 0 or d["images"] > 0) else "warn",
                   "detail": "Embedded pictures found in each file (counts can differ because of merging/splitting)."})
    checks.append({"name": "tables", "value": f'{d["tables"]} in Word / {src_tables} detected in PDF', "unit": "",
                   "status": "pass" if (src_tables == 0 or d["tables"] > 0) else "warn",
                   "detail": "Table detection is heuristic; borderless tables may not be recognised."})

    pages_out = render_page_count(docx_path)
    if pages_out is not None:
        diff = pages_out - analysis["page_count"]
        checks.append({"name": "page_count", "value": f'{pages_out} (LibreOffice render) / {analysis["page_count"]} (PDF)', "unit": "",
                       "status": "pass" if diff == 0 else "warn",
                       "detail": "Approximate page count when rendered by LibreOffice; Word may differ slightly."})

    if image_only:
        warnings = warnings + [f"Pages {sorted(image_only)} are image-only; their text is not editable."]
    statuses = [c["status"] for c in checks]
    if "fail" in statuses:
        level, message = "low", "Significant content may be missing. Review the document carefully against the PDF."
    elif "warn" in statuses or warnings:
        level, message = "review", "Converted, but some items need manual review (see the notes)."
    else:
        level, message = "good", "Automated checks passed. Still compare with the original before relying on it."
    return {
        "level": level, "message": message, "checks": checks, "warnings": list(dict.fromkeys(warnings)),
        "disclaimer": "Heuristic checks only. No converter guarantees identical formatting in every PDF.",
        "docx": {"paragraphs": d["paragraphs"], "tables": d["tables"], "images": d["images"]},
    }
