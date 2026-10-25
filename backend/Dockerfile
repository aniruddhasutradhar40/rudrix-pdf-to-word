FROM python:3.12-slim

# Tesseract + English and Bangla language data (free OCR). Set INSTALL_LIBREOFFICE=true
# to also enable the optional page-count check (adds roughly 400 MB to the image).
ARG INSTALL_LIBREOFFICE=false
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-eng tesseract-ocr-ben libglib2.0-0 \
    && if [ "$INSTALL_LIBREOFFICE" = "true" ]; then apt-get install -y --no-install-recommends libreoffice-writer; fi \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 RUDRIX_WORK_DIR=/tmp/rudrix_jobs
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN useradd -m rudrix && mkdir -p /tmp/rudrix_jobs && chown rudrix /tmp/rudrix_jobs
USER rudrix
EXPOSE 8000
# One worker on purpose: conversions already run in isolated child processes.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
