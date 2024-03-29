.PHONY = all run install test test-ci format
URL = "https://google.com"
DEPTH = 2
WORKERS = 10

all: install run

run:
	poetry run python -m web_crawler --url "$(URL)" --depth "$(DEPTH)" --workers "$(WORKERS)"

install:
	poetry install

test:
	poetry run pytest -vv

test-ci:
	poetry run pytest -vv
	poetry run black --check .
	poetry run mypy . --ignore-missing-imports

format:
	poetry run black web_crawler tests
