FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends poppler-utils tesseract-ocr tesseract-ocr-eng tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-container.txt .
RUN python -m pip install --no-cache-dir -r requirements-container.txt

RUN addgroup --system --gid 10001 anamnes \
    && adduser --system --uid 10001 --ingroup anamnes --no-create-home anamnes \
    && install -d -o anamnes -g anamnes /data/media

COPY manage.py .
COPY anamnes ./anamnes
COPY accounts ./accounts
COPY allergies ./allergies
COPY archive ./archive
COPY medications ./medications

USER anamnes
EXPOSE 8000
CMD ["gunicorn", "anamnes.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "60"]
