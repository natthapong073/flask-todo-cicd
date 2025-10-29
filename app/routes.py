from flask import Blueprint, request, jsonify
from app.models import db, Todo
from sqlalchemy.exc import SQLAlchemyError

api = Blueprint("api", __name__)

@api.route("/health", methods=["GET"])
def health_check():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": "Database connection failed"
        }), 503

@api.route("/todos", methods=["GET"])
def get_todos():
    try:
        todos = Todo.query.order_by(Todo.id.desc()).all()
        return jsonify({
            "success": True,
            "data": [todo.to_dict() for todo in todos],
            "count": len(todos)
        }), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Database error occurred"}), 500

@api.route("/todos/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if not todo:
        return jsonify({"success": False, "error": "Todo not found"}), 404
    return jsonify({"success": True, "data": todo.to_dict()}), 200

@api.route("/todos", methods=["POST"])
def create_todo():
    data = request.get_json() or {}
    if not data.get("title"):
        return jsonify({"success": False, "error": "Title is required"}), 400

    try:
        todo = Todo(title=data["title"], description=data.get("description", ""))
        db.session.add(todo)
        db.session.commit()
        return jsonify({
            "success": True,
            "data": todo.to_dict(),
            "message": "Todo created successfully"
        }), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to create todo"}), 500

@api.route("/todos/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json() or {}

    try:
        todo = Todo.query.get(todo_id)

        # ถ้า query คืน None → ถือว่า session เสียหรือ todo ไม่พบ
        if not todo:
            raise SQLAlchemyError("Todo not found or session broken")

        if "title" in data:
            todo.title = data["title"]
        if "description" in data:
            todo.description = data["description"]
        if "completed" in data:
            todo.completed = data["completed"]

        db.session.commit()

        return jsonify({
            "success": True,
            "data": todo.to_dict(),
            "message": "Todo updated successfully"
        }), 200

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Database error"}), 500

@api.route("/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if not todo:
        return jsonify({"success": False, "error": "Todo not found"}), 404

    try:
        db.session.delete(todo)
        db.session.commit()
        return jsonify({"success": True, "message": "Todo deleted successfully"}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to delete todo"}), 500