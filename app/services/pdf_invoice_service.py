import logging
import io
import os
from typing import Optional, Dict, Any
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from ..models.invoice_models import Invoice, Customer, InvoiceItem

class PDFInvoiceService:
    """Service for generating professional PDF invoices"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_LEFT
        )
        
        # Header style
        self.header_style = ParagraphStyle(
            'Header',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Subheader style
        self.subheader_style = ParagraphStyle(
            'SubHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#7F8C8D'),
            spaceAfter=6
        )
        
        # Body style
        self.body_style = ParagraphStyle(
            'Body',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=6
        )
        
        # Address style
        self.address_style = ParagraphStyle(
            'Address',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=3
        )
        
        # Right aligned style
        self.right_style = ParagraphStyle(
            'Right',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT
        )
        
        # Center aligned style
        self.center_style = ParagraphStyle(
            'Center',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER
        )
    
    def generate_invoice_pdf(self, invoice: Invoice, company_info: Dict = None, logo_path: str = None) -> bytes:
        """Generate PDF invoice and return as bytes"""
        try:
            # Create a BytesIO buffer to hold the PDF
            buffer = io.BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=1*inch,
                bottomMargin=1*inch
            )
            
            # Build the PDF content
            story = []
            
            # Add header with logo and company info
            story.extend(self._build_header(company_info, logo_path))
            
            # Add invoice title and details
            story.extend(self._build_invoice_details(invoice))
            
            # Add customer information
            story.extend(self._build_customer_info(invoice.customer))
            
            # Add invoice items table
            story.extend(self._build_items_table(invoice.items))
            
            # Add totals section
            story.extend(self._build_totals_section(invoice))
            
            # Add notes and terms
            story.extend(self._build_notes_and_terms(invoice))
            
            # Add payment information
            story.extend(self._build_payment_info(invoice))
            
            # Build the PDF
            doc.build(story)
            
            # Get the PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            self.logger.info(f"PDF generated for invoice {invoice.invoice_number}")
            return pdf_bytes
            
        except Exception as e:
            self.logger.error(f"Error generating PDF: {e}")
            return b""
    
    def _build_header(self, company_info: Dict = None, logo_path: str = None):
        """Build the invoice header"""
        elements = []
        
        # Create header table for logo and company info
        header_data = []
        
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=2*inch, height=1*inch)
                company_cell = []
            except:
                logo = ""
                company_cell = []
        else:
            logo = ""
            company_cell = []
        
        # Company information
        if company_info:
            company_lines = [
                Paragraph(f"<b>{company_info.get('name', 'Your Company')}</b>", self.header_style)
            ]
            
            if company_info.get('address'):
                company_lines.append(Paragraph(company_info['address'], self.address_style))
            if company_info.get('city'):
                city_line = company_info['city']
                if company_info.get('state'):
                    city_line += f", {company_info['state']}"
                if company_info.get('zip'):
                    city_line += f" {company_info['zip']}"
                company_lines.append(Paragraph(city_line, self.address_style))
            
            if company_info.get('phone'):
                company_lines.append(Paragraph(f"Phone: {company_info['phone']}", self.address_style))
            if company_info.get('email'):
                company_lines.append(Paragraph(f"Email: {company_info['email']}", self.address_style))
            if company_info.get('website'):
                company_lines.append(Paragraph(f"Website: {company_info['website']}", self.address_style))
            
            company_cell = company_lines
        else:
            company_cell = [Paragraph("<b>Your Business Name</b>", self.header_style)]
        
        if logo:
            header_data.append([logo, company_cell])
            col_widths = [2.5*inch, 4*inch]
        else:
            header_data.append([company_cell])
            col_widths = [6.5*inch]
        
        header_table = Table(header_data, colWidths=col_widths)
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT') if logo else ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.5*inch))
        
        return elements
    
    def _build_invoice_details(self, invoice: Invoice):
        """Build invoice details section"""
        elements = []
        
        # Invoice title and number
        elements.append(Paragraph("INVOICE", self.title_style))
        
        # Invoice details table
        details_data = [
            ["Invoice Number:", invoice.invoice_number or "INV-001"],
            ["Issue Date:", invoice.issue_date.strftime("%B %d, %Y")],
            ["Due Date:", invoice.due_date.strftime("%B %d, %Y")],
            ["Status:", invoice.status.value.title()],
        ]
        
        if invoice.payment_status:
            details_data.append(["Payment Status:", invoice.payment_status.value.title()])
        
        details_table = Table(details_data, colWidths=[1.5*inch, 2*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(details_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_customer_info(self, customer: Customer):
        """Build customer information section"""
        elements = []
        
        if not customer:
            return elements
        
        elements.append(Paragraph("Bill To:", self.header_style))
        
        # Customer details
        customer_lines = []
        if customer.name:
            customer_lines.append(Paragraph(f"<b>{customer.name}</b>", self.body_style))
        if customer.company:
            customer_lines.append(Paragraph(customer.company, self.body_style))
        
        # Billing address
        if customer.billing_address:
            addr = customer.billing_address
            if addr.street:
                customer_lines.append(Paragraph(addr.street, self.address_style))
            
            city_line = ""
            if addr.city:
                city_line = addr.city
            if addr.state:
                city_line += f", {addr.state}" if city_line else addr.state
            if addr.postal_code:
                city_line += f" {addr.postal_code}" if city_line else addr.postal_code
            if city_line:
                customer_lines.append(Paragraph(city_line, self.address_style))
            
            if addr.country:
                customer_lines.append(Paragraph(addr.country, self.address_style))
        
        if customer.email:
            customer_lines.append(Paragraph(f"Email: {customer.email}", self.address_style))
        if customer.phone:
            customer_lines.append(Paragraph(f"Phone: {customer.phone}", self.address_style))
        
        for line in customer_lines:
            elements.append(line)
        
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_items_table(self, items: list):
        """Build invoice items table"""
        elements = []
        
        if not items:
            return elements
        
        # Table headers
        headers = ["Description", "Qty", "Unit Price", "Discount", "Tax", "Total"]
        table_data = [headers]
        
        # Add items
        for item in items:
            row = [
                item.description,
                f"{item.quantity:,.2f}",
                f"${item.unit_price:,.2f}",
                f"{item.discount}%" if item.discount > 0 else "-",
                f"{item.tax_rate}%" if item.tax_rate > 0 else "-",
                f"${item.total:,.2f}"
            ]
            table_data.append(row)
        
        # Create table
        items_table = Table(table_data, colWidths=[2.5*inch, 0.6*inch, 0.8*inch, 0.7*inch, 0.5*inch, 0.8*inch])
        
        # Table styling
        items_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Description left
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Numbers right
            
            # Grid and padding
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_totals_section(self, invoice: Invoice):
        """Build totals section"""
        elements = []
        
        # Create totals table (right-aligned)
        totals_data = []
        
        if invoice.subtotal > 0:
            totals_data.append(["Subtotal:", f"${invoice.subtotal:,.2f}"])
        
        if invoice.total_discount > 0:
            totals_data.append(["Total Discount:", f"-${invoice.total_discount:,.2f}"])
        
        if invoice.total_tax > 0:
            totals_data.append(["Total Tax:", f"${invoice.total_tax:,.2f}"])
        
        totals_data.append(["", ""])  # Spacer row
        totals_data.append(["Total Amount:", f"${invoice.total_amount:,.2f}"])
        
        if invoice.paid_amount > 0:
            totals_data.append(["Paid Amount:", f"${invoice.paid_amount:,.2f}"])
            if invoice.balance_due > 0:
                totals_data.append(["Balance Due:", f"${invoice.balance_due:,.2f}"])
        
        # Create table with specific positioning
        totals_table = Table(totals_data, colWidths=[1.5*inch, 1.2*inch])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -3), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, -3), 'Helvetica'),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -3), 10),
            ('FONTSIZE', (0, -2), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEABOVE', (0, -2), (-1, -2), 1, colors.black),
            ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#ECF0F1')),
        ]))
        
        # Add spacer and table
        elements.append(Spacer(1, 0.1*inch))
        
        # Create a container to right-align the totals table
        container_data = [["", totals_table]]
        container_table = Table(container_data, colWidths=[4.3*inch, 2.7*inch])
        container_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(container_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_notes_and_terms(self, invoice: Invoice):
        """Build notes and terms section"""
        elements = []
        
        if invoice.notes:
            elements.append(Paragraph("Notes:", self.header_style))
            elements.append(Paragraph(invoice.notes, self.body_style))
            elements.append(Spacer(1, 0.2*inch))
        
        if invoice.terms:
            elements.append(Paragraph("Terms & Conditions:", self.header_style))
            elements.append(Paragraph(invoice.terms, self.body_style))
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_payment_info(self, invoice: Invoice):
        """Build payment information section"""
        elements = []
        
        if invoice.payments:
            elements.append(Paragraph("Payment History:", self.header_style))
            
            payment_data = [["Date", "Amount", "Method", "Transaction ID"]]
            
            for payment in invoice.payments:
                payment_data.append([
                    payment.payment_date.strftime("%m/%d/%Y"),
                    f"${payment.amount:,.2f}",
                    payment.payment_method.title(),
                    payment.transaction_id or "-"
                ])
            
            payment_table = Table(payment_data, colWidths=[1.2*inch, 1*inch, 1.2*inch, 1.5*inch])
            payment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('ALIGN', (2, 1), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            elements.append(payment_table)
        
        return elements
    
    def save_invoice_pdf(self, invoice: Invoice, file_path: str, company_info: Dict = None, logo_path: str = None) -> bool:
        """Save invoice PDF to file"""
        try:
            pdf_bytes = self.generate_invoice_pdf(invoice, company_info, logo_path)
            
            if pdf_bytes:
                with open(file_path, 'wb') as f:
                    f.write(pdf_bytes)
                self.logger.info(f"Invoice PDF saved to {file_path}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error saving PDF: {e}")
            return False

# Initialize service instance
pdf_invoice_service = PDFInvoiceService()