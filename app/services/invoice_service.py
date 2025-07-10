import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from .invoice.invoice_core import InvoiceCoreService
from .invoice.invoice_query import InvoiceQueryService
from .invoice.payment_service import PaymentService
from .invoice.invoice_analytics import InvoiceAnalytics
from .invoice.recurring_service import RecurringInvoiceService
from .customer_service import customer_service
from .pdf_invoice_service import pdf_invoice_service

class InvoiceService:
    """Main invoice service orchestrator - coordinates all invoice operations"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize service modules
        self.core = InvoiceCoreService(db_manager)
        self.query = InvoiceQueryService(db_manager)
        self.payments = PaymentService(db_manager)
        self.analytics = InvoiceAnalytics(db_manager)
        self.recurring = RecurringInvoiceService(db_manager)
        
        # External services
        self.customer_service = customer_service
        self.pdf_service = pdf_invoice_service
    
    def set_db_manager(self, db_manager):
        """Set database manager for all services"""
        self.db_manager = db_manager
        self.core.db_manager = db_manager
        self.query.db_manager = db_manager
        self.payments.db_manager = db_manager
        self.analytics.db_manager = db_manager
        self.recurring.db_manager = db_manager
        self.customer_service.db_manager = db_manager
    
    # Core Operations (delegate to core service)
    def create_invoice(self, user_id: str, invoice_data: Dict):
        """Create a new invoice"""
        invoice = self.core.create_invoice(user_id, invoice_data)
        
        # Load customer information if available
        if invoice and invoice.customer_id:
            invoice.customer = self.customer_service.get_customer(user_id, invoice.customer_id)
        
        return invoice
    
    def get_invoice(self, user_id: str, invoice_id: str):
        """Get invoice by ID"""
        invoice = self.core.get_invoice(user_id, invoice_id)
        
        # Load customer information if available
        if invoice and invoice.customer_id and not invoice.customer:
            invoice.customer = self.customer_service.get_customer(user_id, invoice.customer_id)
        
        return invoice
    
    def get_invoice_by_number(self, user_id: str, invoice_number: str):
        """Get invoice by number"""
        return self.core.get_invoice_by_number(user_id, invoice_number)
    
    def update_invoice(self, user_id: str, invoice_id: str, updates: Dict) -> bool:
        """Update invoice"""
        return self.core.update_invoice(user_id, invoice_id, updates)
    
    def delete_invoice(self, user_id: str, invoice_id: str) -> bool:
        """Delete invoice"""
        return self.core.delete_invoice(user_id, invoice_id)
    
    def duplicate_invoice(self, user_id: str, invoice_id: str):
        """Duplicate invoice"""
        return self.core.duplicate_invoice(user_id, invoice_id)
    
    # Query Operations (delegate to query service)
    def list_invoices(self, user_id: str, filters: Dict = None, limit: int = 50, skip: int = 0):
        """List invoices with filters"""
        invoices = self.query.list_invoices(user_id, filters, limit, skip)
        
        # Load customer information for each invoice
        for invoice in invoices:
            if invoice.customer_id and not invoice.customer:
                invoice.customer = self.customer_service.get_customer(user_id, invoice.customer_id)
        
        return invoices
    
    def search_invoices(self, user_id: str, search_term: str):
        """Search invoices"""
        return self.query.search_invoices(user_id, search_term)
    
    def get_overdue_invoices(self, user_id: str):
        """Get overdue invoices"""
        return self.query.get_overdue_invoices(user_id)
    
    def get_customer_invoices(self, user_id: str, customer_id: str):
        """Get customer invoices"""
        return self.query.get_customer_invoices(user_id, customer_id)
    
    # Payment Operations (delegate to payment service)
    def add_payment(self, user_id: str, invoice_id: str, payment_data: Dict) -> bool:
        """Add payment to invoice"""
        return self.payments.add_payment(user_id, invoice_id, payment_data)
    
    def get_payment_history(self, user_id: str, invoice_id: str):
        """Get payment history"""
        return self.payments.get_payment_history(user_id, invoice_id)
    
    def mark_as_paid(self, user_id: str, invoice_id: str, payment_data: Dict = None) -> bool:
        """Mark invoice as paid"""
        return self.payments.mark_as_paid(user_id, invoice_id, payment_data)
    
    # Analytics Operations (delegate to analytics service)
    def get_invoice_stats(self, user_id: str, period_days: int = 30) -> Dict:
        """Get invoice statistics"""
        return self.analytics.get_invoice_stats(user_id, period_days)
    
    def get_revenue_trends(self, user_id: str, period_days: int = 90) -> Dict:
        """Get revenue trends"""
        return self.analytics.get_revenue_trends(user_id, period_days)
    
    def get_customer_analytics(self, user_id: str) -> Dict:
        """Get customer analytics"""
        return self.analytics.get_customer_analytics(user_id)
    
    # Recurring Operations (delegate to recurring service)
    def process_recurring_invoices(self) -> int:
        """Process recurring invoices"""
        return self.recurring.process_recurring_invoices()
    
    def setup_recurring_invoice(self, user_id: str, invoice_id: str, recurrence_config: Dict) -> bool:
        """Setup recurring invoice"""
        return self.recurring.setup_recurring_invoice(user_id, invoice_id, recurrence_config)
    
    def get_recurring_invoices(self, user_id: str):
        """Get recurring invoices"""
        return self.recurring.get_recurring_invoices(user_id)
    
    # Status Operations
    def send_invoice(self, user_id: str, invoice_id: str) -> bool:
        """Mark invoice as sent"""
        updates = {
            'status': 'sent',
            'sent_at': datetime.utcnow()
        }
        return self.update_invoice(user_id, invoice_id, updates)
    
    def cancel_invoice(self, user_id: str, invoice_id: str) -> bool:
        """Cancel invoice"""
        invoice = self.get_invoice(user_id, invoice_id)
        if not invoice or invoice.payment_status.value == 'paid':
            return False
        
        updates = {
            'status': 'cancelled',
            'cancelled_at': datetime.utcnow()
        }
        return self.update_invoice(user_id, invoice_id, updates)
    
    def mark_invoice_viewed(self, user_id: str, invoice_id: str) -> bool:
        """Mark invoice as viewed"""
        invoice = self.get_invoice(user_id, invoice_id)
        if not invoice or invoice.status.value != 'sent':
            return True
        
        updates = {
            'status': 'viewed',
            'viewed_at': datetime.utcnow()
        }
        return self.update_invoice(user_id, invoice_id, updates)
    
    # PDF Generation
    def generate_pdf(self, user_id: str, invoice_id: str, company_info: Dict = None) -> Optional[bytes]:
        """Generate PDF for invoice"""
        try:
            invoice = self.get_invoice(user_id, invoice_id)
            if not invoice:
                return None
            
            return self.pdf_service.generate_invoice_pdf(invoice, company_info)
            
        except Exception as e:
            self.logger.error(f"Error generating PDF: {e}")
            return None

# Create global instance
invoice_service = InvoiceService()