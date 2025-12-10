from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Enum, func
from sqlalchemy.orm import relationship
import enum
from .db import Base

class AccountStatus(str, enum.Enum):
    active = "active"
    frozen = "frozen"

class TransactionType(str, enum.Enum):
    transfer = "transfer"
    deposit = "deposit"
    withdrawal = "withdrawal"

class TransactionStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class EntryType(str, enum.Enum):
    debit = "debit"
    credit = "credit"

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    account_type = Column(String, nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(Enum(AccountStatus), default=AccountStatus.active, nullable=False)

    ledger_entries = relationship("LedgerEntry", back_populates="account", order_by="LedgerEntry.timestamp")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(20,8), nullable=False)
    currency = Column(String(3), nullable=False)
    source_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    destination_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.pending, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    entry_type = Column(Enum(EntryType), nullable=False)
    amount = Column(Numeric(20,8), nullable=False)
    currency = Column(String(3), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="ledger_entries")
