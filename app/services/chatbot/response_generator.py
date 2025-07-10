"""
Response Generation Module

Handles AI-powered and template-based response generation
for different business intents.
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class ResponseGenerator:
    """Generates responses using AI services or templates"""
    
    def __init__(self):
        self.ai_service = None
        self.ai_enabled = False
        self.ai_provider = "None"
        self._initialize_ai_services()
        self.suggestion_map = self._initialize_suggestions()
    
    def _initialize_ai_services(self):
        """Initialize AI services in order of preference"""
        # Try OpenAI first
        try:
            from ..openai_service import openai_service
            self.ai_service = openai_service
            self.ai_enabled = True
            self.ai_provider = "OpenAI"
            logging.info("ResponseGenerator: OpenAI service loaded")
        except ImportError:
            # Fallback to OpenRouter
            try:
                from ..openrouter_service import openrouter_service
                self.ai_service = openrouter_service
                self.ai_enabled = True
                self.ai_provider = "OpenRouter"
                logging.info("ResponseGenerator: OpenRouter service loaded")
            except ImportError:
                # Fallback to DeepSeek
                try:
                    from ..deepseek_service import deepseek_service
                    self.ai_service = deepseek_service
                    self.ai_enabled = True
                    self.ai_provider = "DeepSeek"
                    logging.info("ResponseGenerator: DeepSeek service loaded")
                except ImportError as e:
                    logging.warning(f"ResponseGenerator: No AI services available: {e}")
    
    def _initialize_suggestions(self) -> Dict[str, List[str]]:
        """Initialize suggestion mapping for different intents"""
        return {
            'greeting': [
                "📈 Sales Forecast",
                "📄 Create Invoice", 
                "📊 Business Insights",
                "🔍 Check Anomalies"
            ],
            'sales_forecast': [
                "📈 Quick Forecast",
                "📅 Weekly Forecast", 
                "🎯 Scenario Analysis",
                "🔙 Main Menu"
            ],
            'forecast_comparison': [
                "📈 New Forecast",
                "🎯 Improve Accuracy",
                "📊 View Details",
                "🔙 Main Menu"
            ],
            'scenario_analysis': [
                "📈 Optimistic View",
                "📉 Conservative View",
                "🎯 Custom Scenario",
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
            'sales_input': [
                "➕ Add Another Sale",
                "📊 View Summary", 
                "📈 Sales Insights",
                "🔙 Main Menu"
            ],
            'file_upload': [
                "📈 View Insights",
                "📊 Sales Summary",
                "➕ Add More Data",
                "🔙 Main Menu"
            ],
            'general': [
                "📈 Sales Forecast",
                "📄 Create Invoice",
                "📊 View Insights", 
                "💡 Get Help"
            ]
        }
    
    def generate_response(
        self, 
        intent: str, 
        message: str, 
        user_context: Dict, 
        user_name: str
    ) -> Tuple[str, List[str]]:
        """
        Generate response for given intent and context
        
        Args:
            intent: Detected user intent
            message: Original user message
            user_context: User session context
            user_name: User's name
            
        Returns:
            Tuple of (response_text, suggestions_list)
        """
        # Handle special intents with templates first
        if intent == 'greeting':
            return self._handle_greeting(user_name)
        
        # Try AI service for complex intents
        if self.ai_enabled and self._should_use_ai(intent):
            try:
                logging.info(f"Using {self.ai_provider} for intent: {intent}")
                ai_response = self.ai_service.generate_business_response(
                    user_message=message,
                    intent=intent,
                    context=user_context
                )
                suggestions = self.get_suggestions_for_intent(intent)
                return ai_response, suggestions
                
            except Exception as e:
                logging.error(f"AI service error: {e}")
                # Fall back to template
        
        # Use template responses
        logging.info(f"Using template response for intent: {intent}")
        return self._generate_template_response(intent, user_name)
    
    def _should_use_ai(self, intent: str) -> bool:
        """Determine if AI should be used for this intent"""
        # Use AI for complex business intents
        ai_intents = [
            'business_insights', 'operational_support', 
            'general', 'anomaly_detection'
        ]
        return intent in ai_intents
    
    def _generate_template_response(self, intent: str, user_name: str) -> Tuple[str, List[str]]:
        """Generate template-based response"""
        
        template_responses = {
            'sales_forecast': (
                "📊 *Sales Forecasting*\n\nI can analyze your sales data and predict future performance. How would you like to proceed?",
                ["📈 Use Past 3 Months", "📤 Upload Spreadsheet", "📅 Quick Forecast", "🔙 Back to Menu"]
            ),
            'anomaly_detection': (
                "🔍 *Anomaly Detection*\n\n✅ Analyzing recent data...\n\n⚠️ Found 1 potential issue:\n• Sales dropped 45% on July 7th\n• Possible cause: Weekend effect\n\nWould you like me to investigate further?",
                ["📊 Show Chart", "💡 Get Solutions", "📅 Compare Trends", "✅ Mark Resolved"]
            ),
            'invoice_generation': (
                "📄 *Invoice Generator*\n\nI'll help you create a professional invoice. What type do you need?",
                ["🆕 New Customer", "🔄 Recurring Invoice", "📋 Use Recent Sale", "👥 From Contacts"]
            ),
            'business_insights': (
                "📈 *Business Insights*\n\n*Top 3 Products This Month:*\n1. 🏆 Product A - $2,450 (35%)\n2. 🥈 Product B - $1,890 (27%) \n3. 🥉 Product C - $1,120 (16%)\n\n💰 Total Revenue: $7,020\n📊 Growth: +12% vs last month",
                ["📋 Detailed Report", "📊 Compare Months", "🎯 Restock Alerts", "💡 Growth Ideas"]
            ),
            'operational_support': (
                "💡 *Business Guidance*\n\nHere are proven strategies:\n\n1. 🎁 **Referral Program** - Reward loyal customers\n2. 📱 **WhatsApp Marketing** - Direct customer reach\n3. 📦 **Product Bundles** - Increase order value\n\nWhich interests you most?",
                ["🎁 Setup Referrals", "📱 WhatsApp Marketing", "📦 Create Bundles", "📚 More Strategies"]
            ),
            'general': (
                "🤔 I didn't quite understand that. I'm here to help with your business!\n\nAre you trying to:",
                ["📊 Forecast Sales", "📄 Create Invoice", "📈 View Insights", "🔍 Check Issues"]
            )
        }
        
        response, suggestions = template_responses.get(intent, template_responses['general'])
        return response, suggestions
    
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
    
    def get_suggestions_for_intent(self, intent: str) -> List[str]:
        """Get appropriate suggestions based on intent"""
        return self.suggestion_map.get(intent, self.suggestion_map['general'])
    
    def format_response_with_context(self, response: str, context: Dict) -> str:
        """Add contextual information to response if needed"""
        # Add user-specific context like name, recent actions, etc.
        if context.get('name'):
            response = response.replace('{user_name}', context['name'])
        
        return response