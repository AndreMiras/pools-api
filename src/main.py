import os
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pools import uniswap
from starlette import status

app = FastAPI()
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


@app.get("/portfolio/{address}")
@exception_contextmanger()
def portfolio(address: str):
    data = uniswap.portfolio(address)
    return data
