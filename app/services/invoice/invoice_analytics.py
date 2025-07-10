import logging
from typing import Dict, List
from datetime import datetime, timedelta

class InvoiceAnalytics:
    """Invoice analytics and statistics"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_invoice_stats(self, user_id: str, period_days: int = 30) -> Dict:
        """Get comprehensive invoice statistics"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return {}
            
            # Date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Aggregate statistics
            pipeline = [
                {'$match': {
                    'user_id': user_id,
                    'created_at': {'$gte': start_date, '$lte': end_date}
                }},
                {'$group': {
                    '_id': None,
                    'total_invoices': {'$sum': 1},
                    'total_amount': {'$sum': '$total_amount'},
                    'paid_amount': {'$sum': '$paid_amount'},
                    'outstanding_amount': {'$sum': {'$subtract': ['$total_amount', '$paid_amount']}},
                    'avg_invoice_amount': {'$avg': '$total_amount'},
                    'draft_count': {
                        '$sum': {'$cond': [{'$eq': ['$status', 'draft']}, 1, 0]}
                    },
                    'sent_count': {
                        '$sum': {'$cond': [{'$eq': ['$status', 'sent']}, 1, 0]}
                    },
                    'paid_count': {
                        '$sum': {'$cond': [{'$eq': ['$payment_status', 'paid']}, 1, 0]}
                    },
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
                
                # Calculate additional metrics
                if stats['total_invoices'] > 0:
                    stats['payment_rate'] = (stats['paid_count'] / stats['total_invoices']) * 100
                    stats['overdue_rate'] = (stats['overdue_count'] / stats['total_invoices']) * 100
                else:
                    stats['payment_rate'] = 0
                    stats['overdue_rate'] = 0
                
                return stats
            
            return self._empty_stats()
            
        except Exception as e:
            self.logger.error(f"Error getting invoice stats: {e}")
            return {}
    
    def get_revenue_trends(self, user_id: str, period_days: int = 90) -> Dict:
        """Get revenue trends over time"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return {}
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Daily revenue aggregation
            pipeline = [
                {'$match': {
                    'user_id': user_id,
                    'created_at': {'$gte': start_date, '$lte': end_date}
                }},
                {'$group': {
                    '_id': {
                        'year': {'$year': '$created_at'},
                        'month': {'$month': '$created_at'},
                        'day': {'$dayOfMonth': '$created_at'}
                    },
                    'daily_revenue': {'$sum': '$total_amount'},
                    'daily_paid': {'$sum': '$paid_amount'},
                    'invoice_count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]
            
            daily_data = list(self.db_manager.collections['invoices'].aggregate(pipeline))
            
            return {
                'daily_trends': daily_data,
                'period_days': period_days,
                'total_days': len(daily_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting revenue trends: {e}")
            return {}
    
    def get_customer_analytics(self, user_id: str) -> Dict:
        """Get customer-based analytics"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'collections'):
                return {}
            
            # Customer aggregation
            pipeline = [
                {'$match': {'user_id': user_id}},
                {'$group': {
                    '_id': '$customer_id',
                    'total_invoices': {'$sum': 1},
                    'total_amount': {'$sum': '$total_amount'},
                    'paid_amount': {'$sum': '$paid_amount'},
                    'avg_invoice_amount': {'$avg': '$total_amount'},
                    'first_invoice': {'$min': '$created_at'},
                    'last_invoice': {'$max': '$created_at'}
                }},
                {'$sort': {'total_amount': -1}},
                {'$limit': 10}
            ]
            
            customer_data = list(self.db_manager.collections['invoices'].aggregate(pipeline))
            
            return {
                'top_customers': customer_data,
                'total_unique_customers': len(customer_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting customer analytics: {e}")
            return {}
    
    def _empty_stats(self) -> Dict:
        """Return empty statistics"""
        return {
            'total_invoices': 0,
            'total_amount': 0,
            'paid_amount': 0,
            'outstanding_amount': 0,
            'avg_invoice_amount': 0,
            'draft_count': 0,
            'sent_count': 0,
            'paid_count': 0,
            'overdue_count': 0,
            'payment_rate': 0,
            'overdue_rate': 0
        }