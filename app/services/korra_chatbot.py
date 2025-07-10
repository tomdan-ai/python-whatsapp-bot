"""
Korra Chatbot Service (Legacy File)

This file provides backward compatibility with the modularized version.
It imports and exposes the new modular KorraChatbot from the chatbot package.

For new code, please import directly from:
from app.services.chatbot import KorraChatbot
"""

import logging
from .chatbot import KorraChatbot

# Create the bot instance for backward compatibility with existing code
korra_bot = KorraChatbot()

# Export backward compatibility
__all__ = ['korra_bot']

logging.info("Loaded Korra Chatbot (legacy module) with modular implementation")