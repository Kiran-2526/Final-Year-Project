from flask import Blueprint, request, jsonify
from backend_python.services.auth_service import register_user, login_user

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    try:
        res = register_user(name, email, password)
        return jsonify(res), 201
    except ValueError as ve:
        return jsonify({
            "status": 400,
            "error": "Validation Failed" if "format" in str(ve).lower() or "character" in str(ve).lower() else "Bad Request",
            "message": str(ve)
        }), 400
    except Exception as e:
        return jsonify({
            "status": 500,
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')

    try:
        res = login_user(email, password)
        return jsonify(res), 200
    except ValueError as ve:
        return jsonify({
            "status": 400,
            "error": "Bad Request",
            "message": str(ve)
        }), 400
    except Exception as e:
        return jsonify({
            "status": 500,
            "error": "Internal Server Error",
            "message": str(e)
        }), 500
