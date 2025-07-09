import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

class KorraChatbot:
    """
    Main Korra Chatbot class that handles business operations and AI responses
    """
    
    def __init__(self):
        self.conversation_context = {}
        self.user_sessions = {}
        
        # Import DeepSeek service here to avoid circular imports
        try:
            from .deepseek_service import deepseek_service
            self.ai_service = deepseek_service
            self.ai_enabled = True
            logging.info("DeepSeek AI service loaded successfully")
        except ImportError as e:
            logging.warning(f"Could not import DeepSeek service: {e}")
            self.ai_service = None
            self.ai_enabled = False
        
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
        
        # Initialize user session if new
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'name': user_name,
                'last_action': None,
                'context': {},
                'conversation_history': []
            }
        
        # Add message to history
        self.user_sessions[user_id]['conversation_history'].append({
            'timestamp': datetime.now(),
            'message': message,
            'type': 'user'
        })
        
        # Determine intent and generate response
        intent = self._detect_intent(message_lower)
        response, suggestions = self._generate_response(user_id, intent, message, user_name)
        
        # Add response to history
        self.user_sessions[user_id]['conversation_history'].append({
            'timestamp': datetime.now(),
            'message': response,
            'type': 'bot'
        })
        
        # Update user context
        self.user_sessions[user_id]['last_action'] = intent
        
        return response, suggestions
    
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
    
    def _generate_response(self, user_id: str, intent: str, message: str, user_name: str) -> Tuple[str, List[str]]:
        """Generate response based on intent"""
        
        # Get user context for AI
        user_context = self.user_sessions[user_id].get('context', {})
        user_context['name'] = user_name
        user_context['last_action'] = self.user_sessions[user_id].get('last_action')
        
        # Try to use AI first, fall back to templates
        if self.ai_enabled and self.ai_service:
            try:
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
                "📊 Compare Months",
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