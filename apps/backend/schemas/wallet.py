"""Wallet schemas."""
from pydantic import BaseModel, Field
from typing import Optional


class WalletSummaryResponse(BaseModel):
    balance: float
    total_loaded: float
    total_spent: float
    currency: str = "EUR"


class WalletCreditRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to credit to wallet")
    description: Optional[str] = None

