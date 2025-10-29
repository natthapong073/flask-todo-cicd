from app import create_app
import os

# ✅ เรียกใช้ Flask application
app = create_app()

if __name__ == "__main__":
    # ✅ ดึงพอร์ตจาก environment variable ที่ Railway กำหนดให้
    port = int(os.environ.get("PORT", 5000))
    # ✅ ให้ Flask ฟังที่ทุก IP (จำเป็นสำหรับ Railway)
    app.run(host="0.0.0.0", port=port)
