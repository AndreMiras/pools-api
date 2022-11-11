import os
from contextlib import contextmanager

import sentry_sdk
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pools import uniswap
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette import status

from src.response_models import DatePriceList, Pairs, PairsDaily, Portfolio

app = FastAPI(title="Pools API", description="Liquidity Provider stats web API")
if SENTRY_DSN := os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(dsn=SENTRY_DSN)
    app.add_middleware(SentryAsgiMiddleware)
allow_origins = os.environ.get("ALLOW_ORIGINS", "[]")
app.add_middleware(CORSMiddleware, allow_origins=allow_origins)


@contextmanager
def exception_contextmanger():
    try:
        yield
    except uniswap.InvalidAddressException as e:
        details = "Invalid address " + e.args[0]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=details)
    except uniswap.TheGraphServiceDownException as e:
        details = "The Graph (thegraph.com) is down. " + e.args[0]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=details
        )


@app.get("/")
def index():
    return RedirectResponse(app.redoc_url)


@app.get("/portfolio/{address}", response_model=Portfolio)
@exception_contextmanger()
def portfolio(address: str):
    """Portfolio overview."""
    data = uniswap.portfolio(address)
    return data


@app.get("/tokens/{address}/daily", response_model=DatePriceList)
@exception_contextmanger()
def tokens_daily(address: str):
    """Tokens daily."""
    data = uniswap.get_token_daily(address)
    return data


@app.get("/pairs/{address}/daily", response_model=PairsDaily)
@exception_contextmanger()
def pairs_daily(address: str):
    """Pairs daily."""
    data = uniswap.get_pair_daily(address)
    return data


@app.get("/pairs", response_model=Pairs)
@exception_contextmanger()
def pairs():
    """Returns top pairs"""
    data = uniswap.get_pairs()
    return data
