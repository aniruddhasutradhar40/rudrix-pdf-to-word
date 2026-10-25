# Rudrix PDF to Word Converter

**Rudrix File Solution** – a free, self-hostable PDF → Word (.docx) converter with two modes, OCR for scanned PDFs, and an automatic quality report.

- **Frontend:** static HTML + CSS + JavaScript (deploy on Vercel, GitHub Pages, Netlify…)
- **Backend:** Python FastAPI + PyMuPDF + pdf2docx + python-docx (deploy on a Python/Docker host)
- **No paid APIs.** OCR uses the free, local Tesseract engine.

> ### Honest note about formatting
> PDF stores *drawing instructions*, not a flowing document, so **no converter can guarantee identical
> formatting for every PDF** – this one included. Rudrix does its best, then **measures** the result and
> tells you what it could and could not verify (text coverage, tables, images, page count). Always open
> the .docx and compare it with your PDF before relying on it. Complex brochures, heavy vector art,
> text on curves and unusual fonts are the most likely to differ.

---

## Two modes

| | **Editable Word** | **Maximum Layout Preservation** |
|---|---|---|
| Engine | Own builder on PyMuPDF + python-docx | pdf2docx layout reconstruction |
| Text | Real paragraphs & headings (heading levels guessed from font size) | Blocks that follow the PDF geometry |
| Tables | Real Word tables (read from detected ruling lines) | Real Word tables where detected |
| Images | Inline pictures | Placed close to original position |
| Page size / margins | Follow each PDF page | Follow the PDF |
| Scanned pages | **OCR → editable text** (or image fallback) | Kept as page images (look identical, **not editable**) |
| Best for | Editing, reusing text | Looking as close to the PDF as possible |

Scanned pages are detected automatically (the page is mostly one image and has almost no text).

### OCR (English / Bangla)
OCR runs through PyMuPDF's Tesseract integration. The server reports which languages are **really
installed** at `GET /api/capabilities`; the UI only offers those. If Bangla data (`ben.traineddata`) is
missing, the converter says so in the report and falls back to the installed languages – it never pretends.
The provided Dockerfile installs English **and** Bangla. OCR output is always "best effort": proofread names and numbers.

## What is checked after every conversion
Word-coverage of the source text (digital pages), extra text, image count, table count, and (if LibreOffice
is installed) an approximate rendered page count. The result is labelled **Checks passed / Needs review /
Check carefully**. These are heuristics, not proof.

## Known limitations
- Password-protected PDFs are rejected (remove the password first).
- Editable mode skips full-page background images and cannot reproduce vector charts/diagrams; it warns you.
- Multi-column pages use a simple two-column heuristic; side-by-side blocks may become sequential paragraphs.
- Borderless tables are often not detected as tables.
- Fonts not installed on the reader's computer are substituted by Word.
- Bangla PDFs that use legacy (non-Unicode) fonts may extract as garbled text; that is a property of the PDF.
- In-memory rate limiting and job storage assume a **single backend instance**.

---

## Project layout
```
rudrix-pdf-to-word/
├── backend/              FastAPI app (app/), tests (tests/), Dockerfile, requirements
├── frontend/             Static site (index.html, styles.css, app.js, i18n.js, utils.js), build script, tests
├── scripts/e2e_smoke.py  Optional Playwright browser smoke test
├── .env.example  .gitignore  render.yaml  .github/workflows/ci.yml  LICENSE
```

## Run locally

### 1. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
# OCR (optional but recommended)
#   Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-ben
#   macOS:         brew install tesseract tesseract-lang
#   Windows:       install Tesseract (UB Mannheim build), tick English + Bengali, add it to PATH
uvicorn app.main:app --reload --port 8000
```
Open http://localhost:8000/docs for the API docs and http://localhost:8000/health to check it is up.

> The backend reads **environment variables**; it does not auto-load `.env`. Export them,
> use `set -a; source .env; set +a`, or set them in your host's dashboard. See `.env.example`.

### 2. Frontend
```bash
cd frontend
# the default API URL in config.js is http://localhost:8000
npx serve . -l 3000          # or: python -m http.server 3000
```
Open http://localhost:3000. The status pill (top right) turns green when the backend is reachable.
`http://localhost:3000` is in the default CORS allow-list.

