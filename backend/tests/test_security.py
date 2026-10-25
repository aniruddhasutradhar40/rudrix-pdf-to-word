import pymupdf
import pytest

from app.security import RateLimiter, ValidationError, safe_stem, validate_pdf_bytes

KW = dict(max_pages=5, max_bytes=1024 * 1024)


def test_valid_pdf(text_pdf):
    assert validate_pdf_bytes(text_pdf.read_bytes(), **KW).page_count == 2


@pytest.mark.parametrize("data,code", [(b"", "invalid_file"), (b"hello world not a pdf", "not_pdf"),
                                       (b"%PDF-1.7\ngarbage garbage", "corrupt_pdf")])
def test_rejects_bad_files(data, code):
    with pytest.raises(ValidationError) as e:
        validate_pdf_bytes(data, **KW)
    assert e.value.code == code


def test_rejects_encrypted(encrypted_pdf):
    with pytest.raises(ValidationError) as e:
        validate_pdf_bytes(encrypted_pdf.read_bytes(), **KW)
    assert e.value.code == "encrypted"


def test_rejects_too_many_pages():
    doc = pymupdf.open()
    for _ in range(6):
        doc.new_page()
    with pytest.raises(ValidationError) as e:
        validate_pdf_bytes(doc.tobytes(), **KW)
    assert e.value.code == "too_many_pages"


def test_rejects_too_large(text_pdf):
    with pytest.raises(ValidationError) as e:
        validate_pdf_bytes(text_pdf.read_bytes(), max_pages=5, max_bytes=100)
    assert e.value.status == 413


def test_safe_stem_blocks_traversal():
    assert safe_stem("../../etc/passwd.pdf") == "passwd"
    assert safe_stem('a"b;c<d>.pdf') == "abcd"
    assert safe_stem(None) == "document"
    assert safe_stem("রিপোর্ট ২০২৪.pdf") == "রিপোর্ট ২০২৪"


def test_rate_limiter():
    rl = RateLimiter(2)
    assert rl.allow("a") and rl.allow("a") and not rl.allow("a") and rl.allow("b")
