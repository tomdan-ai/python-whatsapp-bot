import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ...models.invoice_models import Invoice, InvoiceStatus, PaymentStatus

class InvoiceQueryService:
    """Invoice query and search operations"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def list_invoices(self, user_id: str, filters: Dict = None, limit: int = 50, skip: int = 0) -> List[Invoice]:
        """List invoices with optional filters"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return []
            
            # Build query filters
            query = {'user_id': user_id}
            
            if filters:
                if filters.get('status'):
                    query['status'] = filters['status']
                if filters.get('payment_status'):
                    query['payment_status'] = filters['payment_status']
                if filters.get('customer_id'):
                    query['customer_id'] = filters['customer_id']
                if filters.get('date_from'):
                    query.setdefault('issue_date', {})['$gte'] = filters['date_from']
                if filters.get('date_to'):
                    query.setdefault('issue_date', {})['$lte'] = filters['date_to']
                if filters.get('overdue_only'):
                    query['due_date'] = {'$lt': datetime.utcnow()}
                    query['payment_status'] = {'$ne': 'paid'}
                    query['status'] = {'$ne': 'cancelled'}
            
            invoices = []
            cursor = self.db_manager.collections['invoices'].find(query).sort('created_at', -1).skip(skip).limit(limit)
            
            for invoice_doc in cursor:
                invoice = Invoice.from_dict(invoice_doc)
                invoices.append(invoice)
            
            return invoices
            
        except Exception as e:
            self.logger.error(f"Error listing invoices: {e}")
            return []
    
    def search_invoices(self, user_id: str, search_term: str) -> List[Invoice]:
        """Search invoices by number, customer name, or notes"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return []
            
            # Build search query
            query = {
                'user_id': user_id,
                '$or': [
                    {'invoice_number': {'$regex': search_term, '$options': 'i'}},
                    {'notes': {'$regex': search_term, '$options': 'i'}},
                    {'customer.name': {'$regex': search_term, '$options': 'i'}},
                    {'customer.company': {'$regex': search_term, '$options': 'i'}}
                ]
            }
            
            invoices = []
            cursor = self.db_manager.collections['invoices'].find(query).sort('created_at', -1).limit(50)
            
            for invoice_doc in cursor:
                invoice = Invoice.from_dict(invoice_doc)
                invoices.append(invoice)
            
            return invoices
            
        except Exception as e:
            self.logger.error(f"Error searching invoices: {e}")
            return []
    
    def get_overdue_invoices(self, user_id: str) -> List[Invoice]:
        """Get all overdue invoices"""
        filters = {'overdue_only': True}
        return self.list_invoices(user_id, filters)
    
    def get_customer_invoices(self, user_id: str, customer_id: str) -> List[Invoice]:
        """Get all invoices for a specific customer"""
        filters = {'customer_id': customer_id}
        return self.list_invoices(user_id, filters)
    
    def get_invoices_by_status(self, user_id: str, status: str) -> List[Invoice]:
        """Get invoices by status"""
        filters = {'status': status}
        return self.list_invoices(user_id, filters)
    
    def get_invoices_by_date_range(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Invoice]:
        """Get invoices within date range"""
        filters = {
            'date_from': start_date,
            'date_to': end_date
        }
        return self.list_invoices(user_id, filters)