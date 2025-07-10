import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from ...models.invoice_models import (
    Invoice, InvoiceItem, InvoiceStatus, PaymentStatus, RecurrenceType
)

class InvoiceCoreService:
    """Core invoice operations - CRUD operations"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def create_invoice(self, user_id: str, invoice_data: Dict) -> Optional[Invoice]:
        """Create a new invoice"""
        try:
            # Generate invoice number if not provided
            invoice_number = invoice_data.get('invoice_number')
            if not invoice_number:
                invoice_number = self._generate_invoice_number(user_id)
            
            # Create invoice object
            invoice = Invoice(
                invoice_number=invoice_number,
                customer_id=invoice_data.get('customer_id', ''),
                issue_date=invoice_data.get('issue_date', datetime.utcnow()),
                due_date=invoice_data.get('due_date', datetime.utcnow() + timedelta(days=30)),
                status=InvoiceStatus(invoice_data.get('status', 'draft')),
                notes=invoice_data.get('notes', ''),
                terms=invoice_data.get('terms', ''),
                currency=invoice_data.get('currency', 'USD'),
                is_recurring=invoice_data.get('is_recurring', False),
                recurrence_type=RecurrenceType(invoice_data.get('recurrence_type', 'none'))
            )
            
            # Add items
            if invoice_data.get('items'):
                for item_data in invoice_data['items']:
                    item = InvoiceItem.from_dict(item_data)
                    invoice.items.append(item)
            
            # Calculate totals
            invoice.calculate_totals()
            
            # Set up recurrence
            if invoice.is_recurring:
                invoice.generate_next_invoice_date()
            
            # Save to database
            if self.db_manager and hasattr(self.db_manager, 'collections'):
                invoice_doc = invoice.to_dict()
                invoice_doc['user_id'] = user_id
                
                result = self.db_manager.collections['invoices'].insert_one(invoice_doc)
                if result.inserted_id:
                    self.logger.info(f"Invoice created: {invoice.invoice_number}")
                    return invoice
            
            return invoice
            
        except Exception as e:
            self.logger.error(f"Error creating invoice: {e}")
            return None
    
    def get_invoice(self, user_id: str, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return None
            
            invoice_doc = self.db_manager.collections['invoices'].find_one({
                'user_id': user_id,
                'id': invoice_id
            })
            
            if invoice_doc:
                return Invoice.from_dict(invoice_doc)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting invoice: {e}")
            return None
    
    def get_invoice_by_number(self, user_id: str, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return None
            
            invoice_doc = self.db_manager.collections['invoices'].find_one({
                'user_id': user_id,
                'invoice_number': invoice_number
            })
            
            if invoice_doc:
                return Invoice.from_dict(invoice_doc)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting invoice by number: {e}")
            return None
    
    def update_invoice(self, user_id: str, invoice_id: str, updates: Dict) -> bool:
        """Update invoice"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return False
            
            # Get current invoice to recalculate if items changed
            invoice = self.get_invoice(user_id, invoice_id)
            if not invoice:
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(invoice, key):
                    setattr(invoice, key, value)
            
            # Recalculate totals if items were updated
            if 'items' in updates:
                invoice.calculate_totals()
            
            invoice.updated_at = datetime.utcnow()
            
            # Save back to database
            result = self.db_manager.collections['invoices'].update_one(
                {'user_id': user_id, 'id': invoice_id},
                {'$set': invoice.to_dict()}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            self.logger.error(f"Error updating invoice: {e}")
            return False
    
    def delete_invoice(self, user_id: str, invoice_id: str) -> bool:
        """Delete an invoice (only drafts)"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return False
            
            # Only allow deletion of draft invoices
            invoice = self.get_invoice(user_id, invoice_id)
            if not invoice or invoice.status != InvoiceStatus.DRAFT:
                self.logger.warning(f"Cannot delete invoice {invoice_id}: not in draft status")
                return False
            
            result = self.db_manager.collections['invoices'].delete_one({
                'user_id': user_id,
                'id': invoice_id
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting invoice: {e}")
            return False
    
    def duplicate_invoice(self, user_id: str, invoice_id: str) -> Optional[Invoice]:
        """Create a copy of an existing invoice"""
        try:
            original_invoice = self.get_invoice(user_id, invoice_id)
            if not original_invoice:
                return None
            
            # Create new invoice data from original
            new_invoice_data = {
                'customer_id': original_invoice.customer_id,
                'items': [item.to_dict() for item in original_invoice.items],
                'notes': original_invoice.notes,
                'terms': original_invoice.terms,
                'currency': original_invoice.currency,
                'status': 'draft'  # Always create as draft
            }
            
            return self.create_invoice(user_id, new_invoice_data)
            
        except Exception as e:
            self.logger.error(f"Error duplicating invoice: {e}")
            return None
    
    def _generate_invoice_number(self, user_id: str) -> str:
        """Generate unique invoice number"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Get current year and month
            now = datetime.utcnow()
            year_month = now.strftime('%Y%m')
            
            # Find highest number for this month
            query = {
                'user_id': user_id,
                'invoice_number': {'$regex': f'^INV-{year_month}'}
            }
            
            cursor = self.db_manager.collections['invoices'].find(query).sort('invoice_number', -1).limit(1)
            
            last_invoice = None
            for doc in cursor:
                last_invoice = doc
                break
            
            if last_invoice:
                # Extract number and increment
                last_number = last_invoice['invoice_number'].split('-')[-1]
                try:
                    next_number = int(last_number) + 1
                    return f"INV-{year_month}-{next_number:04d}"
                except ValueError:
                    pass
            
            # First invoice of the month
            return f"INV-{year_month}-0001"
            
        except Exception as e:
            self.logger.error(f"Error generating invoice number: {e}")
            return f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"