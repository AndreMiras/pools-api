# Docker image for installing dependencies & running tests.
# Build with:
# docker build --tag=andremiras/uniswap-roi .
# Run with:
# docker run -it --rm --env PORT=8000 --publish 8000:8000 andremiras/uniswap-roi
# Or for interactive shell:
# docker run -it --rm andremiras/uniswap-roi bash
FROM python:3.9-slim

WORKDIR /app

RUN apt update -qq > /dev/null && apt --yes install --no-install-recommends \
    build-essential \
    make \
    && apt --yes autoremove && apt --yes clean
COPY requirements.txt Makefile ./
RUN make virtualenv
COPY . /app

CMD PYTHONPATH=src/ venv/bin/uvicorn main:app --host 0.0.0.0 --port $PORT
