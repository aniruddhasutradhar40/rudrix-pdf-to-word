"""PDF analysis with PyMuPDF: detects scanned pages, images, tables and vector graphics."""
from __future__ import annotations

import pymupdf

SCANNED_TEXT_THRESHOLD = 20  # characters; below this a page with images is treated as scanned


def analyze_pdf(pdf_path: str) -> dict:
    doc = pymupdf.open(pdf_path)
    try:
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            infos = [im for im in page.get_image_info(xrefs=True) if im.get("xref", 0) > 0 or im.get("bbox")]
            area = page.rect.width * page.rect.height or 1
            covered = 0.0
            for im in infos:
                r = pymupdf.Rect(im["bbox"]) & page.rect
                covered = max(covered, (r.width * r.height) / area)
            try:
                tables = len(page.find_tables().tables)
            except Exception:
                tables = 0
            try:
                drawings = len(page.get_drawings())
            except Exception:
                drawings = 0
            scanned = len(text) < SCANNED_TEXT_THRESHOLD and bool(infos) and covered > 0.5
            pages.append({
                "index": i,
                "text_chars": len(text),
                "images": len(infos),
                "image_coverage": round(covered, 2),
                "tables": tables,
                "drawings": drawings,
                "scanned": scanned,
                "blank": len(text) < SCANNED_TEXT_THRESHOLD and not infos and drawings == 0,
            })
        return {
            "page_count": len(pages),
            "scanned_pages": [p["index"] + 1 for p in pages if p["scanned"]],
            "pages": pages,
            "tables": sum(p["tables"] for p in pages),
            "images": sum(p["images"] for p in pages),
        }
    finally:
        doc.close()
