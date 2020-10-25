from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class Token(BaseModel):
    balance: Decimal
    balance_usd: Decimal
    price: Decimal
    symbol: str


class TransactionPair(BaseModel):
    id: str


class TransactionTransaction(BaseModel):
    id: str
    block_number: int
    timestamp: datetime


class Transaction(BaseModel):
    amount0: Decimal
    amount1: Decimal
    amountUSD: Decimal
    liquidity: Decimal
    pair: TransactionPair
    sender: str
    to: str
    transaction: TransactionTransaction
    type: str


class Pair(BaseModel):
    balance_usd: Decimal
    contract_address: str
    owner_balance: Decimal
    pair_symbol: str
    share: Decimal
    staking_contract_address: Optional[str] = None
    token_price: Decimal
    tokens: List[Token] = []
    total_supply: Decimal
    transactions: List[Transaction] = []


class Portfolio(BaseModel):
    address: str
    balance_usd: Decimal
    pairs: List[Pair] = []


class TokenDaily(BaseModel):
    date: datetime
    price_usd: Decimal


class TokensDaily(BaseModel):
    __root__: List[TokenDaily] = []
