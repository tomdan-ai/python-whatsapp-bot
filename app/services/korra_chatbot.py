import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

class KorraChatbot:
    """
    Main Korra Chatbot class that handles business operations and AI responses with MongoDB persistence
    """
    
    def __init__(self):
        self.conversation_context = {}
        self.user_sessions = {}
        
        # Initialize database
        try:
            from ..models.database import db_manager
            self.db_manager = db_manager
            self.db_enabled = False  # Will be set to True when Flask app context is available
            logging.info("Database manager loaded successfully")
        except ImportError as e:
            logging.warning(f"Could not import database manager: {e}")
            self.db_manager = None
            self.db_enabled = False
        
        # Try to import AI services in order of preference
        self.ai_service = None
        self.ai_enabled = False
        
        # Try OpenAI first (your existing key)
        try:
            from .openai_service import openai_service
            self.ai_service = openai_service
            self.ai_enabled = True
            self.ai_provider = "OpenAI"
            logging.info("OpenAI service loaded successfully")
        except ImportError:
            # Fallback to OpenRouter
            try:
                from .openrouter_service import openrouter_service
                self.ai_service = openrouter_service
                self.ai_enabled = True
                self.ai_provider = "OpenRouter"
                logging.info("OpenRouter AI service loaded successfully")
            except ImportError:
                # Fallback to DeepSeek
                try:
                    from .deepseek_service import deepseek_service
                    self.ai_service = deepseek_service
                    self.ai_enabled = True
                    self.ai_provider = "DeepSeek"
                    logging.info("DeepSeek AI service loaded successfully")
                except ImportError as e:
                    logging.warning(f"Could not import AI services: {e}")
                    self.ai_service = None
                    self.ai_enabled = False
                    self.ai_provider = "None"
    
    def initialize_database(self):
        """Initialize database connection when Flask app context is available"""
        if self.db_manager:
            self.db_enabled = self.db_manager.initialize_db()
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
        message_lower = message.lower().strip()
        
        # Load user session from database or memory
        user_session = self._load_user_session(user_id, user_name)
        
        # Determine intent and generate response
        intent = self._detect_intent(message_lower)
        
        # Track analytics
        self._track_event("message_received", user_id, {
            "intent": intent,
            "message_length": len(message)
        })
        
        # Save user message to conversation history
        self._save_conversation(user_id, message, "user", intent)
        
        # Generate response
        response, suggestions = self._generate_response(user_id, intent, message, user_name, user_session)
        
        # Save bot response to conversation history
        self._save_conversation(user_id, response, "bot", intent, self.ai_provider)
        
        # Update user session
        user_session['last_action'] = intent
        user_session['last_interaction'] = datetime.utcnow()
        user_session['context']['recent_intent'] = intent
        
        self._save_user_session(user_id, user_session)
        
        # Track response analytics
        self._track_event("response_sent", user_id, {
            "intent": intent,
            "ai_provider": self.ai_provider if self.ai_enabled else "template",
            "response_length": len(response)
        })
        
        return response, suggestions
    
    def _load_user_session(self, user_id: str, user_name: str) -> Dict:
        """Load user session from database or create new one"""
        
        # Try to load from database first
        if self.db_enabled and self.db_manager:
            session = self.db_manager.get_user_session(user_id)
            if session:
                # Update name if changed
                if session.get('name') != user_name:
                    session['name'] = user_name
                return session
        
        # Fallback to memory storage or create new session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'user_id': user_id,
                'name': user_name,
                'created_at': datetime.utcnow(),
                'last_interaction': datetime.utcnow(),
                'last_action': None,
                'context': {},
                'session_count': 1
            }
        
        return self.user_sessions[user_id]
    
    def _save_user_session(self, user_id: str, session_data: Dict) -> bool:
        """Save user session to database"""
        
        # Save to database if available
        if self.db_enabled and self.db_manager:
            success = self.db_manager.save_user_session(user_id, session_data)
            if success:
                return True
        
        # Fallback to memory storage
        self.user_sessions[user_id] = session_data
        return True
    
    def _save_conversation(self, user_id: str, message: str, message_type: str, intent: str = None, ai_provider: str = None) -> bool:
        """Save conversation message to database"""
        
        if self.db_enabled and self.db_manager:
            return self.db_manager.save_conversation(user_id, message, message_type, intent, ai_provider)
        
        # Fallback: could save to memory or log
        logging.debug(f"Conversation {message_type} for {user_id}: {message[:50]}...")
        return True
    
    def _track_event(self, event_type: str, user_id: str = None, data: Dict = None) -> bool:
        """Track analytics events"""
        
        if self.db_enabled and self.db_manager:
            return self.db_manager.track_event(event_type, user_id, data)
        
        # Fallback: log event
        logging.info(f"Event: {event_type} for user {user_id}: {data}")
        return True
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user interaction statistics"""
        
        if self.db_enabled and self.db_manager:
            return self.db_manager.get_user_stats(user_id)
        
        # Fallback: basic stats from memory
        session = self.user_sessions.get(user_id, {})
        return {
            "total_messages": 0,
            "user_messages": 0,
            "bot_messages": 0,
            "first_interaction": session.get('created_at'),
            "last_interaction": session.get('last_interaction'),
            "intent_breakdown": {}
        }
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        
        if self.db_enabled and self.db_manager:
            return self.db_manager.get_conversation_history(user_id, limit)
        
        # Fallback: return empty or minimal data
        return []
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        
        # Sales Forecasting
        if any(keyword in message for keyword in ['forecast', 'predict', 'sales prediction', 'future sales', 'projection']):
            return 'sales_forecast'
        
        # Anomaly Detection
        if any(keyword in message for keyword in ['anomaly', 'unusual', 'strange', 'drop', 'spike', 'alert', 'issue']):
            return 'anomaly_detection'
        
        # Invoice Generation
        if any(keyword in message for keyword in ['invoice', 'receipt', 'bill', 'generate invoice', 'create invoice']):
            return 'invoice_generation'
        
        # Business Insights
        if any(keyword in message for keyword in ['insights', 'report', 'top products', 'best selling', 'revenue', 'profit', 'analytics']):
            return 'business_insights'
        
        # Operational Support
        if any(keyword in message for keyword in ['help', 'how to', 'strategy', 'customers', 'marketing', 'grow', 'advice']):
            return 'operational_support'
        
        # Greeting
        if any(keyword in message for keyword in ['hi', 'hello', 'hey', 'start', 'begin', 'menu']):
            return 'greeting'
        
        return 'general'
    
    def _generate_response(self, user_id: str, intent: str, message: str, user_name: str, user_session: Dict) -> Tuple[str, List[str]]:
        """Generate response based on intent"""
        
        # Get user context for AI (now includes database history)
        user_context = user_session.get('context', {})
        user_context['name'] = user_name
        user_context['last_action'] = user_session.get('last_action')
        user_context['session_count'] = user_session.get('session_count', 1)
        
        # Add recent conversation context if available
        if self.db_enabled:
            recent_history = self.get_conversation_history(user_id, 5)
            if recent_history:
                user_context['recent_conversations'] = [
                    f"{conv['message_type']}: {conv['message'][:100]}" 
                    for conv in recent_history[-3:]  # Last 3 messages
                ]
        
        # Try to use AI first, fall back to templates
        if self.ai_enabled and self.ai_service:
            try:
                logging.info(f"Using {self.ai_provider} for intent: {intent}")
                ai_response = self.ai_service.generate_business_response(
                    user_message=message,
                    intent=intent,
                    context=user_context
                )
                
                # Get suggestions based on intent
                suggestions = self._get_suggestions_for_intent(intent)
                
                return ai_response, suggestions
                
            except Exception as e:
                logging.error(f"AI service error: {e}")
                # Fall back to template responses
        
        # Template fallback responses
        logging.info(f"Using template response for intent: {intent}")
        if intent == 'greeting':
            return self._handle_greeting(user_name)
        elif intent == 'sales_forecast':
            return self._handle_sales_forecast(user_id, message)
        elif intent == 'anomaly_detection':
            return self._handle_anomaly_detection(user_id)
        elif intent == 'invoice_generation':
            return self._handle_invoice_generation(user_id)
        elif intent == 'business_insights':
            return self._handle_business_insights(user_id, message)
        elif intent == 'operational_support':
            return self._handle_operational_support(user_id, message)
        else:
            return self._handle_general(user_id, message)
    
    def _get_suggestions_for_intent(self, intent: str) -> List[str]:
        """Get appropriate suggestions based on intent"""
        
        suggestion_map = {
            'greeting': [
                "📊 Forecast Sales",
                "📄 Create Invoice", 
                "📈 Business Insights",
                "🔍 Check Anomalies"
            ],
            'sales_forecast': [
                "📈 Use Past Data",
                "📤 Upload Spreadsheet", 
                "📅 Weekly Forecast",
                "🔙 Main Menu"
            ],
            'anomaly_detection': [
                "📊 Show Details",
                "💡 Get Solutions",
                "📅 Compare Periods",
                "🔙 Main Menu"
            ],
            'invoice_generation': [
                "🆕 New Customer",
                "🔄 Recurring Invoice", 
                "📋 Recent Sale",
                "🔙 Main Menu"
            ],
            'business_insights': [
                "📋 Full Report",
                "📊 Compare Periods",
                "🎯 Growth Tips",
                "🔙 Main Menu"
            ],
            'operational_support': [
                "📱 Marketing Tips",
                "👥 Customer Retention",
                "📈 Growth Strategy",
                "🔙 Main Menu"
            ],
            'general': [
                "📊 Forecast Sales",
                "📄 Create Invoice",
                "📈 View Insights", 
                "💡 Get Help"
            ]
        }
        
        return suggestion_map.get(intent, suggestion_map['general'])
    
    def _handle_greeting(self, user_name: str) -> Tuple[str, List[str]]:
        """Handle greeting messages"""
        response = f"👋 Hi {user_name}! I'm Korra, your AI business assistant.\n\nI can help you with:\n• 📊 Sales forecasting\n• 🔍 Anomaly detection\n• 📄 Invoice generation\n• 📈 Business insights\n• 💡 Operational guidance\n\nWhat would you like to do today?"
        
        suggestions = [
            "📊 Forecast Sales",
            "📄 Create Invoice", 
            "📈 Business Insights",
            "🔍 Check Anomalies"
        ]
        
        return response, suggestions
    
    def _handle_sales_forecast(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle sales forecasting requests"""
        response = "📊 *Sales Forecasting*\n\nI can analyze your sales data and predict future performance. How would you like to proceed?"
        
        suggestions = [
            "📈 Use Past 3 Months",
            "📤 Upload Spreadsheet", 
            "📅 Quick Forecast",
            "🔙 Back to Menu"
        ]
        
        return response, suggestions
    
    def _handle_anomaly_detection(self, user_id: str) -> Tuple[str, List[str]]:
        """Handle anomaly detection requests"""
        response = "🔍 *Anomaly Detection*\n\n✅ Analyzing recent data...\n\n⚠️ Found 1 potential issue:\n• Sales dropped 45% on July 7th\n• Possible cause: Weekend effect\n\nWould you like me to investigate further?"
        
        suggestions = [
            "📊 Show Chart",
            "💡 Get Solutions",
            "📅 Compare Trends",
            "✅ Mark Resolved"
        ]
        
        return response, suggestions
    
    def _handle_invoice_generation(self, user_id: str) -> Tuple[str, List[str]]:
        """Handle invoice generation requests"""
        response = "📄 *Invoice Generator*\n\nI'll help you create a professional invoice. What type do you need?"
        
        suggestions = [
            "🆕 New Customer",
            "🔄 Recurring Invoice", 
            "📋 Use Recent Sale",
            "👥 From Contacts"
        ]
        
        return response, suggestions
    
    def _handle_business_insights(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle business insights requests"""
        response = "📈 *Business Insights*\n\n*Top 3 Products This Month:*\n1. 🏆 Product A - $2,450 (35%)\n2. 🥈 Product B - $1,890 (27%) \n3. 🥉 Product C - $1,120 (16%)\n\n💰 Total Revenue: $7,020\n📊 Growth: +12% vs last month"
        
        suggestions = [
            "📋 Detailed Report",
            "📊 Compare Months",
            "🎯 Restock Alerts",
            "💡 Growth Ideas"
        ]
        
        return response, suggestions
    
    def _handle_operational_support(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle operational support and guidance"""
        response = "💡 *Business Guidance*\n\nHere are proven strategies:\n\n1. 🎁 **Referral Program** - Reward loyal customers\n2. 📱 **WhatsApp Marketing** - Direct customer reach\n3. 📦 **Product Bundles** - Increase order value\n\nWhich interests you most?"
        
        suggestions = [
            "🎁 Setup Referrals",
            "📱 WhatsApp Marketing",
            "📦 Create Bundles",
            "📚 More Strategies"
        ]
        
        return response, suggestions
    
    def _handle_general(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle general/unclear messages"""
        response = "🤔 I didn't quite understand that. I'm here to help with your business!\n\nAre you trying to:"
        
        suggestions = [
            "📊 Forecast Sales",
            "📄 Create Invoice",
            "📈 View Insights", 
            "🔍 Check Issues"
        ]
        
        return response, suggestions

# Initialize the chatbot instance
korra_bot = KorraChatbot()