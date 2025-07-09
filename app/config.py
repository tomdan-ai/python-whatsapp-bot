import sys
import os
from dotenv import load_dotenv
import logging


def load_configurations(app):
    load_dotenv()
    
    # WhatsApp Configuration
    app.config["ACCESS_TOKEN"] = os.getenv("ACCESS_TOKEN")
    app.config["YOUR_PHONE_NUMBER"] = os.getenv("YOUR_PHONE_NUMBER")
    app.config["APP_ID"] = os.getenv("APP_ID")
    app.config["APP_SECRET"] = os.getenv("APP_SECRET")
    app.config["RECIPIENT_WAID"] = os.getenv("RECIPIENT_WAID")
    app.config["VERSION"] = os.getenv("VERSION")
    app.config["PHONE_NUMBER_ID"] = os.getenv("PHONE_NUMBER_ID")
    app.config["VERIFY_TOKEN"] = os.getenv("VERIFY_TOKEN")
    
    # AI Configuration (Priority: OpenRouter -> DeepSeek -> OpenAI)
    app.config["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
    app.config["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY")
    app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    app.config["OPENAI_ASSISTANT_ID"] = os.getenv("OPENAI_ASSISTANT_ID")
    
    # MongoDB Configuration
    app.config["MONGODB_URI"] = os.getenv("MONGODB_URI")
    app.config["MONGODB_DATABASE"] = os.getenv("MONGODB_DATABASE", "korra_bot")
    
    # Legacy Database Configuration (backup)
    app.config["DATABASE_URL"] = os.getenv("DATABASE_URL", "sqlite:///korra_bot.db")
    
    # Flask Configuration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "korra_chatbot_secret_key_2025")
    app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", "development")


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
