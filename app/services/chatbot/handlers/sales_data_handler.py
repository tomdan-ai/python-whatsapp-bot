"""
Sales Data Input Handler

Handles manual sales data entry and validation from user messages.
"""

from typing import Dict, List, Tuple, Optional
import re
import logging
from datetime import datetime
from .base_handler import BaseHandler


class SalesDataHandler(BaseHandler):
    """Handles sales data input and validation"""
    
    def __init__(self, db_manager=None):
        super().__init__(db_manager)
        self.sales_manager = None
        self._initialize_sales_manager()
    
    def _initialize_sales_manager(self):
        """Initialize the sales data manager"""
        try:
            from ...sales_models import SalesDataManager
            self.sales_manager = SalesDataManager(self.db_manager)
            self._log_handler_activity("system", "Sales manager initialized")
        except ImportError as e:
            logging.warning(f"Could not load sales manager: {e}")
    
    def handle(self, user_id: str, message: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle sales data input"""
        self._log_handler_activity(user_id, "sales_input", {"message": message[:50]})
        
        if not self.sales_manager:
            return self._get_service_unavailable_response()
        
        try:
            # Parse sales data from message
            sales_data = self._parse_sales_input(message)
            
            if sales_data:
                success = self.sales_manager.save_sales_record(user_id, sales_data)
                
                if success:
                    return self._format_success_response(sales_data)
                else:
                    return self._get_error_response("Failed to save sales record")
            else:
                return self._get_invalid_format_response()
                
        except Exception as e:
            logging.error(f"Sales data handling error: {e}")
            return self._get_error_response()
    
    def _parse_sales_input(self, message: str) -> Optional[Dict]:
        """Parse sales data from user message"""
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
                        if pattern == patterns[0]:  # Product, qty, price
                            product_name = groups[0].strip()
                            quantity = float(groups[1])
                            unit_price = float(groups[2])
                        elif pattern == patterns[1]:  # Product for $amount
                            product_name = groups[0].strip()
                            quantity = 1.0
                            unit_price = float(groups[1])
                        else:  # Qty Product at $price
                            quantity = float(groups[0])
                            product_name = groups[1].strip()
                            unit_price = float(groups[2])
                        
                        return {
                            'product_name': product_name,
                            'quantity': quantity,
                            'unit_price': unit_price,
                            'total_amount': quantity * unit_price,
                            'date': datetime.utcnow(),
                            'source': 'whatsapp_input'
                        }
            
            return None
            
        except (ValueError, AttributeError) as e:
            logging.warning(f"Sales parsing error: {e}")
            return None
    
    def _format_success_response(self, sales_data: Dict) -> Tuple[str, List[str]]:
        """Format successful sales entry response"""
        response = f"✅ *Sales Record Saved*\n\n"
        response += f"📦 Product: {sales_data['product_name']}\n"
        response += f"📊 Quantity: {sales_data['quantity']}\n"
        response += f"💰 Unit Price: {self._format_currency(sales_data['unit_price'])}\n"
        response += f"💵 Total: {self._format_currency(sales_data['total_amount'])}\n"
        response += f"📅 Date: {sales_data['date'].strftime('%Y-%m-%d %H:%M')}\n\n"
        response += "What would you like to do next?"
        
        suggestions = [
            "➕ Add Another Sale",
            "📊 View Summary",
            "📈 Sales Insights", 
            "🔙 Main Menu"
        ]
        
        return response, suggestions
    
    def _get_invalid_format_response(self) -> Tuple[str, List[str]]:
        """Response for invalid sales data format"""
        response = "🤔 *Invalid Sales Format*\n\nI couldn't understand the sales data. Please try one of these formats:\n\n"
        response += "*Format 1:* Product, quantity, price\n"
        response += "Example: \"Coffee, 2, 5.50\"\n\n"
        response += "*Format 2:* Product for $amount\n"
        response += "Example: \"Widget sold for $25\"\n\n"
        response += "*Format 3:* Quantity Product at $price\n"
        response += "Example: \"3 Books at $15.99\""
        
        suggestions = [
            "💡 Show More Examples",
            "📤 Upload File Instead",
            "🔙 Main Menu"
        ]
        
        return response, suggestions
    
    def _get_service_unavailable_response(self) -> Tuple[str, List[str]]:
        """Response when sales service is unavailable"""
        response = "📊 *Sales Service Unavailable*\n\n⚠️ The sales data service is currently unavailable. Please try again later."
        
        suggestions = ["🔄 Try Again", "📤 Upload File", "🔙 Main Menu"]
        return response, suggestions
    
    def get_sales_summary(self, user_id: str, days: int = 30) -> Tuple[str, List[str]]:
        """Get sales summary for user"""
        if not self.sales_manager:
            return self._get_service_unavailable_response()
        
        try:
            summary = self.sales_manager.get_sales_summary(user_id, days)
            
            if summary.get("total_records", 0) > 0:
                response = f"📊 *Sales Summary ({days} days)*\n\n"
                response += f"📈 Total Sales: {summary.get('total_records', 0)}\n"
                response += f"💰 Total Revenue: {self._format_currency(summary.get('total_revenue', 0))}\n"
                response += f"📦 Top Product: {summary.get('top_product', 'N/A')}\n"
                response += f"📅 Daily Average: {self._format_currency(summary.get('daily_average', 0))}"
                
                suggestions = [
                    "📋 Detailed Report",
                    "📈 View Trends",
                    "💡 Get Insights",
                    "🔙 Main Menu"
                ]
            else:
                response = "📊 *No Sales Data*\n\nNo sales records found for the selected period."
                suggestions = [
                    "➕ Add Sales Data",
                    "📤 Upload File", 
                    "🔙 Main Menu"
                ]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Sales summary error: {e}")
            return self._get_error_response()