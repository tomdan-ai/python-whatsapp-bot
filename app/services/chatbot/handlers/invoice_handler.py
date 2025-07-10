"""
Invoice Generation Handler

Handles invoice creation, customer management, and invoice-related operations.
Integrates with the invoice service for professional invoice generation.
"""

from typing import Dict, List, Tuple
import logging
from .base_handler import BaseHandler


class InvoiceHandler(BaseHandler):
    """Handles invoice generation and management"""
    
    def __init__(self, db_manager=None):
        super().__init__(db_manager)
        self.invoice_service = None
        self._initialize_invoice_service()
    
    def _initialize_invoice_service(self):
        """Initialize the invoice service"""
        try:
            from ...invoice_service import InvoiceService
            self.invoice_service = InvoiceService(self.db_manager)
            self._log_handler_activity("system", "Invoice service initialized")
        except ImportError as e:
            logging.warning(f"Could not load invoice service: {e}")
    
    def handle(self, user_id: str, message: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle invoice generation requests"""
        self._log_handler_activity(user_id, "invoice_request")
        
        if not self.invoice_service:
            return self._get_service_unavailable_response()
        
        message_lower = message.lower()
        
        # Determine specific invoice action
        if any(word in message_lower for word in ['new customer', 'new client']):
            return self._handle_new_customer_invoice(user_id, user_context)
        elif any(word in message_lower for word in ['recurring', 'repeat', 'monthly']):
            return self._handle_recurring_invoice(user_id, user_context)
        elif any(word in message_lower for word in ['recent sale', 'last sale']):
            return self._handle_recent_sale_invoice(user_id, user_context)
        else:
            return self._handle_general_invoice(user_id, user_context)
    
    def _handle_general_invoice(self, user_id: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle general invoice generation request"""
        response = "📄 *Invoice Generator*\n\nI'll help you create a professional invoice. What type do you need?"
        
        suggestions = [
            "🆕 New Customer",
            "🔄 Recurring Invoice",
            "📋 Use Recent Sale",
            "👥 From Contacts"
        ]
        
        return response, suggestions
    
    def _handle_new_customer_invoice(self, user_id: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle new customer invoice creation"""
        response = "🆕 *New Customer Invoice*\n\nLet's create an invoice for a new customer. Please provide:\n\n📋 Customer details:\n• Name\n• Email\n• Address (optional)\n\n📦 Items:\n• Product/Service\n• Quantity\n• Price\n\nExample: \"Coffee Beans, 2kg, $25.99\""
        
        suggestions = [
            "📝 Use Template",
            "📤 Upload Details",
            "💡 Show Example",
            "🔙 Back"
        ]
        
        return response, suggestions
    
    def _handle_recurring_invoice(self, user_id: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle recurring invoice setup"""
        try:
            # Get existing recurring invoices
            recurring_invoices = self.invoice_service.get_recurring_invoices(user_id)
            
            if recurring_invoices:
                response = f"🔄 *Recurring Invoices*\n\nYou have {len(recurring_invoices)} active recurring invoice(s):\n\n"
                
                for idx, invoice in enumerate(recurring_invoices[:3]):
                    customer_name = invoice.get('customer_name', 'Unknown Customer')
                    amount = invoice.get('amount', 0)
                    frequency = invoice.get('frequency', 'monthly')
                    response += f"{idx + 1}. {customer_name} - {self._format_currency(amount)} ({frequency})\n"
                
                response += "\nWhat would you like to do?"
                
                suggestions = [
                    "➕ Add New Recurring",
                    "📊 View Details",
                    "⏸️ Pause/Resume",
                    "🔙 Back"
                ]
            else:
                response = "🔄 *Setup Recurring Invoice*\n\nNo recurring invoices found. Let's create your first one!\n\nRecurring invoices will be automatically generated and sent to your customers."
                
                suggestions = [
                    "➕ Create Recurring",
                    "💡 Learn More",
                    "📋 Use Template",
                    "🔙 Back"
                ]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Recurring invoice error: {e}")
            return self._get_error_response()
    
    def _handle_recent_sale_invoice(self, user_id: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle invoice creation from recent sales"""
        try:
            # Get recent sales without invoices
            uninvoiced_sales = self.invoice_service.get_uninvoiced_sales(user_id, limit=5)
            
            if uninvoiced_sales:
                response = "📋 *Recent Sales Without Invoices*\n\n"
                
                for idx, sale in enumerate(uninvoiced_sales):
                    product = sale.get('product_name', 'Unknown Product')
                    amount = sale.get('total_amount', 0)
                    date = sale.get('date', 'Unknown Date')
                    response += f"{idx + 1}. {product} - {self._format_currency(amount)} ({date})\n"
                
                response += "\nSelect a sale to create an invoice:"
                
                suggestions = [
                    f"📄 Invoice Sale 1",
                    f"📄 Invoice Sale 2", 
                    "📄 Invoice All",
                    "🔙 Back"
                ]
            else:
                response = "📋 *No Recent Sales Found*\n\nI couldn't find any recent sales without invoices. You can:\n\n• Add a new sale record\n• Create a manual invoice\n• Upload sales data"
                
                suggestions = [
                    "➕ Add Sale",
                    "📄 Manual Invoice",
                    "📤 Upload Data",
                    "🔙 Back"
                ]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Recent sales invoice error: {e}")
            return self._get_error_response()
    
    def create_invoice_from_data(self, user_id: str, invoice_data: Dict) -> Tuple[str, List[str]]:
        """Create invoice from provided data"""
        try:
            result = self.invoice_service.create_invoice(user_id, invoice_data)
            
            if result.get("status") == "success":
                invoice_id = result.get("invoice_id")
                pdf_path = result.get("pdf_path")
                
                response = f"✅ *Invoice Created Successfully*\n\n📄 Invoice ID: {invoice_id}\n💰 Amount: {self._format_currency(invoice_data.get('total_amount', 0))}\n👤 Customer: {invoice_data.get('customer_name', 'Unknown')}\n\n📎 PDF invoice has been generated and is ready for download."
                
                suggestions = [
                    "📧 Email Invoice",
                    "📱 Share via WhatsApp",
                    "📋 View Details", 
                    "🔙 Main Menu"
                ]
            else:
                response = f"❌ *Invoice Creation Failed*\n\n{result.get('message', 'Unknown error occurred')}"
                suggestions = ["🔄 Try Again", "💡 Get Help", "🔙 Back"]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Invoice creation error: {e}")
            return self._get_error_response()
    
    def _get_service_unavailable_response(self) -> Tuple[str, List[str]]:
        """Response when invoice service is unavailable"""
        response = "📄 *Invoice Service Unavailable*\n\n⚠️ The invoice generation service is currently unavailable. Please try again later."
        
        suggestions = ["🔄 Try Again", "💡 Contact Support", "🔙 Main Menu"]
        return response, suggestions