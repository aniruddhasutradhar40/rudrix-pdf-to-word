import io
import os
import sys
from pathlib import Path

import pymupdf
import pytest
from PIL import Image, ImageDraw

os.environ.setdefault("RUDRIX_QUALITY_RENDER", "false")  # LibreOffice render has its own test
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _png(color=(30, 90, 200)) -> bytes:
    im = Image.new("RGB", (240, 140), color)
    ImageDraw.Draw(im).rectangle((20, 20, 220, 120), outline=(255, 255, 255), width=6)
    buf = io.BytesIO(); im.save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture(scope="session")
def text_pdf(tmp_path_factory) -> Path:
    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_text((72, 90), "Quarterly Report", fontsize=26, fontname="hebo")
    p.insert_textbox(pymupdf.Rect(72, 110, 520, 220),
                     "Rudrix converts documents into editable files. This paragraph checks that ordinary "
                     "body text keeps its words, spacing and order after conversion to Word format.",
                     fontsize=11, fontname="helv")
    p.insert_text((90, 250), "\u2022 First bullet point", fontsize=11, fontname="helv")
    p.insert_text((90, 268), "\u2022 Second bullet point", fontsize=11, fontname="helv")
    p2 = doc.new_page()
    p2.insert_text((72, 90), "Second page heading", fontsize=18, fontname="hebo")
    p2.insert_text((72, 130), "Final page body text with numbers 12345 and 67.89.", fontsize=11, fontname="helv")
    path = tmp_path_factory.mktemp("pdf") / "text.pdf"
    doc.save(path); return path


@pytest.fixture(scope="session")
def table_image_pdf(tmp_path_factory) -> Path:
    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_text((72, 80), "Sales Table", fontsize=20, fontname="hebo")
    x0, y0, cw, rh = 72, 110, 120, 28
    data = [["Item", "Qty", "Price"], ["Apple", "10", "1.50"], ["Banana", "24", "0.75"], ["Cherry", "5", "4.20"]]
    sh = p.new_shape()
    for r in range(len(data) + 1):
        sh.draw_line((x0, y0 + r * rh), (x0 + 3 * cw, y0 + r * rh))
    for c in range(4):
        sh.draw_line((x0 + c * cw, y0), (x0 + c * cw, y0 + len(data) * rh))
    sh.finish(width=1, color=(0, 0, 0)); sh.commit()
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            p.insert_text((x0 + c * cw + 8, y0 + r * rh + 19), val, fontsize=11, fontname="helv")
    p.insert_image(pymupdf.Rect(72, 300, 312, 440), stream=_png())
    p.insert_text((72, 470), "Figure 1: sample picture", fontsize=10, fontname="helv")
    path = tmp_path_factory.mktemp("pdf") / "table_image.pdf"
    doc.save(path); return path


@pytest.fixture(scope="session")
def scanned_pdf(tmp_path_factory) -> Path:
    src = pymupdf.open(); p = src.new_page()
    p.insert_text((72, 120), "INVOICE 2024 Payment Received", fontsize=28, fontname="helv")
    p.insert_text((72, 180), "Thank you for your business", fontsize=22, fontname="helv")
    png = p.get_pixmap(dpi=200).tobytes("png")
    doc = pymupdf.open(); q = doc.new_page()
    q.insert_image(q.rect, stream=png)  # image only: no selectable text
    path = tmp_path_factory.mktemp("pdf") / "scanned.pdf"
    doc.save(path); return path


@pytest.fixture(scope="session")
def encrypted_pdf(tmp_path_factory) -> Path:
    doc = pymupdf.open(); doc.new_page().insert_text((72, 90), "secret")
    path = tmp_path_factory.mktemp("pdf") / "enc.pdf"
    doc.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="pw", owner_pw="pw"); return path
