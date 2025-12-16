"""Payment schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class PaymentCreate(BaseModel):
    """Create payment request."""
    dataset_request_id: str
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="eur", max_length=3)


class PaymentResponse(BaseModel):
    """Payment response."""
    id: str
    user_id: str
    dataset_request_id: Optional[str] = None  # Nullable for package payments
    user_package_id: Optional[str] = None  # For package payments
    amount: str
    currency: str
    status: str
    provider: str
    provider_checkout_session_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CheckoutResponse(BaseModel):
    """Stripe Checkout response."""
    checkout_url: str
    session_id: str


class WebhookEvent(BaseModel):
    """Stripe webhook event."""
    id: str
    type: str
    data: Dict[str, Any]

