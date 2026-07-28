# Hushh Tunnel — Deployment Guide

## Single VPS Deployment (recommended for MVP)

### Prerequisites

| Item | Requirement |
|---|---|
| Server | Ubuntu 22.04 VPS (2 vCPU / 4 GB RAM minimum) |
| DNS | `hushh.online` → server IP, `*.hushh.online` → server IP |
| DNS Provider | Cloudflare (for wildcard TLS challenge) |
| Docker | Docker Engine 24+ and Docker Compose v2 |

---

### Step 1: Provision a server

Using Hetzner (recommended, ~$6/month for CX21):

```bash
# With Terraform
cd terraform/
cp terraform.tfvars.example terraform.tfvars
# Fill in your tokens
terraform init && terraform apply
```

Or manually create an Ubuntu 22.04 server at any VPS provider.

---

### Step 2: Install Docker

```bash
ssh root@<server-ip>

curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
```

---

### Step 3: Clone and configure

```bash
git clone https://github.com/hushh-ai/hushh-tunnel
cd hushh-tunnel

cp .env.example .env
nano .env
```

Set these values in `.env`:

```bash
HUSHH_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
HUSHH_ADMIN_EMAIL=admin@hushh.online
HUSHH_ADMIN_PASSWORD=your_secure_password
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
HUSHH_DOMAIN=hushh.online
```

---

### Step 4: Configure DNS

In Cloudflare, create two A records:

| Type | Name | Value | Proxy |
|---|---|---|---|
| A | `@` | `<server-ip>` | DNS only (grey cloud) |
| A | `*` | `<server-ip>` | DNS only (grey cloud) |

> **Important**: Set to "DNS only" (not proxied). Caddy handles TLS directly.

---

### Step 5: Build Caddy with Cloudflare plugin

Caddy requires the Cloudflare DNS plugin for wildcard certs. Build it:

```bash
docker build -t caddy-cloudflare - <<'EOF'
FROM caddy:2-builder AS builder
RUN xcaddy build --with github.com/caddy-dns/cloudflare

FROM caddy:2-alpine
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
EOF
```

Update `docker/docker-compose.yml` to use `image: caddy-cloudflare` for the caddy service.

---

### Step 6: Deploy

```bash
docker compose -f docker/docker-compose.yml up -d

# Check logs
docker compose -f docker/docker-compose.yml logs -f
```

---

### Step 7: Verify

```bash
# Health check
curl https://hushh.online/health
# {"status": "ok"}

# OpenAPI docs
open https://hushh.online/docs
```

---

### Step 8: Create your first user

The admin account is seeded from `HUSHH_ADMIN_EMAIL` and `HUSHH_ADMIN_PASSWORD`.

```bash
# Login as admin and get token
TOKEN=$(curl -s -X POST https://hushh.online/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@hushh.online","password":"your_password"}' \
  | jq -r .access_token)

# Create a regular user
curl -X POST https://hushh.online/api/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@example.com","password":"devpassword"}'
```

---

### Step 9: Install and use the CLI

On your local machine:

```bash
pip install hushh-tunnel

hushh login
# Email: dev@example.com
# Password: ••••••••••

hushh http 3000
```

---

## Production Hardening Checklist

- [ ] `HUSHH_SECRET_KEY` is a 32+ char random hex string
- [ ] `HUSHH_ADMIN_PASSWORD` is strong and unique
- [ ] SSH access restricted to known IPs
- [ ] Cloudflare API token scoped to `Zone:DNS:Edit` only
- [ ] Docker socket not exposed to the internet
- [ ] Caddy data volume backed up (contains TLS certs)
- [ ] Log rotation configured (Docker's `--log-opt max-size`)
- [ ] Monitoring: Prometheus scraping `/metrics`
- [ ] Alerting: tunnel count, error rate, response latency

---

## Updating

```bash
git pull
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d
```

---

## Backups

```bash
# Backup SQLite database
docker exec hushh-server sqlite3 /data/hushh.db .dump > backup.sql

# Backup Caddy TLS data
docker cp hushh-caddy:/data/caddy ./caddy-backup
```
