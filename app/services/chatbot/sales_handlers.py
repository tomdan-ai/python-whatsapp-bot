"""
Sales-related Message Handlers

Handles sales data input, insights requests, file uploads,
and sales-related business operations.
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class SalesHandlers:
    """Handles sales-related chatbot interactions"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
    
    def handle_sales_data_input(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """
        Handle manual sales data input
        
        Args:
            user_id: User ID
            message: Message containing sales data
            
        Returns:
            Tuple of (response_text, suggestions_list)
        """
        try:
            from ..sales_models import SalesDataManager
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
        """
        Handle request for sales insights
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (response_text, suggestions_list)
        """
        try:
            from ..sales_analytics import SalesAnalytics
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
        """
        Handle file upload from WhatsApp
        
        Args:
            user_id: User ID
            media_id: WhatsApp media ID
            filename: Original filename
            
        Returns:
            Tuple of (response_text, suggestions_list)
        """
        try:
            from ..file_processor import create_file_processor
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
        """
        Parse sales data from user message
        
        Args:
            message: User message containing sales data
            
        Returns:
            Parsed sales data dictionary or None
        """
        try:
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
        """
        Format insights data for WhatsApp display
        
        Args:
            insights: Insights data dictionary
            
        Returns:
            Formatted response string
        """
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
    
    def get_sales_summary(self, user_id: str, days: int = 30) -> Dict:
        """
        Get sales summary for user
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Sales summary dictionary
        """
        try:
            from ..sales_analytics import SalesAnalytics
            analytics = SalesAnalytics(self.db_manager)
            return analytics.generate_business_insights(user_id, days)
        except Exception as e:
            logging.error(f"Error getting sales summary: {e}")
            return {"status": "error", "message": str(e)}
    
    def validate_sales_input(self, message: str) -> Dict:
        """
        Validate sales input format
        
        Args:
            message: Message to validate
            
        Returns:
            Validation result dictionary
        """
        parsed = self._parse_sales_input(message)
        
        if parsed:
            return {
                "valid": True,
                "parsed_data": parsed,
                "confidence": 0.9
            }
        else:
            return {
                "valid": False,
                "error": "Could not parse sales data",
                "suggestions": [
                    "Try format: Product, quantity, price",
                    "Example: Coffee, 2, 5.50",
                    "Or: Product sold for $amount"
                ]
            }