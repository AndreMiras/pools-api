from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    balance: Decimal
    balance_usd: Decimal
    price_usd: Decimal
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
    symbol: str
    share: Decimal
    staking_contract_address: Optional[str] = None
    price_usd: Decimal
    tokens: list[Token] = []
    total_supply: Decimal
    transactions: list[Transaction] = []


class PairsPair(BaseModel):
    id: str
    symbol: str
    price_usd: Decimal
    total_supply: Decimal
    reserve_usd: Decimal


class Pairs(BaseModel):
    __root__: list[PairsPair] = []


class Portfolio(BaseModel):
    address: str
    balance_usd: Decimal
    pairs: list[Pair] = []


class DatePrice(BaseModel):
    date: datetime
    price_usd: Decimal


class DatePriceList(BaseModel):
    __root__: list[DatePrice] = []


class PairsDailyPair(BaseModel):
    price_usd: Decimal
    reserve_usd: Decimal
    symbol: str
    # TODO token0 & token1, but should actually be tokens [], to be fixed in lib
    total_supply: Decimal


class PairsDaily(BaseModel):
    pair: PairsDailyPair
    date_price: DatePriceList
