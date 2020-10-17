import os
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette import status

import experiment

app = FastAPI()
allow_origins = os.environ.get("ALLOW_ORIGINS", "[]")
app.add_middleware(CORSMiddleware, allow_origins=allow_origins)


@contextmanager
def exception_contextmanger():
    try:
        yield
    except experiment.InvalidAddressException as e:
        details = "Invalid address " + e.args[0]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=details)


@app.get("/")
def index():
    return RedirectResponse(app.redoc_url)


@app.get("/portfolio/{address}")
@exception_contextmanger()
def portfolio(address: str):
    data = experiment.portfolio(address)
    return data
