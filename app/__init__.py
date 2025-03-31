import logging
from flask import Flask
from app.models import db
from app.config import Config


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from app.routes.meetings import meetings_bp
    app.register_blueprint(meetings_bp)
    
    # Register test utils blueprint in development mode
    if app.config['DEBUG']:
        from app.routes.test_utils import test_utils_bp
        app.register_blueprint(test_utils_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return {"status": "ok", "service": "Fireflies Transcription Service"}, 200
    
    logging.getLogger(__name__).info('Fireflies Transcription Service started')
    return app
