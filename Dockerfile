# ---------------------------
# Build stage
# ---------------------------
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# ---------------------------
# Runtime stage
# ---------------------------
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies and source code
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py

# Use non-root user
USER appuser

# Expose port
EXPOSE 5000

# Healthcheck (แค่ตรวจว่ายังตอบอยู่ ไม่ต้องรัน gunicorn)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# ✅ Run with gunicorn (แบบที่ Render ใช้ได้แน่นอน)
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "4", "--timeout", "120", "run:app"]
