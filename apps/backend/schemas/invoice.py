"""Invoice schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


class InvoiceResponse(BaseModel):
    """Invoice response."""
    id: str
    invoice_number: str
    user_id: str
    payment_id: str
    dataset_request_id: str
    amount: str
    tax_amount: Optional[str]
    total_amount: str
    currency: str
    invoice_date: date
    due_date: Optional[date]
    status: str
    storage_path: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """List of invoices."""
    invoices: list[InvoiceResponse]
    total: int

