.PHONY: install dev lint format typecheck test test-unit test-integration \
        migrate migrate-create server docker-build docker-up docker-down clean

# ── Setup ─────────────────────────────────────────────────────────────────────
install:
	pip install -e ".[dev]"

# ── Dev server ────────────────────────────────────────────────────────────────
dev:
	uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

server:
	python -m server.main

# ── Code quality ──────────────────────────────────────────────────────────────
lint:
	ruff check .

format:
	black .
	ruff check --fix .

typecheck:
	mypy server/ client/ shared/

check: lint typecheck

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

test-cov:
	pytest tests/ --cov --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; alembic revision --autogenerate -m "$$name"

migrate-downgrade:
	alembic downgrade -1

# ── Docker ────────────────────────────────────────────────────────────────────
docker-build:
	docker build -f docker/Dockerfile.server -t hushh-server:latest .

docker-up:
	docker compose -f docker/docker-compose.yml up -d

docker-down:
	docker compose -f docker/docker-compose.yml down

docker-logs:
	docker compose -f docker/docker-compose.yml logs -f

docker-dev:
	docker compose -f docker/docker-compose.dev.yml up

# ── Utilities ─────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build

seed-admin:
	python -c "from server.db.seed import seed_admin; import asyncio; asyncio.run(seed_admin())"

generate-key:
	@python -c "import secrets; print(secrets.token_hex(32))"
