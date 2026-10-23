import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from backend_python.config import Config
from backend_python.db.database import init_db
from backend_python.routes.auth_routes import auth_bp
from backend_python.routes.prediction_routes import prediction_bp
from backend_python.routes.dashboard_routes import dashboard_bp
from backend_python.services.pytorch_service import get_inference_service
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

frontend_dir = os.path.join(Config.BASE_DIR, 'frontend')

app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Register API blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(prediction_bp)
app.register_blueprint(dashboard_bp)

# Static Uploads Route
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(Config.UPLOAD_DIR, filename)

# Frontend Page Routes
@app.route('/')
def serve_index():
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/<page>.html')
def serve_html_page(page):
    filename = f"{page}.html"
    if os.path.exists(os.path.join(frontend_dir, filename)):
        return send_from_directory(frontend_dir, filename)
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/login')
def serve_login():
    return send_from_directory(frontend_dir, 'login.html')

@app.route('/register')
def serve_register():
    return send_from_directory(frontend_dir, 'register.html')

@app.route('/predict')
def serve_predict():
    return send_from_directory(frontend_dir, 'predict.html')

@app.route('/history')
def serve_history():
    return send_from_directory(frontend_dir, 'history.html')

@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory(frontend_dir, 'dashboard.html')

@app.route('/performance')
def serve_performance():
    return send_from_directory(frontend_dir, 'performance.html')

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(frontend_dir, 'index.html')

if __name__ == '__main__':
    # Initialize MySQL schema
    init_db()
    
    # Pre-warm PyTorch model
    logger.info("Initializing PyTorch ResNet50 Inference Service...")
    get_inference_service()

    port = int(os.environ.get('PORT', 8081))
    logger.info(f"Starting AgriThermal AI Flask Server on http://localhost:{port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
