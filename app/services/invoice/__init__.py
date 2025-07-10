"""
Invoice Management Module

This module provides modular invoice management capabilities:
- Core CRUD operations
- Query and search functionality  
- Payment processing
- Analytics and reporting
- Recurring invoice automation
"""

from .invoice_core import InvoiceCoreService
from .invoice_query import InvoiceQueryService
from .payment_service import PaymentService
from .invoice_analytics import InvoiceAnalytics
from .recurring_service import RecurringInvoiceService

__all__ = [
    'InvoiceCoreService',
    'InvoiceQueryService', 
    'PaymentService',
    'InvoiceAnalytics',
    'RecurringInvoiceService'
]