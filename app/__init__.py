from flask import Flask
from app.config import load_configurations, configure_logging
from .views import webhook_blueprint


def create_app():
    app = Flask(__name__)

    # Load configurations and logging settings
    load_configurations(app)
    configure_logging()
    
    # Register blueprints
    app.register_blueprint(webhook_blueprint)

    # Initialize services when app context is available
    with app.app_context():
        # Initialize MongoDB
        try:
            from .models.database import db_manager
            db_manager.initialize_db()
        except ImportError as e:
            import logging
            logging.warning(f"Database initialization failed: {e}")
        
        # Initialize Korra Chatbot with database
        try:
            from .services.korra_chatbot import korra_bot
            korra_bot.initialize_database()
        except ImportError as e:
            import logging
            logging.warning(f"Chatbot initialization failed: {e}")

    return app
