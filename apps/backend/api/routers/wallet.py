"""Wallet endpoints (virtual portfolio)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
import math

from db.session import get_db
from db.models.user import User
from core.dependencies import get_current_active_user
from schemas.wallet import WalletSummaryResponse, WalletCreditRequest
from services.wallet_service import get_wallet_totals, credit_wallet

router = APIRouter(prefix="/api/v1/wallet", tags=["wallet"])

TEST_TOPUP_EMAIL = "r.amoroso80@gmail.com"

@router.get("/summary", response_model=WalletSummaryResponse)
async def wallet_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    balance, total_loaded, total_spent = get_wallet_totals(db, current_user.id)
    return WalletSummaryResponse(
        balance=float(balance),
        total_loaded=float(total_loaded),
        total_spent=float(total_spent),
        currency="EUR",
    )


@router.post("/credit", response_model=WalletSummaryResponse, status_code=status.HTTP_201_CREATED)
async def wallet_credit(
    payload: WalletCreditRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Credit wallet (temporary endpoint).
    In production this should be done only after payment provider confirms the top-up.
    """
    if (current_user.email or "").lower() != TEST_TOPUP_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ricarica manuale disponibile solo per l'utente di test. Per gli altri utenti è richiesto un pagamento reale.",
        )
    if not math.isfinite(payload.amount) or payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Importo non valido")
    try:
        credit_wallet(db, current_user.id, Decimal(str(payload.amount)), payload.description)
        balance, total_loaded, total_spent = get_wallet_totals(db, current_user.id)
        return WalletSummaryResponse(
            balance=float(balance),
            total_loaded=float(total_loaded),
            total_spent=float(total_spent),
            currency="EUR",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

