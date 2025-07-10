"""
Korra Chatbot Orchestrator

Main coordinator that delegates responsibilities to specialized modules
for a clean, maintainable chatbot architecture.
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from .session_manager import SessionManager
from .intent_detector import IntentDetector
from .response_generator import ResponseGenerator


class KorraChatbot:
    """
    Main Korra Chatbot orchestrator that coordinates all chatbot functionality
    through specialized modules for better maintainability and testing.
    """
    
    def __init__(self):
        # Initialize database connection
        self.db_manager = None
        self.db_enabled = False
        self._initialize_database()
        
        # Initialize core modules
        self.session_manager = SessionManager(self.db_manager)
        self.intent_detector = IntentDetector()
        self.response_generator = ResponseGenerator()
        
        # Initialize specialized handlers
        self._initialize_handlers()
        
        logging.info("KorraChatbot orchestrator initialized successfully")
    
    def _initialize_database(self):
        """Initialize database connection"""
        try:
            from ...models.database import db_manager
            self.db_manager = db_manager
            logging.info("Database manager loaded successfully")
        except ImportError as e:
            logging.warning(f"Could not import database manager: {e}")
            self.db_manager = None
    
    def _initialize_handlers(self):
        """Initialize specialized business handlers with better error handling"""
        self.handlers = {}
        
        # Sales forecasting handler
        try:
            try:
                from .handlers.sales_forecast_handler import SalesForecastHandler
                self.handlers['sales_forecast'] = SalesForecastHandler(self.db_manager)
            except ImportError as e:
                # Fall back to default handler if module not found
                from .handlers.base_handler import BaseHandler
                
                class FallbackForecastHandler(BaseHandler):
                    def handle(self, user_id, message, user_context):
                        return ("📊 *Sales Forecasting*\n\nForecasting is currently unavailable. "
                                "Please try again later or contact support.", ["🔙 Main Menu"])
                
                self.handlers['sales_forecast'] = FallbackForecastHandler()
                logging.warning(f"Using fallback forecast handler: {e}")
        
            # Share with related intents
            self.handlers['forecast_comparison'] = self.handlers['sales_forecast'] 
            self.handlers['scenario_analysis'] = self.handlers['sales_forecast']
        except Exception as e:
            logging.error(f"Could not initialize forecast handler: {e}")
        
        # Anomaly detection handler
        try:
            from .handlers.anomaly_handler import AnomalyHandler
            self.handlers['anomaly_detection'] = AnomalyHandler(self.db_manager)
        except ImportError as e:
            logging.warning(f"Anomaly handler not available: {e}")
        
        # Invoice handler
        try:
            from .handlers.invoice_handler import InvoiceHandler
            self.handlers['invoice_generation'] = InvoiceHandler(self.db_manager)
        except ImportError as e:
            logging.warning(f"Invoice handler not available: {e}")
        
        # Sales data handler
        try:
            from .handlers.sales_data_handler import SalesDataHandler
            self.handlers['sales_input'] = SalesDataHandler(self.db_manager)
        except ImportError as e:
            logging.warning(f"Sales data handler not available: {e}")
        
        # File upload handler
        try:
            from .handlers.file_handler import FileHandler
            self.handlers['file_upload'] = FileHandler(self.db_manager)
        except ImportError as e:
            logging.warning(f"File handler not available: {e}")
    
    def initialize_database(self):
        """Initialize database connection when Flask app context is available"""
        if self.db_manager:
            self.db_enabled = self.db_manager.initialize_db()
            self.session_manager.initialize_database()
            if self.db_enabled:
                logging.info("MongoDB database initialized successfully")
            else:
                logging.warning("MongoDB initialization failed, using in-memory storage")
    
    def process_message(self, user_id: str, message: str, user_name: str) -> Tuple[str, List[str]]:
        """
        Process incoming message and return response with suggestions
        
        Args:
            user_id: WhatsApp user ID
            message: User's message
            user_name: User's name
            
        Returns:
            Tuple of (response_text, suggestions_list)
        """
        try:
            # Load user session
            user_session = self.session_manager.load_user_session(user_id, user_name)
            
            # Detect intent
            intent = self.intent_detector.detect_intent(message)
            
            # Track analytics
            self.session_manager.track_event("message_received", user_id, {
                "intent": intent,
                "message_length": len(message),
                "confidence": self.intent_detector.get_intent_confidence(message, intent)
            })
            
            # Save user message to conversation history
            self.session_manager.save_conversation(user_id, message, "user", intent)
            
            # Generate response
            response, suggestions = self._generate_response(
                user_id, intent, message, user_name, user_session
            )
            
            # Save bot response to conversation history
            ai_provider = getattr(self.response_generator, 'ai_provider', 'template')
            self.session_manager.save_conversation(user_id, response, "bot", intent, ai_provider)
            
            # Update user session
            self.session_manager.update_session_context(user_id, {
                'name': user_name,
                'last_action': intent,
                'recent_intent': intent
            })
            
            # Track response analytics
            self.session_manager.track_event("response_sent", user_id, {
                "intent": intent,
                "ai_provider": ai_provider,
                "response_length": len(response)
            })
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error processing message from {user_id}: {e}")
            return self._generate_error_response(), ["🔙 Main Menu", "💡 Get Help"]
    
    def _generate_response(
        self, 
        user_id: str, 
        intent: str, 
        message: str, 
        user_name: str, 
        user_session: Dict
    ) -> Tuple[str, List[str]]:
        """
        Generate response using appropriate handler or response generator
        
        Args:
            user_id: User ID
            intent: Detected intent
            message: Original message
            user_name: User's name
            user_session: User session data
            
        Returns:
            Tuple of (response_text, suggestions_list)
        """
        # Prepare user context
        user_context = user_session.get('context', {})
        user_context.update({
            'name': user_name,
            'last_action': user_session.get('last_action'),
            'session_count': user_session.get('session_count', 1)
        })
        
        # Add recent conversation context if available
        recent_history = self.session_manager.get_conversation_history(user_id, 5)
        if recent_history:
            user_context['recent_conversations'] = [
                f"{conv['message_type']}: {conv['message'][:100]}" 
                for conv in recent_history[-3:]
            ]
        
        # Try specialized handler first
        if intent in self.handlers:
            try:
                handler = self.handlers[intent]
                return handler.handle(user_id, message, user_context)
            except Exception as e:
                logging.error(f"Handler error for intent {intent}: {e}")
                # Fall back to response generator
        
        # Use response generator (AI or template)
        try:
            return self.response_generator.generate_response(
                intent, message, user_context, user_name
            )
        except Exception as e:
            logging.error(f"Response generator error: {e}")
            return self._generate_error_response(), ["🔙 Main Menu"]
    
    def _generate_error_response(self) -> str:
        """Generate a friendly error response"""
        return ("🤖 Sorry, I encountered an issue processing your request. "
                "Please try again or contact support if the problem persists.")
    
    # Public API methods for external access
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user interaction statistics"""
        return self.session_manager.get_user_stats(user_id)
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        return self.session_manager.get_conversation_history(user_id, limit)
    
    def handle_file_upload(self, user_id: str, media_id: str, filename: str) -> Tuple[str, List[str]]:
        """Handle file upload from WhatsApp"""
        if 'file_upload' in self.handlers:
            try:
                user_session = self.session_manager.load_user_session(user_id, '')
                user_context = user_session.get('context', {})
                return self.handlers['file_upload'].handle_upload(user_id, media_id, filename, user_context)
            except Exception as e:
                logging.error(f"File upload error: {e}")
        
        return ("❌ Sorry, file upload is not available right now. Please try again later.", 
                ["🔙 Main Menu"])
    
    def clear_user_session(self, user_id: str) -> bool:
        """Clear user session data"""
        return self.session_manager.clear_user_session(user_id)
    
    def get_active_users_count(self, hours: int = 24) -> int:
        """Get count of active users"""
        return self.session_manager.get_active_users_count(hours)
    
    def get_system_health(self) -> Dict:
        """Get system health status"""
        return {
            "database_enabled": self.db_enabled,
            "ai_enabled": self.response_generator.ai_enabled,
            "ai_provider": getattr(self.response_generator, 'ai_provider', 'None'),
            "handlers_loaded": list(self.handlers.keys()),
            "active_users": self.get_active_users_count(1),  # Last hour
            "total_sessions": len(self.session_manager.user_sessions)
        }