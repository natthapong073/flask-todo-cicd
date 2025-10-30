from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from app.models import Todo, db

api = Blueprint("api", __name__)

# ✅ Root route — สำหรับ Render / Railway health check
@api.route('/')
def home():
    return jsonify({
        "message": "Flask Todo API is live",
        "status": "ok",
        "endpoints": ["/api/health", "/api/todos"]
    }), 200


# ✅ Health check รองรับทั้ง /health และ /api/health
@api.route('/health', methods=['GET'])
@api.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    from sqlalchemy.exc import OperationalError
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    except OperationalError:
        return jsonify({
            'status': 'unhealthy',
            'database': 'initializing'
        }), 503
    except Exception:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected'
        }), 503


@api.route("/todos", methods=["GET"])
def get_todos():
    """Get all todo items"""
    try:
        todos = Todo.query.order_by(Todo.created_at.desc()).all()
        return jsonify({
            "success": True,
            "data": [todo.to_dict() for todo in todos],
            "count": len(todos),
        }), 200
    except SQLAlchemyError:
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
    data = request.get_json()
    if not data or not data.get("title"):
        return jsonify({"success": False, "error": "Title is required"}), 400

    try:
        todo = Todo(title=data["title"], description=data.get("description", ""))
        db.session.add(todo)
        db.session.commit()
        return jsonify({
            "success": True,
            "data": todo.to_dict(),
            "message": "Todo created successfully",
        }), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to create todo"}), 500


@api.route("/todos/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    """Update an existing todo item"""
    todo = Todo.query.get(todo_id)
    if not todo:
        return jsonify({"success": False, "error": "Todo not found"}), 404

    data = request.get_json()
    try:
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
            "message": "Todo updated successfully",
        }), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to update todo"}), 500


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
