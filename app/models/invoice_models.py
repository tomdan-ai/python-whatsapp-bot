from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid

class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PaymentStatus(Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    REFUNDED = "refunded"

class RecurrenceType(Enum):
    NONE = "none"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"

@dataclass
class Address:
    """Address data structure"""
    street: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Address':
        return cls(
            street=data.get("street", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            postal_code=data.get("postal_code", ""),
            country=data.get("country", "")
        )

@dataclass
class Customer:
    """Customer data structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    billing_address: Address = field(default_factory=Address)
    shipping_address: Optional[Address] = None
    tax_id: str = ""
    payment_terms: int = 30  # days
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "billing_address": self.billing_address.to_dict(),
            "shipping_address": self.shipping_address.to_dict() if self.shipping_address else None,
            "tax_id": self.tax_id,
            "payment_terms": self.payment_terms,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Customer':
        customer = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            company=data.get("company", ""),
            billing_address=Address.from_dict(data.get("billing_address", {})),
            tax_id=data.get("tax_id", ""),
            payment_terms=data.get("payment_terms", 30),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow())
        )
        
        if data.get("shipping_address"):
            customer.shipping_address = Address.from_dict(data["shipping_address"])
            
        return customer

@dataclass
class InvoiceItem:
    """Invoice item data structure"""
    description: str = ""
    quantity: float = 1.0
    unit_price: float = 0.0
    tax_rate: float = 0.0  # percentage
    discount: float = 0.0  # percentage
    
    @property
    def subtotal(self) -> float:
        """Calculate subtotal before tax and discount"""
        return self.quantity * self.unit_price
    
    @property
    def discount_amount(self) -> float:
        """Calculate discount amount"""
        return self.subtotal * (self.discount / 100)
    
    @property
    def discounted_subtotal(self) -> float:
        """Calculate subtotal after discount"""
        return self.subtotal - self.discount_amount
    
    @property
    def tax_amount(self) -> float:
        """Calculate tax amount"""
        return self.discounted_subtotal * (self.tax_rate / 100)
    
    @property
    def total(self) -> float:
        """Calculate total amount including tax"""
        return self.discounted_subtotal + self.tax_amount
    
    def to_dict(self) -> Dict:
        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "tax_rate": self.tax_rate,
            "discount": self.discount,
            "subtotal": self.subtotal,
            "discount_amount": self.discount_amount,
            "discounted_subtotal": self.discounted_subtotal,
            "tax_amount": self.tax_amount,
            "total": self.total
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InvoiceItem':
        return cls(
            description=data.get("description", ""),
            quantity=data.get("quantity", 1.0),
            unit_price=data.get("unit_price", 0.0),
            tax_rate=data.get("tax_rate", 0.0),
            discount=data.get("discount", 0.0)
        )

@dataclass
class Payment:
    """Payment record data structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    amount: float = 0.0
    payment_date: datetime = field(default_factory=datetime.utcnow)
    payment_method: str = ""  # cash, bank_transfer, credit_card, etc.
    transaction_id: str = ""
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "amount": self.amount,
            "payment_date": self.payment_date,
            "payment_method": self.payment_method,
            "transaction_id": self.transaction_id,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Payment':
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            amount=data.get("amount", 0.0),
            payment_date=data.get("payment_date", datetime.utcnow()),
            payment_method=data.get("payment_method", ""),
            transaction_id=data.get("transaction_id", ""),
            notes=data.get("notes", "")
        )

@dataclass
class Invoice:
    """Invoice data structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str = ""
    customer_id: str = ""
    customer: Optional[Customer] = None
    items: List[InvoiceItem] = field(default_factory=list)
    
    # Dates
    issue_date: datetime = field(default_factory=datetime.utcnow)
    due_date: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))
    
    # Status
    status: InvoiceStatus = InvoiceStatus.DRAFT
    payment_status: PaymentStatus = PaymentStatus.PENDING
    
    # Financial
    subtotal: float = 0.0
    total_tax: float = 0.0
    total_discount: float = 0.0
    total_amount: float = 0.0
    paid_amount: float = 0.0
    
    # Additional fields
    notes: str = ""
    terms: str = ""
    currency: str = "USD"
    
    # Payments
    payments: List[Payment] = field(default_factory=list)
    
    # Recurrence
    is_recurring: bool = False
    recurrence_type: RecurrenceType = RecurrenceType.NONE
    recurrence_end_date: Optional[datetime] = None
    next_invoice_date: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    
    def calculate_totals(self):
        """Calculate invoice totals from items"""
        self.subtotal = sum(item.subtotal for item in self.items)
        self.total_discount = sum(item.discount_amount for item in self.items)
        self.total_tax = sum(item.tax_amount for item in self.items)
        self.total_amount = sum(item.total for item in self.items)
        
        # Update payment status based on paid amount
        if self.paid_amount == 0:
            self.payment_status = PaymentStatus.PENDING
        elif self.paid_amount >= self.total_amount:
            self.payment_status = PaymentStatus.PAID
        else:
            self.payment_status = PaymentStatus.PARTIAL
    
    @property
    def balance_due(self) -> float:
        """Calculate remaining balance"""
        return max(0, self.total_amount - self.paid_amount)
    
    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        return (self.due_date < datetime.utcnow() and 
                self.payment_status != PaymentStatus.PAID and 
                self.status != InvoiceStatus.CANCELLED)
    
    def add_payment(self, payment: Payment):
        """Add a payment to the invoice"""
        self.payments.append(payment)
        self.paid_amount = sum(p.amount for p in self.payments)
        self.calculate_totals()
        
        if self.payment_status == PaymentStatus.PAID:
            self.status = InvoiceStatus.PAID
    
    def generate_next_invoice_date(self):
        """Generate next invoice date for recurring invoices"""
        if not self.is_recurring or self.recurrence_type == RecurrenceType.NONE:
            return
        
        base_date = self.next_invoice_date or self.due_date
        
        if self.recurrence_type == RecurrenceType.WEEKLY:
            self.next_invoice_date = base_date + timedelta(weeks=1)
        elif self.recurrence_type == RecurrenceType.MONTHLY:
            # Add one month (approximate)
            if base_date.month == 12:
                self.next_invoice_date = base_date.replace(year=base_date.year + 1, month=1)
            else:
                self.next_invoice_date = base_date.replace(month=base_date.month + 1)
        elif self.recurrence_type == RecurrenceType.QUARTERLY:
            # Add three months
            month = base_date.month + 3
            year = base_date.year
            if month > 12:
                month -= 12
                year += 1
            self.next_invoice_date = base_date.replace(year=year, month=month)
        elif self.recurrence_type == RecurrenceType.ANNUALLY:
            self.next_invoice_date = base_date.replace(year=base_date.year + 1)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "customer_id": self.customer_id,
            "customer": self.customer.to_dict() if self.customer else None,
            "items": [item.to_dict() for item in self.items],
            "issue_date": self.issue_date,
            "due_date": self.due_date,
            "status": self.status.value,
            "payment_status": self.payment_status.value,
            "subtotal": self.subtotal,
            "total_tax": self.total_tax,
            "total_discount": self.total_discount,
            "total_amount": self.total_amount,
            "paid_amount": self.paid_amount,
            "balance_due": self.balance_due,
            "notes": self.notes,
            "terms": self.terms,
            "currency": self.currency,
            "payments": [payment.to_dict() for payment in self.payments],
            "is_recurring": self.is_recurring,
            "recurrence_type": self.recurrence_type.value,
            "recurrence_end_date": self.recurrence_end_date,
            "next_invoice_date": self.next_invoice_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "sent_at": self.sent_at,
            "viewed_at": self.viewed_at,
            "is_overdue": self.is_overdue
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Invoice':
        invoice = cls(
            id=data.get("id", str(uuid.uuid4())),
            invoice_number=data.get("invoice_number", ""),
            customer_id=data.get("customer_id", ""),
            issue_date=data.get("issue_date", datetime.utcnow()),
            due_date=data.get("due_date", datetime.utcnow() + timedelta(days=30)),
            status=InvoiceStatus(data.get("status", "draft")),
            payment_status=PaymentStatus(data.get("payment_status", "pending")),
            subtotal=data.get("subtotal", 0.0),
            total_tax=data.get("total_tax", 0.0),
            total_discount=data.get("total_discount", 0.0),
            total_amount=data.get("total_amount", 0.0),
            paid_amount=data.get("paid_amount", 0.0),
            notes=data.get("notes", ""),
            terms=data.get("terms", ""),
            currency=data.get("currency", "USD"),
            is_recurring=data.get("is_recurring", False),
            recurrence_type=RecurrenceType(data.get("recurrence_type", "none")),
            recurrence_end_date=data.get("recurrence_end_date"),
            next_invoice_date=data.get("next_invoice_date"),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            sent_at=data.get("sent_at"),
            viewed_at=data.get("viewed_at")
        )
        
        # Load items
        if data.get("items"):
            invoice.items = [InvoiceItem.from_dict(item) for item in data["items"]]
        
        # Load customer
        if data.get("customer"):
            invoice.customer = Customer.from_dict(data["customer"])
        
        # Load payments
        if data.get("payments"):
            invoice.payments = [Payment.from_dict(payment) for payment in data["payments"]]
        
        return invoice

@dataclass
class InvoiceTemplate:
    """Invoice template for recurring invoices"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    customer_id: str = ""
    items: List[InvoiceItem] = field(default_factory=list)
    notes: str = ""
    terms: str = ""
    recurrence_type: RecurrenceType = RecurrenceType.MONTHLY
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "customer_id": self.customer_id,
            "items": [item.to_dict() for item in self.items],
            "notes": self.notes,
            "terms": self.terms,
            "recurrence_type": self.recurrence_type.value,
            "is_active": self.is_active,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InvoiceTemplate':
        template = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            customer_id=data.get("customer_id", ""),
            notes=data.get("notes", ""),
            terms=data.get("terms", ""),
            recurrence_type=RecurrenceType(data.get("recurrence_type", "monthly")),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", datetime.utcnow())
        )
        
        if data.get("items"):
            template.items = [InvoiceItem.from_dict(item) for item in data["items"]]
            
        return template