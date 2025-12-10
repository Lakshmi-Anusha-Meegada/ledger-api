from pydantic import BaseModel, condecimal, constr
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

Money = condecimal(max_digits=20, decimal_places=8)

class AccountCreate(BaseModel):
    user_id: str
    account_type: str
    currency: constr(min_length=3, max_length=3)

class AccountOut(BaseModel):
    id: int
    user_id: str
    account_type: str
    currency: str
    status: str
    balance: Decimal

    class Config:
        orm_mode = True

class LedgerEntryOut(BaseModel):
    id: int
    account_id: int
    transaction_id: int
    entry_type: str
    amount: Decimal
    currency: str
    timestamp: datetime

    class Config:
        orm_mode = True

class TransactionCreate(BaseModel):
    type: str
    amount: Money
    currency: constr(min_length=3, max_length=3)
    source_account_id: Optional[int] = None
    destination_account_id: Optional[int] = None
    description: Optional[str] = None

class TransactionOut(BaseModel):
    id: int
    type: str
    amount: Decimal
    currency: str
    status: str
    description: Optional[str]

    class Config:
        orm_mode = True