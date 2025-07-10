import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.invoice_models import Customer, Address

class CustomerService:
    """Service for managing customers"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def create_customer(self, user_id: str, customer_data: Dict) -> Optional[Customer]:
        """Create a new customer"""
        try:
            customer = Customer(
                name=customer_data.get('name', ''),
                email=customer_data.get('email', ''),
                phone=customer_data.get('phone', ''),
                company=customer_data.get('company', ''),
                tax_id=customer_data.get('tax_id', ''),
                payment_terms=customer_data.get('payment_terms', 30),
                notes=customer_data.get('notes', '')
            )
            
            # Set billing address
            if customer_data.get('billing_address'):
                customer.billing_address = Address.from_dict(customer_data['billing_address'])
            
            # Set shipping address if different
            if customer_data.get('shipping_address'):
                customer.shipping_address = Address.from_dict(customer_data['shipping_address'])
            
            # Save to database
            if self.db_manager and hasattr(self.db_manager, 'collections'):
                customer_doc = customer.to_dict()
                customer_doc['user_id'] = user_id
                
                result = self.db_manager.collections['customers'].insert_one(customer_doc)
                if result.inserted_id:
                    self.logger.info(f"Customer created: {customer.id}")
                    return customer
            
            return customer
            
        except Exception as e:
            self.logger.error(f"Error creating customer: {e}")
            return None
    
    def get_customer(self, user_id: str, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return None
            
            customer_doc = self.db_manager.collections['customers'].find_one({
                'user_id': user_id,
                'id': customer_id
            })
            
            if customer_doc:
                return Customer.from_dict(customer_doc)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting customer: {e}")
            return None
    
    def update_customer(self, user_id: str, customer_id: str, updates: Dict) -> bool:
        """Update customer information"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return False
            
            updates['updated_at'] = datetime.utcnow()
            
            result = self.db_manager.collections['customers'].update_one(
                {'user_id': user_id, 'id': customer_id},
                {'$set': updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            self.logger.error(f"Error updating customer: {e}")
            return False
    
    def delete_customer(self, user_id: str, customer_id: str) -> bool:
        """Delete a customer"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return False
            
            # Check if customer has any invoices
            invoice_count = self.db_manager.collections['invoices'].count_documents({
                'user_id': user_id,
                'customer_id': customer_id
            })
            
            if invoice_count > 0:
                self.logger.warning(f"Cannot delete customer {customer_id}: has {invoice_count} invoices")
                return False
            
            result = self.db_manager.collections['customers'].delete_one({
                'user_id': user_id,
                'id': customer_id
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting customer: {e}")
            return False
    
    def list_customers(self, user_id: str, limit: int = 50, skip: int = 0) -> List[Customer]:
        """List all customers for a user"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return []
            
            customers = []
            cursor = self.db_manager.collections['customers'].find({
                'user_id': user_id
            }).sort('name', 1).skip(skip).limit(limit)
            
            for customer_doc in cursor:
                customer = Customer.from_dict(customer_doc)
                customers.append(customer)
            
            return customers
            
        except Exception as e:
            self.logger.error(f"Error listing customers: {e}")
            return []
    
    def search_customers(self, user_id: str, query: str, limit: int = 20) -> List[Customer]:
        """Search customers by name, email, or company"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return []
            
            # Create text search filter
            search_filter = {
                'user_id': user_id,
                '$or': [
                    {'name': {'$regex': query, '$options': 'i'}},
                    {'email': {'$regex': query, '$options': 'i'}},
                    {'company': {'$regex': query, '$options': 'i'}},
                    {'phone': {'$regex': query, '$options': 'i'}}
                ]
            }
            
            customers = []
            cursor = self.db_manager.collections['customers'].find(search_filter).limit(limit)
            
            for customer_doc in cursor:
                customer = Customer.from_dict(customer_doc)
                customers.append(customer)
            
            return customers
            
        except Exception as e:
            self.logger.error(f"Error searching customers: {e}")
            return []
    
    def get_customer_stats(self, user_id: str, customer_id: str) -> Dict:
        """Get customer statistics"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return {}
            
            # Aggregate invoice statistics
            pipeline = [
                {'$match': {'user_id': user_id, 'customer_id': customer_id}},
                {'$group': {
                    '_id': None,
                    'total_invoices': {'$sum': 1},
                    'total_amount': {'$sum': '$total_amount'},
                    'paid_amount': {'$sum': '$paid_amount'},
                    'outstanding_amount': {'$sum': {'$subtract': ['$total_amount', '$paid_amount']}},
                    'avg_invoice_amount': {'$avg': '$total_amount'},
                    'overdue_count': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$and': [
                                        {'$lt': ['$due_date', datetime.utcnow()]},
                                        {'$ne': ['$payment_status', 'paid']},
                                        {'$ne': ['$status', 'cancelled']}
                                    ]
                                },
                                1,
                                0
                            ]
                        }
                    }
                }}
            ]
            
            result = list(self.db_manager.collections['invoices'].aggregate(pipeline))
            
            if result:
                stats = result[0]
                stats.pop('_id', None)
                return stats
            
            return {
                'total_invoices': 0,
                'total_amount': 0,
                'paid_amount': 0,
                'outstanding_amount': 0,
                'avg_invoice_amount': 0,
                'overdue_count': 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting customer stats: {e}")
            return {}

# Initialize service instance
customer_service = CustomerService()