all: .build tests


PYTHON := .venv/bin/python

clean:
	rm .build

build: .build

.build:
	python -m venv .venv/
	$(PYTHON) -m pip install -r requirements.txt -r requirements-dev.txt
	touch .build

tests: .build
	$(PYTHON) -m pytest ./
