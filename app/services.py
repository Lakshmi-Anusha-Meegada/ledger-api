from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from decimal import Decimal
from . import models, crud

# -----------------------------------------
# Create a transaction record (pending)
# -----------------------------------------
def create_transaction_record(
    db: Session,
    tx_type: models.TransactionType,
    amount: Decimal,
    currency: str,
    src_id: int = None,
    dst_id: int = None,
    description: str = None
):
    tx = models.Transaction(
        type=tx_type,
        amount=amount,
        currency=currency,
        source_account_id=src_id,
        destination_account_id=dst_id,
        description=description
    )
    db.add(tx)
    db.flush()   # assigns transaction.id
    return tx

# -----------------------------------------
# Create a single ledger entry (immutable)
# -----------------------------------------
def create_ledger_entry(
    db: Session,
    account_id: int,
    tx_id: int,
    entry_type: models.EntryType,
    amount: Decimal,
    currency: str
):
    entry = models.LedgerEntry(
        account_id=account_id,
        transaction_id=tx_id,
        entry_type=entry_type,
        amount=amount,
        currency=currency
    )
    db.add(entry)
    return entry

# -----------------------------------------
# TRANSFER MONEY (double-entry)
# -----------------------------------------
def do_transfer(
    db: Session,
    amount: Decimal,
    currency: str,
    source_account_id: int,
    destination_account_id: int,
    description: str = None
):
    # Prevent sending to same account
    if source_account_id == destination_account_id:
        raise HTTPException(status_code=400, detail="Source and destination must differ")

    # Lock accounts (sorted to avoid deadlocks)
    ids = sorted([source_account_id, destination_account_id])
    accounts = {}

    for aid in ids:
        acct = crud.get_account_with_lock(db, aid)
        if not acct:
            raise HTTPException(status_code=404, detail=f"Account {aid} not found")
        if acct.status != models.AccountStatus.active:
            raise HTTPException(status_code=422, detail=f"Account {aid} not active")
        accounts[aid] = acct

    # Ensure same currency
    if accounts[source_account_id].currency != currency or accounts[destination_account_id].currency != currency:
        raise HTTPException(status_code=422, detail="Currency mismatch")

    # Create transaction record (status = pending)
    tx = create_transaction_record(
        db,
        models.TransactionType.transfer,
        amount,
        currency,
        src_id=source_account_id,
        dst_id=destination_account_id,
        description=description
    )

    # Check balance of source account
    source_balance = crud.get_account_balance(db, source_account_id)
    new_balance = source_balance - amount

    if new_balance < Decimal("0"):
        tx.status = models.TransactionStatus.failed
        db.flush()
        raise HTTPException(status_code=422, detail="Insufficient funds")

    # Double-entry
    create_ledger_entry(db, source_account_id, tx.id, models.EntryType.debit, amount, currency)
    create_ledger_entry(db, destination_account_id, tx.id, models.EntryType.credit, amount, currency)

    # Mark successful
    tx.status = models.TransactionStatus.completed
    db.flush()
    return tx

# -----------------------------------------
# DEPOSIT MONEY (credit)
# -----------------------------------------
def do_deposit(
    db: Session,
    amount: Decimal,
    currency: str,
    destination_account_id: int,
    description: str = None
):
    acct = crud.get_account_with_lock(db, destination_account_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found")

    if acct.status != models.AccountStatus.active:
        raise HTTPException(status_code=422, detail="Account not active")

    if acct.currency != currency:
        raise HTTPException(status_code=422, detail="Currency mismatch")

    # Create transaction
    tx = create_transaction_record(
        db,
        models.TransactionType.deposit,
        amount,
        currency,
        src_id=None,
        dst_id=destination_account_id,
        description=description
    )

    # Ledger entry (credit)
    create_ledger_entry(db, destination_account_id, tx.id, models.EntryType.credit, amount, currency)

    tx.status = models.TransactionStatus.completed
    db.flush()
    return tx

# -----------------------------------------
# WITHDRAW MONEY (debit)
# -----------------------------------------
def do_withdrawal(
    db: Session,
    amount: Decimal,
    currency: str,
    source_account_id: int,
    description: str = None
):
    acct = crud.get_account_with_lock(db, source_account_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found")

    if acct.status != models.AccountStatus.active:
        raise HTTPException(status_code=422, detail="Account not active")

    if acct.currency != currency:
        raise HTTPException(status_code=422, detail="Currency mismatch")

    # Create transaction
    tx = create_transaction_record(
        db,
        models.TransactionType.withdrawal,
        amount,
        currency,
        src_id=source_account_id,
        dst_id=None,
        description=description
    )

    # Check sufficient balance
    balance = crud.get_account_balance(db, source_account_id)
    if balance - amount < Decimal("0"):
        tx.status = models.TransactionStatus.failed
        db.flush()
        raise HTTPException(status_code=422, detail="Insufficient funds")

    # Ledger entry (debit)
    create_ledger_entry(db, source_account_id, tx.id, models.EntryType.debit, amount, currency)

    tx.status = models.TransactionStatus.completed
    db.flush()
    return tx
