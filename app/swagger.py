from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = '/docs'  # URL ที่ใช้เปิด Swagger UI
API_URL = '/static/swagger.json'  # ไฟล์ swagger.json ที่จะอ้างอิง API schema

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Flask Todo API"
    }
)
