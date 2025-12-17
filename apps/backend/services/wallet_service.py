"""Wallet service (virtual portfolio)."""
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError, OperationalError
from decimal import Decimal
from uuid import UUID
from typing import Tuple

from db.models.wallet import WalletTransaction, WalletTxType, WalletTxStatus


def get_wallet_totals(db: Session, user_id: UUID) -> Tuple[Decimal, Decimal, Decimal]:
    """Return (balance, total_loaded, total_spent) for confirmed transactions."""
    try:
        txs = db.query(WalletTransaction).filter(
            WalletTransaction.user_id == user_id,
            WalletTransaction.status == WalletTxStatus.CONFIRMED,
        ).all()
    except (ProgrammingError, OperationalError):
        # DB not migrated yet (e.g. wallet_transactions missing) -> treat as empty wallet
        db.rollback()
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00")

    total_loaded = Decimal("0.00")
    total_spent = Decimal("0.00")

    for tx in txs:
        amt = Decimal(str(tx.amount))
        if tx.tx_type == WalletTxType.CREDIT:
            total_loaded += amt
        else:
            total_spent += amt

    balance = total_loaded - total_spent
    return balance, total_loaded, total_spent


def credit_wallet(db: Session, user_id: UUID, amount: Decimal, description: str = None) -> WalletTransaction:
    tx = WalletTransaction(
        user_id=user_id,
        tx_type=WalletTxType.CREDIT,
        status=WalletTxStatus.CONFIRMED,
        amount=amount,
        currency="EUR",
        description=description,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def debit_wallet(db: Session, user_id: UUID, amount: Decimal, description: str = None) -> WalletTransaction:
    balance, _, _ = get_wallet_totals(db, user_id)
    if balance < amount:
        raise ValueError("Insufficient wallet balance")

    tx = WalletTransaction(
        user_id=user_id,
        tx_type=WalletTxType.DEBIT,
        status=WalletTxStatus.CONFIRMED,
        amount=amount,
        currency="EUR",
        description=description,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

