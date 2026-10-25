"""Optional browser smoke test (needs `pip install playwright && playwright install chromium`).

Starts nothing itself: run the backend on :8000 and a static server for ./frontend on :3000 first.
Usage: python scripts/e2e_smoke.py path/to/sample.pdf
"""
import sys, zipfile, io
from playwright.sync_api import sync_playwright

pdf = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, vp in (("desktop", {"width": 1280, "height": 900}), ("mobile", {"width": 390, "height": 800})):
        page = b.new_page(viewport=vp, accept_downloads=True)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto("http://localhost:3000/")
        page.wait_for_selector("#serverPill.pill-ok", timeout=10000)
        page.set_input_files("#fileInput", pdf)
        page.check('input[value="preserve"]' if name == "mobile" else 'input[value="editable"]')
        page.click("#convertBtn")
        page.wait_for_selector("#result:not([hidden])", timeout=120000)
        with page.expect_download() as dl:
            page.click("#downloadBtn")
        data = open(dl.value.path(), "rb").read()
        assert zipfile.ZipFile(io.BytesIO(data)).testzip() is None, "docx is not a valid zip"
        print(name, "download ok:", dl.value.suggested_filename, len(data), "bytes; badge:", page.inner_text("#levelBadge"))
        page.screenshot(path=f"/tmp/e2e_{name}.png", full_page=False)
        assert not errors, errors
    b.close()
print("E2E OK")
