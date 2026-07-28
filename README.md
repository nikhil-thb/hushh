<div align="center">

# 🔒 Hushh Tunnel

**Production-ready open-source reverse tunneling platform**

[![CI](https://github.com/hushh-ai/hushh-tunnel/actions/workflows/ci.yml/badge.svg)](https://github.com/hushh-ai/hushh-tunnel/actions/workflows/ci.yml)
[![Docker](https://github.com/hushh-ai/hushh-tunnel/actions/workflows/docker.yml/badge.svg)](https://github.com/hushh-ai/hushh-tunnel/actions/workflows/docker.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Expose your localhost to the internet over HTTPS in seconds.

```
hushh http 3000
```

```
✔ Connected

Tunnel URL:
https://a8x91kp3.hushh.online

Forwarding:
  https://a8x91kp3.hushh.online
        →
  http://localhost:3000
```

</div>

---

## ✨ Features

- 🔐 **Secure HTTPS tunnels** via Caddy + Let's Encrypt wildcard certificates
- ⚡ **WebSocket-based protocol** — persistent, low-latency connections
- 🔑 **API key authentication** with bcrypt hashing
- 🎯 **Custom subdomains** — `hushh http 3000 --subdomain myapi`
- 🔄 **Auto-reconnect** with exponential backoff
- 📊 **Prometheus metrics** at `/metrics`
- 🌡️ **Health probes** at `/health` and `/readyz`
- 🐳 **Docker + Kubernetes** ready
- ☁️ **Terraform** infrastructure examples
- 🧪 **Full test suite** — unit, integration, and E2E

---

## 🚀 Quick Start

### Install the CLI

```bash
pip install hushh-tunnel
```

### Login

```bash
hushh login
# Enter your email and password
```

### Expose a local service

```bash
# Start your local app first
python -m http.server 3000

# Open a tunnel
hushh http 3000
```

### Custom subdomain

```bash
hushh http 8080 --subdomain myapi
# → https://myapi.hushh.online
```

---

## 🏗️ Architecture

```
Browser
  │
  ▼ HTTPS
Caddy (TLS termination, wildcard cert)
  │
  ▼ HTTP
FastAPI Server (hushh.online)
  │
  ├── REST API     (/auth, /api/tunnels, /api/users, /health, /metrics)
  │
  └── TunnelRoutingMiddleware
        │  (routes by Host: <subdomain>.hushh.online)
        ▼
      TunnelManager (in-memory registry)
        │
        ▼ WebSocket (persistent)
      CLI Client (hushh http 3000)
        │
        ▼ HTTP
      localhost:3000
```

**Protocol**: JSON messages over WebSocket with Base64 binary support.
See [docs/protocol.md](docs/protocol.md) for full specification.

---

## 📦 Project Structure

```
hushh/
├── server/          # FastAPI tunnel server
│   ├── main.py      # App entrypoint + WebSocket handler
│   ├── config.py    # Pydantic Settings
│   ├── core/        # TunnelManager, proxy, middleware, metrics
│   ├── api/         # REST routers (auth, tunnels, users, stats, health)
│   ├── models/      # SQLAlchemy ORM models
│   └── db/          # Database engine + Alembic migrations
├── client/          # Typer CLI
│   ├── main.py      # CLI commands
│   ├── tunnel.py    # WebSocket client loop
│   ├── proxy.py     # httpx local forwarding
│   └── display.py   # Rich terminal UI
├── shared/
│   └── protocol.py  # Pydantic v2 wire protocol models
├── docker/          # Dockerfile + Caddy + Compose
├── kubernetes/      # K8s manifests
├── terraform/       # Infrastructure as code
├── .github/         # CI/CD workflows
├── tests/           # Unit + integration + E2E tests
└── docs/            # Documentation
```

---

## 🛠️ Self-Hosting

### Prerequisites

- Ubuntu 22.04 VPS
- Wildcard DNS: `*.hushh.online → <server-ip>` (and `hushh.online → <server-ip>`)
- Cloudflare account (for wildcard TLS DNS challenge)
- Docker + Docker Compose

### 1. Clone and configure

```bash
git clone https://github.com/hushh-ai/hushh-tunnel
cd hushh-tunnel
cp .env.example .env
# Edit .env — set HUSHH_SECRET_KEY, HUSHH_ADMIN_PASSWORD, CLOUDFLARE_API_TOKEN
```

### 2. Deploy

```bash
docker compose -f docker/docker-compose.yml up -d
```

### 3. Create users

```bash
# SSH into server
curl -X POST https://hushh.online/api/users \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "yourpassword"}'
```

See [docs/deployment.md](docs/deployment.md) for the full guide.

---

## 💻 CLI Reference

| Command | Description |
|---|---|
| `hushh login` | Authenticate with the server |
| `hushh logout` | Clear local credentials |
| `hushh whoami` | Show current user |
| `hushh http <port>` | Open an HTTP tunnel |
| `hushh http <port> --subdomain <name>` | Open with custom subdomain |
| `hushh status` | List your active tunnels |
| `hushh stop <subdomain>` | Disconnect a tunnel |
| `hushh version` | Show version |

---

## 🔧 Development

```bash
# Clone
git clone https://github.com/hushh-ai/hushh-tunnel
cd hushh-tunnel

# Install with dev dependencies
pip install -e ".[dev]"

# Initialize DB
alembic upgrade head

# Run server (dev mode)
make dev

# Run tests
make test

# Lint + typecheck
make check
```

---

## 📡 API

OpenAPI docs available at `https://hushh.online/docs` when the server is running.

Key endpoints:

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/login` | Get access token + API key |
| `GET` | `/auth/whoami` | Current user info |
| `GET` | `/api/tunnels` | List active tunnels |
| `DELETE` | `/api/tunnels/{subdomain}` | Stop a tunnel |
| `GET` | `/health` | Liveness probe |
| `GET` | `/readyz` | Readiness probe |
| `GET` | `/metrics` | Prometheus metrics |

---

## 🗺️ Roadmap

- [ ] TCP tunnels
- [ ] Request inspector (replay, traffic recording)
- [ ] Reserved domains & custom domains
- [ ] Team accounts + paid plans
- [ ] Multi-region deployment
- [ ] SSH tunnel support
- [ ] Web dashboard

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
Built with ❤️ by the Hushh team · <a href="https://hushh.online">hushh.online</a>
</div>
