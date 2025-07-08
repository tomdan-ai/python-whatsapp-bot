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
        
        return response, suggestions
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        
        # Sales Forecasting
        if any(keyword in message for keyword in ['forecast', 'predict', 'sales prediction', 'future sales']):
            return 'sales_forecast'
        
        # Anomaly Detection
        if any(keyword in message for keyword in ['anomaly', 'unusual', 'strange', 'drop', 'spike', 'alert']):
            return 'anomaly_detection'
        
        # Invoice Generation
        if any(keyword in message for keyword in ['invoice', 'receipt', 'bill', 'generate invoice']):
            return 'invoice_generation'
        
        # Business Insights
        if any(keyword in message for keyword in ['insights', 'report', 'top products', 'best selling', 'revenue', 'profit']):
            return 'business_insights'
        
        # Operational Support
        if any(keyword in message for keyword in ['help', 'how to', 'strategy', 'customers', 'marketing', 'grow']):
            return 'operational_support'
        
        # Greeting
        if any(keyword in message for keyword in ['hi', 'hello', 'hey', 'start', 'begin']):
            return 'greeting'
        
        return 'general'
    
    def _generate_response(self, user_id: str, intent: str, message: str, user_name: str) -> Tuple[str, List[str]]:
        """Generate response based on intent"""
        
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
    
    def _handle_greeting(self, user_name: str) -> Tuple[str, List[str]]:
        """Handle greeting messages"""
        response = f"👋 Hi {user_name}! I'm Korra, your AI business assistant.\n\nI can help you with:\n• 📊 Sales forecasting\n• 🔍 Anomaly detection\n• 📄 Invoice generation\n• 📈 Business insights\n• 💡 Operational guidance\n\nWhat would you like to do today?"
        
        suggestions = [
            "📊 Forecast Sales",
            "📄 Create Invoice", 
            "📈 Business Insights",
            "🔍 Check Anomalies",
            "💡 Get Business Help"
        ]
        
        return response, suggestions
    
    def _handle_sales_forecast(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle sales forecasting requests"""
        response = "📊 *Sales Forecasting*\n\nI can analyze your sales data and predict future performance. How would you like to proceed?"
        
        suggestions = [
            "📈 Use Past 3 Months Data",
            "📤 Upload Sales Spreadsheet", 
            "📅 Quick Weekly Forecast",
            "🔙 Back to Main Menu"
        ]
        
        return response, suggestions
    
    def _handle_anomaly_detection(self, user_id: str) -> Tuple[str, List[str]]:
        """Handle anomaly detection requests"""
        # Simulate anomaly detection
        response = "🔍 *Anomaly Detection*\n\n✅ Analyzing your recent business data...\n\n⚠️ Found 1 anomaly:\n• Sales dropped 45% on July 5th compared to weekly average\n• Possible cause: Weekend effect or inventory shortage"
        
        suggestions = [
            "📊 Show Detailed Chart",
            "💡 Suggest Solutions",
            "📅 Compare with Last Month",
            "✅ Mark as Resolved"
        ]
        
        return response, suggestions
    
    def _handle_invoice_generation(self, user_id: str) -> Tuple[str, List[str]]:
        """Handle invoice generation requests"""
        response = "📄 *Invoice Generator*\n\nI'll help you create a professional invoice. What type of invoice do you need?"
        
        suggestions = [
            "🆕 New Customer Invoice",
            "🔄 Recurring Invoice", 
            "📋 Use Recent Sale",
            "👥 Select from Contacts"
        ]
        
        return response, suggestions
    
    def _handle_business_insights(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle business insights requests"""
        # Simulate business insights
        response = "📈 *Business Insights*\n\n*Top 3 Products This Month:*\n1. 🏆 Product A - $2,450 (35%)\n2. 🥈 Product B - $1,890 (27%) \n3. 🥉 Product C - $1,120 (16%)\n\n💰 Total Revenue: $7,020\n📊 Growth: +12% vs last month"
        
        suggestions = [
            "📋 Full Report (PDF)",
            "📊 Compare Periods",
            "🎯 Restock Alerts",
            "💡 Growth Suggestions"
        ]
        
        return response, suggestions
    
    def _handle_operational_support(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle operational support and guidance"""
        response = "💡 *Business Guidance*\n\nHere are proven strategies to grow your business:\n\n1. 🎁 **Referral Program** - Reward customers for bringing friends\n2. 📱 **WhatsApp Marketing** - Send promotions to your customer list\n3. 📦 **Product Bundles** - Package items together for higher sales\n\nWhich strategy interests you most?"
        
        suggestions = [
            "🎁 Set up Referrals",
            "📱 WhatsApp Marketing",
            "📦 Create Bundles",
            "📚 More Strategies"
        ]
        
        return response, suggestions
    
    def _handle_general(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle general/unclear messages"""
        response = "🤔 I didn't quite understand that. I'm here to help with your business needs!\n\nAre you trying to:"
        
        suggestions = [
            "📊 Forecast Sales",
            "📄 Create Invoice",
            "📈 View Insights", 
            "🔍 Check for Issues",
            "💡 Get Business Advice"
        ]
        
        return response, suggestions

# Initialize the chatbot instance
korra_bot = KorraChatbot()