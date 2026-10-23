from flask import Blueprint, request, jsonify
from backend_python.services.prediction_service import get_dashboard_stats

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
def get_stats():
    user_id = request.args.get('userId', 1)
    try:
        res = get_dashboard_stats(int(user_id))
        return jsonify(res), 200
    except Exception as e:
        return jsonify({
            "status": 500,
            "error": "Internal Server Error",
            "message": str(e)
        }), 500
