from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class Token(BaseModel):
    balance: Decimal
    balance_usd: Decimal
    price: Decimal
    symbol: str


class Pair(BaseModel):
    balance_usd: Decimal
    contract_address: str
    owner_balance: Decimal
    pair_symbol: str
    share: Decimal
    staking_contract_address: Optional[str] = None
    token_price: Decimal
    tokens: List[Token] = []


class Portfolio(BaseModel):
    address: str
    balance_usd: Decimal
    pairs: List[Pair] = []
