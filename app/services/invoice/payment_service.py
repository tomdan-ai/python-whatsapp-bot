import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from ...models.invoice_models import Invoice, Payment, PaymentStatus
from .invoice_core import InvoiceCoreService

class PaymentService:
    """Payment management for invoices"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.invoice_core = InvoiceCoreService(db_manager)
        self.logger = logging.getLogger(__name__)
    
    def add_payment(self, user_id: str, invoice_id: str, payment_data: Dict) -> bool:
        """Add payment to invoice"""
        try:
            invoice = self.invoice_core.get_invoice(user_id, invoice_id)
            if not invoice:
                return False
            
            payment = Payment(
                amount=payment_data.get('amount', 0.0),
                payment_date=payment_data.get('payment_date', datetime.utcnow()),
                payment_method=payment_data.get('payment_method', ''),
                transaction_id=payment_data.get('transaction_id', ''),
                notes=payment_data.get('notes', '')
            )
            
            invoice.add_payment(payment)
            
            # Update invoice in database
            return self.invoice_core.update_invoice(user_id, invoice_id, {
                'payments': [p.to_dict() for p in invoice.payments],
                'paid_amount': invoice.paid_amount,
                'payment_status': invoice.payment_status.value,
                'status': invoice.status.value
            })
            
        except Exception as e:
            self.logger.error(f"Error adding payment: {e}")
            return False
    
    def get_payment_history(self, user_id: str, invoice_id: str) -> List[Payment]:
        """Get payment history for an invoice"""
        try:
            invoice = self.invoice_core.get_invoice(user_id, invoice_id)
            if invoice:
                return invoice.payments
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting payment history: {e}")
            return []
    
    def mark_as_paid(self, user_id: str, invoice_id: str, payment_data: Dict = None) -> bool:
        """Mark invoice as fully paid"""
        try:
            invoice = self.invoice_core.get_invoice(user_id, invoice_id)
            if not invoice:
                return False
            
            remaining_amount = invoice.total_amount - invoice.paid_amount
            
            if remaining_amount > 0:
                payment_info = payment_data or {}
                payment_info['amount'] = remaining_amount
                return self.add_payment(user_id, invoice_id, payment_info)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking invoice as paid: {e}")
            return False
    
    def refund_payment(self, user_id: str, invoice_id: str, refund_amount: float, refund_reason: str = "") -> bool:
        """Process a refund for an invoice"""
        try:
            invoice = self.invoice_core.get_invoice(user_id, invoice_id)
            if not invoice:
                return False
            
            if refund_amount > invoice.paid_amount:
                self.logger.error(f"Refund amount exceeds paid amount")
                return False
            
            # Create refund payment (negative amount)
            refund_payment = Payment(
                amount=-refund_amount,
                payment_date=datetime.utcnow(),
                payment_method="refund",
                notes=f"Refund: {refund_reason}"
            )
            
            invoice.add_payment(refund_payment)
            
            # Update invoice
            return self.invoice_core.update_invoice(user_id, invoice_id, {
                'payments': [p.to_dict() for p in invoice.payments],
                'paid_amount': invoice.paid_amount,
                'payment_status': invoice.payment_status.value
            })
            
        except Exception as e:
            self.logger.error(f"Error processing refund: {e}")
            return False