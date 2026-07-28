# Hushh Tunnel — Architecture

## System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         hushh.online                                │
│                                                                     │
│  Browser                                                            │
│     │ HTTPS                                                         │
│     ▼                                                               │
│  ┌──────────┐   wildcard TLS    ┌─────────────────────────────────┐ │
│  │  Caddy   │ ←─ Let's Encrypt ─│  Cloudflare DNS (DNS-01 chall.) │ │
│  │ (proxy)  │                   └─────────────────────────────────┘ │
│  └────┬─────┘                                                       │
│       │ HTTP + WebSocket                                            │
│       ▼                                                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              FastAPI Server (server/main.py)                   │ │
│  │                                                                │ │
│  │  ┌─────────────────────────────────────────────────────────┐  │ │
│  │  │         TunnelRoutingMiddleware                          │  │ │
│  │  │  Routes requests by Host: <sub>.hushh.online header     │  │ │
│  │  └──────────────────────────┬──────────────────────────────┘  │ │
│  │                             │                                  │ │
│  │  ┌──────────────────────────▼──────────────────────────────┐  │ │
│  │  │             TunnelManager (in-memory)                    │  │ │
│  │  │  subdomain → Tunnel { websocket, pending_requests }      │  │ │
│  │  └──────────────────────────┬──────────────────────────────┘  │ │
│  │                             │ WebSocket (persistent)          │ │
│  │  REST API  ──── SQLite ─────┘                                  │ │
│  │  /auth   /api/tunnels   /health   /metrics                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                             │                                       │
└─────────────────────────────┼───────────────────────────────────────┘
                              │ wss://hushh.online/tunnel/ws
                    ┌─────────▼───────────┐
                    │   Hushh CLI Client   │
                    │  (client/tunnel.py)  │
                    └─────────┬───────────┘
                              │ HTTP
                    ┌─────────▼───────────┐
                    │  localhost:3000      │
                    │  (your app)          │
                    └─────────────────────┘
```

---

## Request Flow (Sequence Diagram)

```
Browser     Caddy     FastAPI    TunnelManager    TunnelWS    CLI       localhost
   │           │          │            │              │          │           │
   │──GET /────▶          │            │              │          │           │
   │           │──proxy──▶│            │              │          │           │
   │           │          │──lookup(sub)──────────────▶          │           │
   │           │          │            │◀─ Tunnel ────│          │           │
   │           │          │──send REQUEST──────────────────────▶ │           │
   │           │          │            │              │          │──GET /────▶│
   │           │          │            │              │          │◀─ 200 ────│
   │           │          │──await Future             │          │           │
   │           │          │            │              │          │──RESPONSE─▶│
   │           │          │◀─ Future resolved ────────────────────            │
   │           │◀─ 200 ───│            │              │          │           │
   │◀─ 200 ────│          │            │              │          │           │
```

---

## TunnelManager State Machine

```
                    ┌──────────┐
                    │  Empty   │
                    └────┬─────┘
                         │ register()
                    ┌────▼─────┐
                    │  Active  │◀─── heartbeat()
                    └────┬─────┘
              ┌──────────┴───────────┐
      timeout │               client │ disconnect
     (sweep)  │               calls  │ unregister()
              ▼                      ▼
         ┌──────────┐          ┌──────────┐
         │ Evicted  │          │  Closed  │
         └──────────┘          └──────────┘
```

---

## Data Model

```
users
  id          INTEGER PK
  email       TEXT UNIQUE
  hashed_password  TEXT
  api_key_hash     TEXT
  is_active   BOOLEAN
  is_admin    BOOLEAN
  max_tunnels INTEGER
  created_at  DATETIME
  updated_at  DATETIME

tunnel_records
  id           INTEGER PK
  subdomain    TEXT UNIQUE
  user_id      INTEGER FK → users.id
  local_port   INTEGER
  status       TEXT (active|closed|timeout|error)
  created_at   DATETIME
  last_seen_at DATETIME
  closed_at    DATETIME
  client_version TEXT
```

---

## Protocol Message Hierarchy

```
BaseMessage
  ├── RegisterMessage         (client → server)
  ├── RegisterAckMessage      (server → client)
  ├── HeartbeatMessage        (client → server)
  ├── HeartbeatAckMessage     (server → client)
  ├── RequestMessage          (server → client)
  ├── ResponseMessage         (client → server)
  ├── ErrorMessage            (server → client)
  └── DisconnectMessage       (either → either)
```

---

## Extensibility

The architecture is designed to support future features without major refactoring:

| Future Feature | Extension Point |
|---|---|
| TCP tunnels | New message type + TCP proxy in `server/core/` |
| Custom domains | TunnelManager lookup by full hostname |
| Reserved domains | DB column on TunnelRecord |
| Multi-region | Redis-backed TunnelManager for shared state |
| Request inspector | Hook in `proxy.py` to log to a ring buffer |
| Traffic recording | Same hook, write to object storage |
| Team accounts | New `Team` model + FK on `User` |
| SSH tunnels | New protocol command + server-side SSH multiplexer |
