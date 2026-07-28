# Hushh Tunnel — Developer Guide

## Local Development Setup

### Requirements

- Python 3.12+
- `pip`
- Git

### Setup

```bash
git clone https://github.com/hushh-ai/hushh-tunnel
cd hushh-tunnel

# Install with dev dependencies
pip install -e ".[dev]"

# Copy env
cp .env.example .env
# Edit .env — set HUSHH_SECRET_KEY (any 32-char string for dev)
```

### Run the server

```bash
# Initialize DB
alembic upgrade head

# Start server (auto-reload)
make dev
# → http://localhost:8000
# → http://localhost:8000/docs
```

### Run the CLI locally

```bash
# Point client to local server
export HUSHH_SERVER_URL=http://localhost:8000

hushh login  # use admin@hushh.online / changeme_admin_password

# Start a local service
python -m http.server 3000 &

# Open tunnel
hushh http 3000
```

---

## Testing

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration

# E2E tests
make test-e2e

# With coverage report
make test-cov
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures (settings, DB, app, HTTP client)
├── unit/
│   ├── test_protocol.py     # Protocol serialization / validation
│   ├── test_tunnel_manager.py  # TunnelManager unit tests
│   └── test_subdomain.py    # Subdomain validation
├── integration/
│   ├── test_auth.py         # Auth API integration tests
│   ├── test_tunnel_flow.py  # Proxy flow tests
│   └── test_reconnect.py    # Reconnect logic tests
└── e2e/
    └── test_http_tunnel.py  # Full end-to-end flow
```

---

## Code Quality

```bash
# Lint
make lint         # ruff

# Format
make format       # black + ruff --fix

# Type check
make typecheck    # mypy
```

All CI checks must pass before merging.

---

## Database Migrations

```bash
# Create a new migration after modifying ORM models
make migrate-create
# Enter a name: add_user_plan_field

# Apply migrations
make migrate

# Rollback one step
make migrate-downgrade
```

Migrations live in `server/db/migrations/versions/`.

---

## Adding a New Feature

### Adding a new API endpoint

1. Create or modify a router in `server/api/`
2. Include the router in `server/main.py` via `app.include_router()`
3. Add integration tests in `tests/integration/`
4. Update OpenAPI description if needed

### Adding a new protocol message type

1. Add the type to `MessageType` enum in `shared/protocol.py`
2. Create a new Pydantic model
3. Add to the appropriate union (`ClientMessage` or `ServerMessage`)
4. Handle the new type in `server/main.py::_handle_client_message`
5. Handle in `client/tunnel.py::_message_loop`
6. Add unit tests in `tests/unit/test_protocol.py`

### Adding a new CLI command

1. Add a `@app.command()` function in `client/main.py`
2. Add display helpers to `client/display.py` if needed
3. Document in README.md

---

## Architecture Decisions

### Why WebSocket over HTTP long-polling?

WebSocket provides a true duplex channel with lower overhead for the
high-frequency ping-pong of tunnel request/response pairs.

### Why asyncio.Future for response correlation?

Each incoming HTTP request creates a `Future` keyed by `request_id`.
When the client sends the matching `ResponseMessage`, the server resolves
the future. This avoids polling or queues.

### Why SQLite for MVP?

Zero-configuration, no separate service, suitable for hundreds of concurrent
tunnels on a single server. The `database_url` setting lets you switch to
PostgreSQL with no code changes.

### Why Caddy instead of nginx?

Caddy handles Let's Encrypt wildcard certificates automatically via the
DNS-01 challenge. No manual cert renewal, no certbot crons.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes, add tests
4. Ensure all checks pass: `make check && make test`
5. Push and open a Pull Request

Please follow the existing code style (Black + Ruff).