## Configuration (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `RUDRIX_ALLOWED_ORIGINS` | localhost:3000/5500 | Comma-separated CORS origins (your Vercel URL goes here) |
| `RUDRIX_MAX_UPLOAD_MB` | 25 | Upload size limit (enforced while streaming) |
| `RUDRIX_MAX_PAGES` | 100 | Page limit |
| `RUDRIX_OCR_MAX_PAGES` | 30 | Max scanned pages OCR'd per file |
| `RUDRIX_TIMEOUT_SECONDS` | 240 | Hard time limit; the worker process is killed after this |
| `RUDRIX_FILE_TTL_SECONDS` | 900 | Converted files are deleted after this many seconds |
| `RUDRIX_MAX_CONCURRENT` | 2 | Simultaneous conversions |
| `RUDRIX_RATE_LIMIT_PER_MIN` | 10 | Per-IP conversions per minute |
| `RUDRIX_TRUST_PROXY` | false | Use `X-Forwarded-For` for the client IP (only behind a trusted proxy) |
| `RUDRIX_WORK_DIR` | system temp | Temporary storage folder |
| `RUDRIX_QUALITY_RENDER` | true | Use LibreOffice (if installed) for the page-count check |
| `RUDRIX_API_URL` | – | **Frontend build** variable: public backend URL |

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/api/capabilities` | Limits, modes, installed OCR languages |
| POST | `/api/convert` | multipart: `file`, `mode` (`editable`\|`preserve`), `ocr` (`true`\|`false`), `ocr_lang` (`eng`\|`ben`\|`eng+ben`) → JSON with `download_url` and `report` |
| GET | `/api/download/{job_id}` | Download the .docx (until it expires) |
| DELETE | `/api/jobs/{job_id}` | Delete the result immediately |

```bash
curl -F file=@sample.pdf -F mode=editable http://localhost:8000/api/convert
```

## Security & privacy design
Magic-byte + real-parse validation, size cap while streaming, page cap, encrypted-PDF rejection,
random 128-bit job IDs (strictly validated, so no path traversal), original filename never used on disk,
sanitised download filename, uploaded PDF deleted right after processing, results deleted after the TTL
(background janitor + purge at startup), conversion in a separate process with a hard timeout,
concurrency limit, per-IP rate limit, CORS allow-list, `nosniff`/`no-store` headers, non-root Docker user,
and no outbound calls. PDFs are parsed by native libraries (MuPDF); keep dependencies updated and run the
container with resource limits for public deployments.

## Tests
```bash
cd backend  && python -m pytest          # unit + API + real conversions (generates its own PDFs)
cd frontend && npm test                  # pure-JS helper and i18n tests (Node 18+)
```
Some tests skip automatically if Tesseract English data or LibreOffice is not installed.
Optional browser smoke test: start the backend (8000) and a static server (3000), then
`pip install playwright && playwright install chromium && python scripts/e2e_smoke.py sample.pdf`.

---

## Deploy

Frontend and backend are deployed **separately**. The backend cannot run on Vercel Functions: it needs
Tesseract binaries, spawns worker processes, and conversions can exceed serverless size/time limits.

### Step 1 – Push to GitHub
```bash
cd rudrix-pdf-to-word
git init && git add . && git commit -m "Rudrix PDF to Word"
git branch -M main
git remote add origin https://github.com/<your-user>/rudrix-pdf-to-word.git
git push -u origin main
```
The included GitHub Actions workflow runs the backend and frontend tests on every push.

### Step 2 – Deploy the Python backend (Docker host)
Any host that runs Docker works (Render, Railway, Fly.io, a VPS). Example with **Render**:
1. *New → Web Service* → connect your GitHub repo.
2. **Root Directory:** `backend` · **Runtime:** Docker (uses `backend/Dockerfile`, which installs Tesseract English + Bangla).
   Or use the included `render.yaml` as a Blueprint.
3. Environment variables: `RUDRIX_ALLOWED_ORIGINS=https://<your-app>.vercel.app`, `RUDRIX_TRUST_PROXY=true`
   (add others from the table if you want different limits).
4. Health check path: `/health`. Deploy and note the URL, e.g. `https://rudrix-api.onrender.com`.
5. Verify: open `<backend-url>/api/capabilities` – `ocr.languages` shows what is really installed.

Notes: free tiers have small RAM and sleep when idle (the first request is slow); large or scanned PDFs need
more memory. Lower `RUDRIX_MAX_PAGES` / `RUDRIX_MAX_UPLOAD_MB` if you see out-of-memory restarts. To enable the
LibreOffice page-count check, build with `--build-arg INSTALL_LIBREOFFICE=true` (bigger image).
Without Docker: install `tesseract-ocr tesseract-ocr-ben` on the server, `pip install -r requirements.txt`, and run
`uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

### Step 3 – Deploy the frontend on Vercel
1. *Add New → Project* → import the same GitHub repo.
2. **Root Directory:** `frontend`. Vercel reads `frontend/vercel.json` (build `npm run build`, output `dist`).
3. **Environment Variable:** `RUDRIX_API_URL` = your backend URL (https, no trailing slash).
4. Deploy. The build script writes `dist/config.js` with that URL.
5. Copy the Vercel URL into the backend's `RUDRIX_ALLOWED_ORIGINS` and redeploy the backend
   (CORS must list the exact origin; add your custom domain too if you use one).

Static-only alternative: edit `frontend/config.js` (`API_BASE_URL`) and host the folder anywhere.

## Troubleshooting
- **"Server offline" / network error** – wrong `RUDRIX_API_URL`, backend asleep, or the frontend origin is missing from `RUDRIX_ALLOWED_ORIGINS`.
- **"OCR is not installed"** – install Tesseract (see above) or use the provided Dockerfile.
- **Bangla OCR missing** – install `tesseract-ocr-ben` (`ben.traineddata`).
- **Mixed content error** – an https frontend cannot call an http backend; use an https backend URL.

## Credits & licences
[PyMuPDF](https://pymupdf.readthedocs.io) (AGPL-3.0 / commercial), [pdf2docx](https://github.com/ArtifexSoftware/pdf2docx) (GPL-3.0),
[python-docx](https://github.com/python-openxml/python-docx) (MIT), [FastAPI](https://fastapi.tiangolo.com) (MIT), [Tesseract](https://github.com/tesseract-ocr/tesseract) (Apache-2.0).

**Licence note:** PyMuPDF (AGPL) and pdf2docx (GPL) are copyleft. If you run this as a public network service, the
AGPL may require you to offer the corresponding source to its users; for closed-source or commercial use, review
those licences (Artifex sells a commercial PyMuPDF licence). The Rudrix code in this repo is MIT; that does not
change the licences of its dependencies. This is not legal advice.
