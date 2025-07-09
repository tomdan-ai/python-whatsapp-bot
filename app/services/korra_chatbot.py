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
        """Detect user intent from message - Updated with forecasting"""
        
        # Sales Forecasting (Enhanced)
        if any(keyword in message for keyword in ['forecast', 'predict', 'prediction', 'future sales', 'projection', 'what if', 'scenario']):
            return 'sales_forecast'
        
        # Forecast Comparison
        if any(keyword in message for keyword in ['accuracy', 'compare forecast', 'actual vs predicted', 'how accurate']):
            return 'forecast_comparison'
        
        # Scenario Analysis  
        if any(keyword in message for keyword in ['scenario', 'what if', 'optimistic', 'pessimistic', 'best case', 'worst case']):
            return 'scenario_analysis'
        
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
        """Generate response based on intent - Updated with forecasting"""
        
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
        
        # Handle forecasting intents first
        if intent == 'sales_forecast':
            return self.handle_forecasting_request(user_id, message)
        elif intent == 'forecast_comparison':
            return self.handle_forecast_comparison(user_id)
        elif intent == 'scenario_analysis':
            return self.handle_scenario_analysis(user_id, message)
        
        # Try to use AI for other intents, fall back to templates
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
        """Get appropriate suggestions based on intent - Updated with forecasting"""
        
        suggestion_map = {
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
            'general': [
                "📈 Sales Forecast",
                "📄 Create Invoice",
                "📊 View Insights", 
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
    
    # Sales-specific handlers
    def handle_sales_data_input(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle manual sales data input"""
        try:
            from .sales_models import SalesDataManager
            sales_manager = SalesDataManager(self.db_manager)
            
            # Parse sales data from message
            sales_data = self._parse_sales_input(message)
            
            if sales_data:
                success = sales_manager.save_sales_record(user_id, sales_data)
                
                if success:
                    response = f"✅ *Sales Record Saved*\n\n📦 Product: {sales_data['product_name']}\n💰 Amount: ${sales_data['total_amount']:.2f}\n📅 Date: {sales_data['date'].strftime('%Y-%m-%d')}\n\nWhat would you like to do next?"
                    
                    suggestions = [
                        "➕ Add Another Sale",
                        "📊 View Summary", 
                        "📈 Sales Insights",
                        "🔙 Main Menu"
                    ]
                else:
                    response = "❌ Sorry, I couldn't save that sales record. Please try again or contact support."
                    suggestions = ["🔙 Main Menu", "💡 Get Help"]
            else:
                response = "🤔 I couldn't understand the sales data. Please try this format:\n\n*Product name, quantity, price*\n\nExample: \"Coffee, 2, 5.50\" or \"Widget sold for $25\""
                suggestions = ["💡 Show Examples", "📤 Upload File", "🔙 Main Menu"]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error handling sales input: {e}")
            response = "❌ Sorry, there was an error processing your sales data. Please try again."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions
    
    def handle_sales_insights_request(self, user_id: str) -> Tuple[str, List[str]]:
        """Handle request for sales insights"""
        try:
            from .sales_analytics import SalesAnalytics
            analytics = SalesAnalytics(self.db_manager)
            
            insights = analytics.generate_business_insights(user_id, 30)
            
            if insights.get("status") == "no_data":
                response = "📊 *No Sales Data Found*\n\nI don't have any sales data to analyze yet. Let's get started!\n\nYou can:"
                suggestions = [
                    "➕ Add Sales Record",
                    "📤 Upload Sales File",
                    "💡 Learn More",
                    "🔙 Main Menu"
                ]
            elif insights.get("status") == "error":
                response = f"❌ Error generating insights: {insights.get('message', 'Unknown error')}"
                suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            else:
                # Format insights for WhatsApp
                response = self._format_insights_response(insights)
                suggestions = [
                    "📋 Detailed Report",
                    "📊 Compare Periods",
                    "💡 Get Recommendations",
                    "🔙 Main Menu"
                ]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error handling insights request: {e}")
            response = "❌ Sorry, I couldn't generate insights right now. Please try again later."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions
    
    def handle_file_upload(self, user_id: str, media_id: str, filename: str) -> Tuple[str, List[str]]:
        """Handle file upload from WhatsApp"""
        try:
            from .file_processor import create_file_processor
            file_processor = create_file_processor(self.db_manager)
            
            result = file_processor.process_whatsapp_document(media_id, user_id)
            
            if result["status"] == "success":
                data = result.get("data", {})
                response = f"✅ *File Processed Successfully*\n\n📁 File: {data.get('filename', 'Unknown')}\n📊 Records: {data.get('success_count', 0)} processed\n"
                
                if data.get("error_count", 0) > 0:
                    response += f"⚠️ Errors: {data['error_count']} records had issues\n"
                
                response += "\nWhat would you like to do next?"
                
                suggestions = [
                    "📈 View Insights",
                    "📊 Sales Summary",
                    "➕ Add More Data",
                    "🔙 Main Menu"
                ]
                
            elif result["status"] == "warning":
                data = result.get("data", {})
                response = f"⚠️ *Could Not Auto-Process File*\n\n📁 {data.get('filename', 'Unknown')}\n📊 Found {data.get('row_count', 0)} rows\n\nColumns: {', '.join(data.get('columns', [])[:5])}\n\nPlease check the format and try again."
                
                suggestions = [
                    "💡 Format Help",
                    "📤 Try Another File",
                    "➕ Manual Entry",
                    "🔙 Main Menu"
                ]
                
            else:
                response = f"❌ *File Processing Failed*\n\n{result.get('message', 'Unknown error')}\n\nPlease check your file format and try again."
                
                suggestions = [
                    "💡 Format Help",
                    "📤 Try Another File",
                    "🔙 Main Menu"
                ]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error handling file upload: {e}")
            response = "❌ Sorry, I couldn't process your file. Please try again or contact support."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions
    
    def _parse_sales_input(self, message: str) -> Optional[Dict]:
        """Parse sales data from user message"""
        try:
            import re
            
            # Remove common prefixes
            message = re.sub(r'^(sold|sale|add sale|record sale):\s*', '', message.lower().strip())
            
            # Try different patterns
            patterns = [
                # "Product, quantity, price" format
                r'([^,]+),\s*(\d+(?:\.\d+)?),\s*\$?(\d+(?:\.\d+)?)',
                # "Product for $amount" format
                r'([^,]+?)\s+(?:for|sold for|\$)\s*\$?(\d+(?:\.\d+)?)',
                # "Quantity Product at $price" format
                r'(\d+(?:\.\d+)?)\s+([^,]+?)\s+(?:at|@|\$)\s*\$?(\d+(?:\.\d+)?)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message)
                if match:
                    groups = match.groups()
                    
                    if len(groups) == 3:
                        if pattern == patterns[0]:  # product, qty, price
                            product, quantity, price = groups
                            return {
                                'product_name': product.strip().title(),
                                'quantity': float(quantity),
                                'unit_price': float(price),
                                'total_amount': float(quantity) * float(price),
                                'date': datetime.utcnow(),
                                'customer_name': '',
                                'source': 'chat_input'
                            }
                        elif pattern == patterns[2]:  # qty product at price
                            quantity, product, price = groups
                            return {
                                'product_name': product.strip().title(),
                                'quantity': float(quantity),
                                'unit_price': float(price),
                                'total_amount': float(quantity) * float(price),
                                'date': datetime.utcnow(),
                                'customer_name': '',
                                'source': 'chat_input'
                            }
                    elif len(groups) == 2:  # product for amount
                        product, amount = groups
                        return {
                            'product_name': product.strip().title(),
                            'quantity': 1.0,
                            'unit_price': float(amount),
                            'total_amount': float(amount),
                            'date': datetime.utcnow(),
                            'customer_name': '',
                            'source': 'chat_input'
                        }
            
            return None
            
        except Exception as e:
            logging.error(f"Error parsing sales input: {e}")
            return None
    
    def _format_insights_response(self, insights: Dict) -> str:
        """Format insights data for WhatsApp display"""
        try:
            summary = insights.get("summary", {})
            trends = insights.get("trends", {})
            insight_points = insights.get("insights", [])
            
            response = f"📈 *Business Insights* - {insights.get('period', 'Recent')}\n\n"
            
            # Summary stats
            total_revenue = summary.get("total_revenue", 0)
            total_sales = summary.get("total_sales", 0)
            avg_order_value = summary.get("average_order_value", 0)
            
            response += f"💰 Revenue: ${total_revenue:,.2f}\n"
            response += f"📊 Sales: {total_sales} transactions\n"
            response += f"🎯 Avg Order: ${avg_order_value:.2f}\n\n"
            
            # Top product
            top_products = summary.get("top_products", [])
            if top_products:
                top_product = top_products[0]
                response += f"🏆 Best Seller: {top_product['name']}\n"
                response += f"   Revenue: ${top_product['revenue']:.2f}\n\n"
            
            # Key trends
            if trends:
                revenue_trend = trends.get("revenue_trend", {})
                if revenue_trend:
                    direction = "📈" if revenue_trend["direction"] == "up" else "📉"
                    change = revenue_trend["change_percent"]
                    response += f"{direction} Revenue trend: {change:+.1f}%\n"
            
            # Top insights
            if insight_points:
                response += "\n*Key Insights:*\n"
                for insight in insight_points[:3]:  # Show top 3
                    response += f"• {insight}\n"
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"Error formatting insights: {e}")
            return "❌ Error formatting insights data"
    
    # Sales Forecasting handlers
    def handle_forecasting_request(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle sales forecasting requests"""
        try:
            from .sales_forecasting import SalesForecasting
            forecaster = SalesForecasting(self.db_manager)
            
            # Parse forecasting request
            forecast_type = self._parse_forecast_request(message)
            
            if forecast_type == "quick":
                result = forecaster.generate_quick_forecast(user_id)
            elif forecast_type == "weekly":
                result = forecaster.generate_weekly_forecast(user_id)
            elif forecast_type == "monthly":
                result = forecaster.generate_monthly_forecast(user_id)
            elif forecast_type == "trend":
                result = forecaster.analyze_trends(user_id)
            else:
                # Default to quick forecast
                result = forecaster.generate_quick_forecast(user_id)
            
            if result.get("status") == "success":
                response = self._format_forecast_response(result)
                suggestions = [
                    "📊 View Details",
                    "📈 Weekly Forecast", 
                    "📅 Monthly Forecast",
                    "🔙 Main Menu"
                ]
            elif result.get("status") == "insufficient_data":
                response = f"📊 *Need More Data for Forecasting*\n\n{result.get('message', 'Not enough sales data')}\n\nTo generate accurate forecasts, I need:\n• At least 7 days of sales data\n• Multiple sales records\n• Consistent data entry"
                suggestions = [
                    "➕ Add Sales Data",
                    "📤 Upload Sales File",
                    "💡 Learn More",
                    "🔙 Main Menu"
                ]
            else:
                response = f"❌ *Forecasting Error*\n\n{result.get('message', 'Could not generate forecast')}"
                suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error handling forecasting request: {e}")
            response = "❌ Sorry, I couldn't generate a forecast right now. Please try again later."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions
    
    def handle_forecast_comparison(self, user_id: str) -> Tuple[str, List[str]]:
        """Handle forecast vs actual comparison"""
        try:
            from .sales_forecasting import SalesForecasting
            forecaster = SalesForecasting(self.db_manager)
            
            comparison = forecaster.compare_forecast_vs_actual(user_id)
            
            if comparison.get("status") == "success":
                response = self._format_comparison_response(comparison)
                suggestions = [
                    "📈 New Forecast",
                    "📊 Accuracy Details",
                    "🎯 Improve Accuracy",
                    "🔙 Main Menu"
                ]
            elif comparison.get("status") == "no_forecasts":
                response = "📊 *No Previous Forecasts*\n\nI don't have any previous forecasts to compare with actual results.\n\nLet's create your first forecast!"
                suggestions = [
                    "📈 Quick Forecast",
                    "📅 Weekly Forecast",
                    "📤 Upload Data",
                    "🔙 Main Menu"
                ]
            else:
                response = f"❌ *Comparison Error*\n\n{comparison.get('message', 'Could not compare forecasts')}"
                suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error handling forecast comparison: {e}")
            response = "❌ Sorry, I couldn't compare forecasts right now. Please try again later."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions
    
    def handle_scenario_analysis(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle what-if scenario analysis"""
        try:
            from .sales_forecasting import SalesForecasting
            forecaster = SalesForecasting(self.db_manager)
            
            # Parse scenario from message
            scenario = self._parse_scenario_request(message)
            
            result = forecaster.generate_scenario_forecast(user_id, scenario)
            
            if result.get("status") == "success":
                response = self._format_scenario_response(result, scenario)
                suggestions = [
                    "📈 Optimistic Scenario",
                    "📉 Conservative Scenario",
                    "🎯 Custom Scenario",
                    "🔙 Main Menu"
                ]
            else:
                response = f"❌ *Scenario Analysis Error*\n\n{result.get('message', 'Could not analyze scenario')}"
                suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error handling scenario analysis: {e}")
            response = "❌ Sorry, I couldn't analyze scenarios right now. Please try again later."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions
    
    def _parse_forecast_request(self, message: str) -> str:
        """Parse the type of forecast requested"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['quick', 'fast', 'brief', 'summary']):
            return "quick"
        elif any(word in message_lower for word in ['week', 'weekly', '7 day']):
            return "weekly"
        elif any(word in message_lower for word in ['month', 'monthly', '30 day']):
            return "monthly"
        elif any(word in message_lower for word in ['trend', 'pattern', 'direction']):
            return "trend"
        else:
            return "quick"  # Default
    
    def _parse_scenario_request(self, message: str) -> Dict:
        """Parse scenario parameters from message"""
        message_lower = message.lower()
        
        scenario = {
            "type": "normal",
            "growth_rate": 0.0,
            "market_conditions": "normal"
        }
        
        if any(word in message_lower for word in ['optimistic', 'best case', 'good', 'growth']):
            scenario["type"] = "optimistic"
            scenario["growth_rate"] = 0.15  # 15% growth
            scenario["market_conditions"] = "favorable"
        elif any(word in message_lower for word in ['pessimistic', 'worst case', 'bad', 'decline']):
            scenario["type"] = "pessimistic"
            scenario["growth_rate"] = -0.10  # 10% decline
            scenario["market_conditions"] = "unfavorable"
        elif any(word in message_lower for word in ['conservative', 'cautious', 'steady']):
            scenario["type"] = "conservative"
            scenario["growth_rate"] = 0.05  # 5% growth
            scenario["market_conditions"] = "stable"
        
        return scenario
    
    def _format_forecast_response(self, result: Dict) -> str:
        """Format forecast results for WhatsApp display"""
        try:
            forecast_data = result.get("forecast", {})
            
            response = f"📈 *Sales Forecast* - {forecast_data.get('period', 'Next Period')}\n\n"
            
            # Main prediction
            predicted_revenue = forecast_data.get("predicted_revenue", 0)
            predicted_sales = forecast_data.get("predicted_sales", 0)
            confidence = forecast_data.get("confidence_score", 0)
            
            response += f"💰 Predicted Revenue: ${predicted_revenue:,.2f}\n"
            response += f"📊 Predicted Sales: {predicted_sales} transactions\n"
            response += f"🎯 Confidence: {confidence:.1%}\n\n"
            
            # Trend information
            trend = forecast_data.get("trend", {})
            if trend:
                direction = trend.get("direction", "stable")
                magnitude = trend.get("magnitude", 0)
                
                if direction == "increasing":
                    response += f"📈 Trend: Growing by {magnitude:.1%}\n"
                elif direction == "decreasing":
                    response += f"📉 Trend: Declining by {magnitude:.1%}\n"
                else:
                    response += f"➡️ Trend: Stable\n"
            
            # Key insights
            insights = forecast_data.get("insights", [])
            if insights:
                response += "\n*Key Points:*\n"
                for insight in insights[:3]:  # Show top 3
                    response += f"• {insight}\n"
            
            # Recommendations
            recommendations = forecast_data.get("recommendations", [])
            if recommendations:
                response += "\n*Recommendations:*\n"
                for rec in recommendations[:2]:  # Show top 2
                    response += f"• {rec}\n"
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"Error formatting forecast response: {e}")
            return "❌ Error formatting forecast data"
    
    def _format_comparison_response(self, comparison: Dict) -> str:
        """Format forecast comparison results"""
        try:
            accuracy = comparison.get("accuracy", {})
            
            response = "📊 *Forecast vs Actual Results*\n\n"
            
            # Overall accuracy
            overall_accuracy = accuracy.get("overall_accuracy", 0)
            response += f"🎯 Overall Accuracy: {overall_accuracy:.1%}\n\n"
            
            # Revenue comparison
            revenue_comparison = comparison.get("revenue_comparison", {})
            if revenue_comparison:
                predicted = revenue_comparison.get("predicted", 0)
                actual = revenue_comparison.get("actual", 0)
                accuracy_pct = revenue_comparison.get("accuracy", 0)
                
                response += f"💰 Revenue Accuracy: {accuracy_pct:.1%}\n"
                response += f"   Predicted: ${predicted:,.2f}\n"
                response += f"   Actual: ${actual:,.2f}\n\n"
            
            # Performance insights
            insights = comparison.get("insights", [])
            if insights:
                response += "*Performance Insights:*\n"
                for insight in insights[:3]:
                    response += f"• {insight}\n"
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"Error formatting comparison response: {e}")
            return "❌ Error formatting comparison data"
    
    def _format_scenario_response(self, result: Dict, scenario: Dict) -> str:
        """Format scenario analysis results"""
        try:
            scenario_data = result.get("scenario_forecast", {})
            scenario_type = scenario.get("type", "normal").title()
            
            response = f"🎯 *{scenario_type} Scenario Analysis*\n\n"
            
            # Scenario predictions
            predicted_revenue = scenario_data.get("predicted_revenue", 0)
            baseline_revenue = result.get("baseline_revenue", 0)
            
            response += f"💰 Scenario Revenue: ${predicted_revenue:,.2f}\n"
            response += f"📊 Baseline Revenue: ${baseline_revenue:,.2f}\n"
            
            if baseline_revenue > 0:
                difference = predicted_revenue - baseline_revenue
                diff_pct = (difference / baseline_revenue) * 100
                
                if difference > 0:
                    response += f"📈 Upside: +${difference:,.2f} ({diff_pct:+.1f}%)\n"
                else:
                    response += f"📉 Risk: ${difference:,.2f} ({diff_pct:+.1f}%)\n"
            
            response += f"\n*Scenario Assumptions:*\n"
            response += f"• Market Conditions: {scenario.get('market_conditions', 'Normal')}\n"
            response += f"• Growth Rate: {scenario.get('growth_rate', 0):+.1%}\n"
            
            # Scenario insights
            insights = scenario_data.get("insights", [])
            if insights:
                response += "\n*Key Insights:*\n"
                for insight in insights[:2]:
                    response += f"• {insight}\n"
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"Error formatting scenario response: {e}")
            return "❌ Error formatting scenario data"
    
    def handle_anomaly_analysis_request(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle anomaly detection and analysis requests"""
        try:
            from .anomaly_analyzer import create_anomaly_analyzer
            analyzer = create_anomaly_analyzer(self.db_manager)
            
            # Determine type of analysis requested
            if any(word in message.lower() for word in ['alert', 'critical', 'urgent']):
                result = analyzer.get_anomaly_alerts(user_id)
            else:
                result = analyzer.run_full_analysis(user_id)
            
            if result.get("status") == "success":
                response = self._format_anomaly_response(result)
                suggestions = [
                    "📊 View Details",
                    "🚨 Critical Alerts",
                    "💡 Get Recommendations", 
                    "🔙 Main Menu"
                ]
            elif result.get("status") == "no_anomalies":
                response = f"✅ *Great News!*\n\n{result.get('message')}\n\nYour business metrics look healthy with no significant anomalies detected."
                suggestions = [
                    "📈 Sales Forecast",
                    "📊 Business Insights",
                    "➕ Add More Data",
                    "🔙 Main Menu"
                ]
            elif result.get("status") == "alerts_found":
                response = self._format_alert_response(result)
                suggestions = [
                    "🔍 Investigate Issues",
                    "✅ Mark Resolved",
                    "📊 Full Analysis",
                    "🔙 Main Menu"
                ]
            else:
                response = f"❌ *Analysis Error*\n\n{result.get('message', 'Could not run anomaly analysis')}"
                suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error handling anomaly analysis: {e}")
            response = "❌ Sorry, I couldn't run anomaly analysis right now. Please try again later."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions