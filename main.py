from fastapi import FastAPI
from fastapi.responses import RedirectResponse

import experiment

app = FastAPI()


@app.get("/")
def read_root():
    return RedirectResponse(app.redoc_url)


@app.get("/portfolio/{address}")
def portfolio(address: str):
    data = experiment.portfolio(address)
    return data
