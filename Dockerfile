# Docker image for installing dependencies & running tests.
# Build with:
# docker build --tag=andremiras/uniswap-roi .
# Run with:
# docker run andremiras/uniswap-roi /bin/sh -c 'echo TODO'
# Or for interactive shell:
# docker run -it --rm andremiras/uniswap-roi
FROM python:3.8

WORKDIR /app
COPY requirements.txt Makefile ./
RUN make venv
COPY . /app

CMD venv/bin/uvicorn main:app --host 0.0.0.0 --port $PORT
