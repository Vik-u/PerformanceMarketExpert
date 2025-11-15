PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
ADPULSE := $(VENV)/bin/adpulse

.PHONY: setup install test cli

setup: $(VENV)/bin/activate
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)

install: setup

test:
	$(PYTEST)

cli:
	$(ADPULSE) --help
