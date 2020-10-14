VIRTUAL_ENV ?= venv
PIP=$(VIRTUAL_ENV)/bin/pip
TOX=`which tox`
PYTHON=$(VIRTUAL_ENV)/bin/python
ISORT=$(VIRTUAL_ENV)/bin/isort
FLAKE8=$(VIRTUAL_ENV)/bin/flake8
BLACK=$(VIRTUAL_ENV)/bin/black
PYTEST=$(VIRTUAL_ENV)/bin/pytest
TWINE=$(VIRTUAL_ENV)/bin/twine
UVICORN=$(VIRTUAL_ENV)/bin/uvicorn
PYTHON_MAJOR_VERSION=3
PYTHON_MINOR_VERSION=8
PYTHON_VERSION=$(PYTHON_MAJOR_VERSION).$(PYTHON_MINOR_VERSION)
PYTHON_MAJOR_MINOR=$(PYTHON_MAJOR_VERSION)$(PYTHON_MINOR_VERSION)
PYTHON_WITH_VERSION=python$(PYTHON_VERSION)
SOURCES=experiment.py main.py
DOCKER_IMAGE=andremiras/uniswap-roi
DOCKER_COMMAND ?= /bin/bash
DOCKER_PORT=8000


$(VIRTUAL_ENV):
	$(PYTHON_WITH_VERSION) -m venv $(VIRTUAL_ENV)
	$(PIP) install -r requirements.txt

virtualenv: $(VIRTUAL_ENV)

test:
	$(TOX)

lint/isort: virtualenv
	$(ISORT) --check-only --diff $(SOURCES)

lint/flake8: virtualenv
	$(FLAKE8) $(SOURCES)

lint/black: virtualenv
	$(BLACK) --check $(SOURCES)

format/isort: virtualenv
	$(ISORT) $(SOURCES)

format/black: virtualenv
	$(BLACK) --verbose $(SOURCES)

lint: lint/isort lint/flake8 lint/black

format: format/isort format/black

clean: release/clean docs/clean
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +

clean/all: clean
	rm -rf $(VIRTUAL_ENV) .tox/

run/uvicorn: $(VIRTUAL_ENV)
	$(UVICORN) main:app --reload

docker/build:
	docker build --tag=$(DOCKER_IMAGE) .

docker/shell:
	docker run --rm -it \
		--env PORT=$(DOCKER_PORT) \
		--env WEB3_INFURA_PROJECT_ID \
		--publish $(DOCKER_PORT):$(DOCKER_PORT) $(DOCKER_IMAGE) $(DOCKER_COMMAND)

docker/run:
	docker run --rm -it \
		--env PORT=$(DOCKER_PORT) \
		--env WEB3_INFURA_PROJECT_ID \
		--publish $(DOCKER_PORT):$(DOCKER_PORT) $(DOCKER_IMAGE)
