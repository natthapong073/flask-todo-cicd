# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.10

RUN useradd -m -u 1000 appuser

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py

USER appuser

# ✅ แก้ตรงนี้: ใช้ Render PORT (ไม่ fix 5000)
EXPOSE 5000

# ✅ แก้ Healthcheck ให้ใช้ $PORT
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests, os; requests.get(f'http://localhost:{os.environ.get(\"PORT\",5000)}/api/health')" || exit 1

# ✅ แก้ตรงนี้! ใช้ dynamic port จาก Render
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT:-5000}", "--workers", "4", "--timeout", "120", "run:app"]
