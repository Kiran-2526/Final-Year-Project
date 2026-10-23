from flask import Blueprint, request, jsonify
from backend_python.services.prediction_service import (
    predict_and_save_batch,
    get_user_predictions,
    get_prediction_by_id,
    clear_user_predictions
)

prediction_bp = Blueprint('prediction_bp', __name__, url_prefix='/api/predictions')

@prediction_bp.route('', methods=['GET', 'POST', 'DELETE'], strict_slashes=False)
@prediction_bp.route('/', methods=['GET', 'POST', 'DELETE'], strict_slashes=False)
def handle_predictions_root():
    if request.method == 'POST':
        return create_prediction()
    elif request.method == 'DELETE':
        return clear_predictions()
    else:
        return get_predictions()

def create_prediction():
    files = []
    if 'files' in request.files:
        files.extend(request.files.getlist('files'))
    if 'file' in request.files:
        files.extend(request.files.getlist('file'))
    if 'files[]' in request.files:
        files.extend(request.files.getlist('files[]'))

    if not files:
        for k in request.files:
            if k not in ('files', 'file', 'files[]'):
                files.extend(request.files.getlist(k))

    # Filter out empty filename entries
    files = [f for f in files if f and f.filename != '']

    if not files:
        return jsonify({
            "status": 500,
            "error": "Internal Server Error",
            "message": "Required part 'files' or 'file' is not present."
        }), 500

    user_id = request.form.get('userId', 1)

    try:
        res = predict_and_save_batch(files, int(user_id))
        
        # Backward compatibility for single file requests under key 'file'
        if len(files) == 1 and 'files' not in request.files and len(res.get('results', [])) == 1:
            single_res = res['results'][0]
            if not single_res.get('error'):
                return jsonify(single_res), 201

        return jsonify(res), 201
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

def get_predictions():
    user_id = request.args.get('userId', 1)
    try:
        res = get_user_predictions(int(user_id))
        return jsonify(res), 200
    except Exception as e:
        return jsonify({
            "status": 500,
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

def clear_predictions():
    user_id = request.args.get('userId', 1)
    try:
        res = clear_user_predictions(int(user_id))
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

@prediction_bp.route('/<int:pred_id>', methods=['GET'])
def get_prediction(pred_id):
    user_id = request.args.get('userId', 1)
    try:
        res = get_prediction_by_id(pred_id, int(user_id))
        return jsonify(res), 200
    except ValueError as ve:
        status_code = 404 if "not found" in str(ve).lower() else 400
        error_type = "Not Found" if status_code == 404 else "Bad Request"
        return jsonify({
            "status": status_code,
            "error": error_type,
            "message": str(ve)
        }), status_code
    except Exception as e:
        return jsonify({
            "status": 500,
            "error": "Internal Server Error",
            "message": str(e)
        }), 500
