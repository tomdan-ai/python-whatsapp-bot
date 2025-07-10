import logging
from typing import Dict, List
from datetime import datetime, timedelta
from ...models.invoice_models import Invoice, RecurrenceType
from .invoice_core import InvoiceCoreService

class RecurringInvoiceService:
    """Recurring invoice automation"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.invoice_core = InvoiceCoreService(db_manager)
        self.logger = logging.getLogger(__name__)
    
    def process_recurring_invoices(self) -> int:
        """Process recurring invoices that are due"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return 0
            
            # Find invoices due for recurrence
            query = {
                'is_recurring': True,
                'next_invoice_date': {'$lte': datetime.utcnow()},
                'recurrence_type': {'$ne': 'none'},
                'status': {'$ne': 'cancelled'}
            }
            
            cursor = self.db_manager.collections['invoices'].find(query)
            processed_count = 0
            
            for invoice_doc in cursor:
                try:
                    # Create new invoice from template
                    original_invoice = Invoice.from_dict(invoice_doc)
                    
                    # Check if recurrence has ended
                    if (original_invoice.recurrence_end_date and 
                        datetime.utcnow() > original_invoice.recurrence_end_date):
                        continue
                    
                    new_invoice_data = {
                        'customer_id': original_invoice.customer_id,
                        'items': [item.to_dict() for item in original_invoice.items],
                        'notes': original_invoice.notes,
                        'terms': original_invoice.terms,
                        'currency': original_invoice.currency,
                        'is_recurring': True,
                        'recurrence_type': original_invoice.recurrence_type.value
                    }
                    
                    # Create new invoice
                    new_invoice = self.invoice_core.create_invoice(invoice_doc['user_id'], new_invoice_data)
                    
                    if new_invoice:
                        # Update original invoice next date
                        original_invoice.generate_next_invoice_date()
                        self.invoice_core.update_invoice(
                            invoice_doc['user_id'], 
                            original_invoice.id, 
                            {'next_invoice_date': original_invoice.next_invoice_date}
                        )
                        
                        processed_count += 1
                        self.logger.info(f"Created recurring invoice: {new_invoice.invoice_number}")
                
                except Exception as e:
                    self.logger.error(f"Error processing recurring invoice {invoice_doc.get('id')}: {e}")
                    continue
            
            return processed_count
            
        except Exception as e:
            self.logger.error(f"Error processing recurring invoices: {e}")
            return 0
    
    def setup_recurring_invoice(self, user_id: str, invoice_id: str, recurrence_config: Dict) -> bool:
        """Set up recurring schedule for an invoice"""
        try:
            updates = {
                'is_recurring': True,
                'recurrence_type': recurrence_config.get('type', 'monthly'),
                'recurrence_end_date': recurrence_config.get('end_date'),
                'next_invoice_date': recurrence_config.get('next_date', datetime.utcnow() + timedelta(days=30))
            }
            
            return self.invoice_core.update_invoice(user_id, invoice_id, updates)
            
        except Exception as e:
            self.logger.error(f"Error setting up recurring invoice: {e}")
            return False
    
    def stop_recurring_invoice(self, user_id: str, invoice_id: str) -> bool:
        """Stop recurring schedule for an invoice"""
        try:
            updates = {
                'is_recurring': False,
                'recurrence_type': 'none',
                'next_invoice_date': None
            }
            
            return self.invoice_core.update_invoice(user_id, invoice_id, updates)
            
        except Exception as e:
            self.logger.error(f"Error stopping recurring invoice: {e}")
            return False
    
    def get_recurring_invoices(self, user_id: str) -> List[Invoice]:
        """Get all recurring invoices for a user"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return []
            
            query = {
                'user_id': user_id,
                'is_recurring': True,
                'status': {'$ne': 'cancelled'}
            }
            
            invoices = []
            cursor = self.db_manager.collections['invoices'].find(query).sort('next_invoice_date', 1)
            
            for invoice_doc in cursor:
                invoice = Invoice.from_dict(invoice_doc)
                invoices.append(invoice)
            
            return invoices
            
        except Exception as e:
            self.logger.error(f"Error getting recurring invoices: {e}")
            return []