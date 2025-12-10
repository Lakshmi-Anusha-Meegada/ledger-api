from sqlalchemy import select, func, case
from sqlalchemy.orm import Session
from . import models
from decimal import Decimal

def create_account(db: Session, user_id: str, account_type: str, currency: str):
    acct = models.Account(user_id=user_id, account_type=account_type, currency=currency)
    db.add(acct)
    db.flush()
    return acct

def get_account(db: Session, account_id: int):
    return db.get(models.Account, account_id)

def get_account_with_lock(db: Session, account_id: int):
    stmt = select(models.Account).where(models.Account.id == account_id).with_for_update()
    return db.execute(stmt).scalars().first()

def ledger_entries_for_account(db: Session, account_id: int):
    stmt = select(models.LedgerEntry).where(models.LedgerEntry.account_id == account_id).order_by(models.LedgerEntry.timestamp)
    return db.execute(stmt).scalars().all()

def get_account_balance(db: Session, account_id: int):
    stmt = select(
        func.coalesce(func.sum(
            case(
                (models.LedgerEntry.entry_type == models.EntryType.credit, models.LedgerEntry.amount),
                else_=-models.LedgerEntry.amount
            )
        ), 0)
    ).where(models.LedgerEntry.account_id == account_id)

    result = db.execute(stmt).scalar_one()
    return Decimal(result or 0)