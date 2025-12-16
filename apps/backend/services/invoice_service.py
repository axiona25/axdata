"""Invoice generation service."""
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.models.invoice import Invoice, InvoiceStatus
from db.models.payment import Payment
from db.models.user import User, UserProfile
from db.models.dataset import DatasetRequest
from services.storage_service import save_to_storage, s3_client
from core.config import settings

logger = logging.getLogger(__name__)


def generate_invoice_number(db: Session, invoice_date: date = None) -> str:
    """
    Generate sequential invoice number.
    
    Format: INV-YYYY-NNNN
    
    Args:
        db: Database session
        invoice_date: Invoice date (default: today)
    
    Returns:
        Invoice number string
    """
    if not invoice_date:
        invoice_date = date.today()
    
    year = invoice_date.year
    
    # Get last invoice number for this year
    last_invoice = db.query(Invoice).filter(
        func.extract('year', Invoice.invoice_date) == year
    ).order_by(Invoice.invoice_number.desc()).first()
    
    if last_invoice:
        # Extract number from last invoice
        try:
            parts = last_invoice.invoice_number.split('-')
            if len(parts) == 3 and parts[0] == 'INV' and parts[1] == str(year):
                last_num = int(parts[2])
                next_num = last_num + 1
            else:
                next_num = 1
        except:
            next_num = 1
    else:
        next_num = 1
    
    invoice_number = f"INV-{year}-{next_num:04d}"
    return invoice_number


def generate_invoice_pdf(
    invoice: Invoice,
    user: User,
    user_profile: UserProfile,
    dataset: Optional[DatasetRequest] = None,
    package_name: Optional[str] = None
) -> bytes:
    """
    Generate invoice PDF.
    
    Args:
        invoice: Invoice object
        user: User object
        user_profile: UserProfile object
        dataset: DatasetRequest object (for dataset payments)
        package_name: Package name (for package payments)
    
    Returns:
        PDF data as bytes
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from io import BytesIO
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50*mm, height - 50*mm, "FATTURA / INVOICE")
        
        # Invoice number and date
        c.setFont("Helvetica", 10)
        c.drawString(50*mm, height - 65*mm, f"Invoice Number: {invoice.invoice_number}")
        c.drawString(50*mm, height - 75*mm, f"Date: {invoice.invoice_date.strftime('%d/%m/%Y')}")
        
        # Company info (placeholder)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50*mm, height - 100*mm, "Dataset Portal")
        c.setFont("Helvetica", 10)
        c.drawString(50*mm, height - 110*mm, "VAT: IT12345678901")
        c.drawString(50*mm, height - 120*mm, "Email: info@datasetportal.com")
        
        # Customer info
        y_pos = height - 150*mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50*mm, y_pos, "Bill To:")
        c.setFont("Helvetica", 10)
        y_pos -= 10*mm
        c.drawString(50*mm, y_pos, f"{user_profile.first_name or ''} {user_profile.last_name or ''}".strip() or user.email)
        c.drawString(50*mm, y_pos - 10*mm, user.email)
        if user_profile.organization:
            c.drawString(50*mm, y_pos - 20*mm, user_profile.organization)
        
        # Line items
        y_pos = height - 220*mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50*mm, y_pos, "Description")
        c.drawString(150*mm, y_pos, "Amount")
        
        y_pos -= 15*mm
        c.setFont("Helvetica", 10)
        if dataset:
            c.drawString(50*mm, y_pos, f"Dataset: {dataset.title}")
        elif package_name:
            c.drawString(50*mm, y_pos, f"Package: {package_name}")
        else:
            c.drawString(50*mm, y_pos, "Service Payment")
        c.drawString(150*mm, y_pos, f"€ {invoice.amount:.2f}")
        
        # Totals
        y_pos -= 30*mm
        if invoice.tax_amount:
            c.drawString(150*mm, y_pos, f"Tax: € {invoice.tax_amount:.2f}")
            y_pos -= 15*mm
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(150*mm, y_pos, f"Total: € {invoice.total_amount:.2f}")
        
        # Footer
        c.setFont("Helvetica", 8)
        c.drawString(50*mm, 30*mm, "Thank you for your business!")
        
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    except ImportError:
        # Fallback: simple text-based invoice if reportlab not available
        logger.warning("reportlab not available, using simple text invoice")
        description = "Service Payment"
        if dataset:
            description = f"Dataset - {dataset.title}"
        elif package_name:
            description = f"Package - {package_name}"
        
        invoice_text = f"""
INVOICE
Invoice Number: {invoice.invoice_number}
Date: {invoice.invoice_date}

Bill To:
{user.email}

Description: {description}
Amount: € {invoice.amount:.2f}
Total: € {invoice.total_amount:.2f}
"""
        return invoice_text.encode('utf-8')


def create_invoice_from_payment(
    db: Session,
    payment: Payment
) -> Invoice:
    """
    Create invoice from completed payment.
    
    Supports both:
    - Dataset payments (dataset_request_id set)
    - Package payments (user_package_id set, dataset_request_id is None)
    
    Args:
        db: Database session
        payment: Payment object
    
    Returns:
        Created Invoice
    """
    # Check if invoice already exists
    existing = db.query(Invoice).filter(Invoice.payment_id == payment.id).first()
    if existing:
        return existing
    
    # Get user
    user = db.query(User).filter(User.id == payment.user_id).first()
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == payment.user_id).first()
    
    # Get dataset or package info
    dataset = None
    package_name = None
    if payment.dataset_request_id:
        dataset = db.query(DatasetRequest).filter(DatasetRequest.id == payment.dataset_request_id).first()
    elif payment.user_package_id:
        from db.models.package import UserPackage
        user_package = db.query(UserPackage).filter(UserPackage.id == payment.user_package_id).first()
        if user_package:
            package_name = user_package.package.name
    
    # Generate invoice number
    invoice_number = generate_invoice_number(db)
    
    # Calculate amounts
    amount = payment.amount
    tax_amount = amount * Decimal("0.22")  # 22% VAT (configurable)
    total_amount = amount + tax_amount
    
    # Create invoice
    # Note: dataset_request_id can be None for package payments
    invoice = Invoice(
        invoice_number=invoice_number,
        user_id=payment.user_id,
        payment_id=payment.id,
        dataset_request_id=payment.dataset_request_id,  # Can be None for packages
        amount=amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        currency=payment.currency,
        invoice_date=date.today(),
        status=InvoiceStatus.ISSUED
    )
    db.add(invoice)
    db.flush()
    
    # Generate PDF
    pdf_data = generate_invoice_pdf(invoice, user, user_profile, dataset=dataset, package_name=package_name)
    
    # Save PDF to storage
    s3_key = f"invoices/{invoice.invoice_number}.pdf"
    save_to_storage(
        data=pdf_data,
        s3_key=s3_key,
        content_type="application/pdf"
    )
    
    invoice.storage_path = s3_key
    invoice.status = InvoiceStatus.PAID  # Mark as paid since payment is completed
    db.commit()
    db.refresh(invoice)
    
    logger.info(f"Created invoice {invoice.invoice_number} for payment {payment.id}")
    
    return invoice

