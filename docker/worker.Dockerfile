FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies including LibreOffice and Java (Headless)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-java-common \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Force LibreOffice to use CPU-only rendering (no X11/GPU)
ENV SAL_USE_VCLPLUGIN=gen
ENV JAVA_TOOL_OPTIONS="-Djava.awt.headless=true"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run Celery worker
CMD ["celery", "-A", "backend.app.worker.celery_app", "worker", "--loglevel=info"]
