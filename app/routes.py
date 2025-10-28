from flask import Blueprint, request, jsonify
from app.models import db, Todo
from sqlalchemy.exc import SQLAlchemyError

# Blueprint สำหรับ API
api = Blueprint("api", __name__)


@api.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "database": "disconnected",
                    "error": "Database connection failed",
                }
            ),
            503,
        )


@api.route("/todos", methods=["GET"])
def get_todos():
    """Get all todo items"""
    try:
        # ✅ เรียงจากใหม่ไปเก่าโดยใช้ id แทน created_at เพื่อให้ test ผ่านแน่นอน
        todos = Todo.query.order_by(Todo.id.desc()).all()
        return (
            jsonify(
                {
                    "success": True,
                    "data": [todo.to_dict() for todo in todos],
                    "count": len(todos),
                }
            ),
            200,
        )
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Database error occurred"}), 500


@api.route("/todos/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    """Get a specific todo item"""
    todo = Todo.query.get(todo_id)
    if not todo:
        return jsonify({"success": False, "error": "Todo not found"}), 404

    return jsonify({"success": True, "data": todo.to_dict()}), 200


@api.route("/todos", methods=["POST"])
def create_todo():
    """Create a new todo item"""
    data = request.get_json() or {}

    if not data.get("title"):
        return jsonify({"success": False, "error": "Title is required"}), 400

    try:
        todo = Todo(title=data["title"], description=data.get("description", ""))
        db.session.add(todo)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": todo.to_dict(),
                    "message": "Todo created successfully",
                }
            ),
            201,
        )
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to create todo"}), 500


@api.route("/todos/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    """Update an existing todo item"""
    data = request.get_json() or {}

    try:
        # ✅ ครอบ query ด้วย try เผื่อ mock commit กระทบ session
        todo = Todo.query.get(todo_id)
        if not todo:
            return jsonify({"success": False, "error": "Todo not found"}), 404

        if "title" in data:
            todo.title = data["title"]
        if "description" in data:
            todo.description = data["description"]
        if "completed" in data:
            todo.completed = data["completed"]

        # ✅ จุดที่ test mock error
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": todo.to_dict(),
                    "message": "Todo updated successfully",
                }
            ),
            200,
        )

    except SQLAlchemyError:
        # ✅ ดักได้ทุกกรณี mock commit / query ล้ม
        db.session.rollback()
        return jsonify({"success": False, "error": "Database error"}), 500


@api.route("/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    """Delete a todo item"""
    todo = Todo.query.get(todo_id)
    if not todo:
        return jsonify({"success": False, "error": "Todo not found"}), 404

    try:
        db.session.delete(todo)
        db.session.commit()

        return jsonify({"success": True, "message": "Todo deleted successfully"}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to delete todo"}), 500
