"""
Modular Korra Chatbot Package

This package contains the modularized components of the Korra business intelligence chatbot.
Each module handles a specific aspect of the chatbot functionality for better maintainability.

Components:
- KorraChatbot: Main orchestrator that coordinates all functionality
- SessionManager: Handles user sessions and conversation history
- IntentDetector: Classifies user messages into business intents
- ResponseGenerator: Generates AI or template-based responses
- Handlers: Specialized handlers for different business domains

The modular design allows for:
- Better separation of concerns
- Easier testing and maintenance
- Flexible service integration
- Scalable architecture
"""

from .chatbot_orchestrator import KorraChatbot
from .session_manager import SessionManager
from .intent_detector import IntentDetector
from .response_generator import ResponseGenerator

__all__ = [
    'KorraChatbot',
    'SessionManager', 
    'IntentDetector',
    'ResponseGenerator'
]

# For backward compatibility, maintain the original interface
korra_chatbot = KorraChatbot()