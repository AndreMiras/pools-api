import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

import experiment

app = FastAPI()
allow_origins = os.environ.get("ALLOW_ORIGINS", "[]")
app.add_middleware(CORSMiddleware, allow_origins=allow_origins)


@app.get("/")
def index():
    return RedirectResponse(app.redoc_url)


@app.get("/portfolio/{address}")
def portfolio(address: str):
    data = experiment.portfolio(address)
    return data
