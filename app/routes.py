from flask import Blueprint, jsonify

api = Blueprint("api", __name__)

@api.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@api.route("/todos", methods=["GET"])
def get_todos():
    # ตัวอย่างข้อมูลจำลอง
    todos = [
        {"id": 1, "title": "Learn Flask", "done": False},
        {"id": 2, "title": "Setup CI/CD", "done": True}
    ]
    return jsonify(todos), 200
