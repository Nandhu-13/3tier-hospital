from flask import Flask
from flask_cors import CORS
from .database import init_db
from .routes.patients import patients_bp
from .routes.doctors import doctors_bp
from .routes.appointments import appointments_bp
from .routes.departments import departments_bp
from .routes.stats import stats_bp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Register blueprints
    app.register_blueprint(patients_bp,     url_prefix='/api/patients')
    app.register_blueprint(doctors_bp,      url_prefix='/api/doctors')
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    app.register_blueprint(departments_bp,  url_prefix='/api/departments')
    app.register_blueprint(stats_bp,        url_prefix='/api')

    # Health endpoints
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'hospital-backend-flask'}, 200

    @app.route('/api/health')
    def api_health():
        return {'status': 'healthy', 'service': 'hospital-backend-flask', 'version': '1.0.0'}, 200

    # Initialize DB tables + seed data
    with app.app_context():
        try:
            init_db()
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ DB init error: {e}")

    return app
