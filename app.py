"""
app.py - Academic Plagiarism Detector
Flask Backend with Document Upload Support

Run: python app.py
API: http://localhost:5000/api/
"""
import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run()
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
    
    # Create upload dir
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Enable CORS for all origins (customize for production)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Rate limiting (optional, requires flask-limiter)
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per hour", "50 per minute"],
            storage_uri="memory://"
        )
        
        logger.info("Rate limiting enabled")
    except ImportError:
        logger.warning("flask-limiter not installed. Rate limiting disabled.")
    
    # Register API blueprint
    from api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Serve frontend
    @app.route('/')
    def index():
        return send_from_directory('static', 'index.html')
    
    @app.route('/<path:path>')
    def static_files(path):
        return send_from_directory('static', path)
    
    # Error handlers
    @app.errorhandler(413)
    def too_large(e):
        from flask import jsonify
        return jsonify({"error": "File too large. Maximum size is 10MB.", "status": "error"}), 413
    
    @app.errorhandler(404)
    def not_found(e):
        from flask import jsonify
        return jsonify({"error": "Endpoint not found", "status": "error"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        from flask import jsonify
        return jsonify({"error": "Internal server error", "status": "error"}), 500
    
    logger.info("Academic Plagiarism Detector initialized")
    logger.info("Endpoints:")
    logger.info("  GET  /api/health")
    logger.info("  POST /api/analyze          (JSON: {text: '...'})")
    logger.info("  POST /api/analyze-document (form-data: file=<doc>)")
    logger.info("  POST /api/batch-analyze    (form-data: files=<doc1>,<doc2>)")
    
    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'true').lower() == 'true'
    
    print("\n" + "="*60)
    print("  Academic Plagiarism Detector API")
    print("="*60)
    print(f"  Running on: http://localhost:{port}")
    print(f"  Frontend:   http://localhost:{port}/")
    print(f"  API Docs:   http://localhost:{port}/api/health")
    print("="*60)
    print("\n  Quick Test (Postman):")
    print(f"  POST http://localhost:{port}/api/analyze-document")
    print("  Body: form-data → file: <your_pdf>")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)