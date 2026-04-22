.PHONY: install run migrate test lint

install:
	python -m pip install -r requirements-dev.txt

run:
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	python -m alembic upgrade head

test:
	python -m pytest

lint:
	python -m ruff check .
