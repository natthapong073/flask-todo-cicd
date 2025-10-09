# ---------------------------
# Build stage
# ---------------------------
# ใช้ as builder เพื่อตั้งชื่อ stage นี้ สำหรับอ้างอิงใน stage ถัดไป
FROM python:3.11-slim as builder

# กำหนด working directory ภายใน container
WORKDIR /app

# ติดตั้ง build-time dependencies ที่จำเป็นสำหรับการ compile บาง package (เช่น psycopg2)
# --no-install-recommends ช่วยลดขนาด image
# rm -rf /var/lib/apt/lists/* เพื่อลบ cache ของ apt-get หลังติดตั้งเสร็จ
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# สร้าง virtual environment เพื่อแยก dependencies ออกจาก system python
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# คัดลอกแค่ไฟล์ requirements.txt เข้ามาก่อน เพื่อใช้ประโยชน์จาก Docker layer caching
# ถ้าไฟล์นี้ไม่เปลี่ยน Docker จะไม่รันคำสั่ง RUN pip install ใหม่
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ---------------------------
# Runtime stage
# ---------------------------
# เริ่ม stage ใหม่จาก base image ที่เล็กและปลอดภัย
FROM python:3.11-slim

# สร้าง user ที่ไม่มีสิทธิ์ root เพื่อรันแอป (Security Best Practice)
RUN useradd --create-home --shell /bin/bash -u 1000 appuser

WORKDIR /app

# ติดตั้งเฉพาะ run-time dependencies ที่จำเป็นจริงๆ
# curl จำเป็นสำหรับ HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# คัดลอก virtual environment ที่มี packages ติดตั้งครบแล้วจาก builder stage
COPY --from=builder /opt/venv /opt/venv

# คัดลอก source code ของแอปพลิเคชัน และเปลี่ยนเจ้าของเป็น appuser
# แนะนำ: ให้สร้างไฟล์ .dockerignore เพื่อไม่ให้ copy ไฟล์ที่ไม่จำเป็นเข้ามา
COPY --chown=appuser:appuser . .

# กำหนด Environment variables
# ทำให้ Python packages ที่ติดตั้งใน venv ถูกเรียกใช้งานได้
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# สลับไปใช้ user ที่ไม่มีสิทธิ์ root
USER appuser

# บอก Docker ว่า container จะ listen ที่ port ไหนตอน runtime
EXPOSE 5000

# Healthcheck เพื่อให้ Docker ตรวจสอบว่าแอปยังทำงานปกติ
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# คำสั่งสำหรับรันแอปพลิเคชัน
# ใช้ shell form (ไม่มีวงเล็บ []) เพื่อให้ shell ขยายค่าตัวแปร $PORT ได้
# ${PORT:-5000} หมายความว่า: ถ้ามีตัวแปร PORT ให้ใช้ค่านั้น, ถ้าไม่มีให้ใช้ 5000 เป็น default
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 4 --timeout 120 run:app