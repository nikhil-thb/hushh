# Hushh Tunnel — Wire Protocol Specification

Version: `0.1.0`

---

## Overview

All messages between the tunnel server and CLI client are JSON-encoded over a
persistent WebSocket connection at `wss://hushh.online/tunnel/ws`.

Binary payloads (request/response bodies) are **Base64-encoded** in the `body`
field with `is_binary: true`.

---

## Message Format

Every message has:

| Field | Type | Description |
|---|---|---|
| `type` | string | Message type discriminator (see below) |
| `message_id` | UUID | Unique ID for this message |

---

## Message Types

### `register` (Client → Server)

Sent as the first message after WebSocket connection.

```json
{
  "type": "register",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "api_key": "hushh_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456",
  "requested_subdomain": "myapi",
  "client_version": "0.1.0",
  "local_port": 3000
}
```

`requested_subdomain` is optional. If omitted, the server generates a random 8-char slug.

---

### `register_ack` (Server → Client)

```json
{
  "type": "register_ack",
  "message_id": "...",
  "subdomain": "myapi",
  "tunnel_url": "https://myapi.hushh.online",
  "server_version": "0.1.0"
}
```

---

### `heartbeat` (Client → Server)

```json
{
  "type": "heartbeat",
  "message_id": "..."
}
```

Sent every 15 seconds. Server evicts tunnels that miss 3 consecutive heartbeats.

---

### `heartbeat_ack` (Server → Client)

```json
{
  "type": "heartbeat_ack",
  "message_id": "..."
}
```

---

### `request` (Server → Client)

Forwarded incoming HTTP request.

```json
{
  "type": "request",
  "message_id": "...",
  "request_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "method": "POST",
  "path": "/api/users",
  "query": "page=1&limit=10",
  "headers": {
    "content-type": "application/json",
    "x-forwarded-for": "1.2.3.4",
    "x-forwarded-proto": "https"
  },
  "body": "eyJuYW1lIjogInRlc3QifQ==",
  "is_binary": false
}
```

`request_id` must be included in the matching `response` message.

---

### `response` (Client → Server)

```json
{
  "type": "response",
  "message_id": "...",
  "request_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status_code": 201,
  "headers": {
    "content-type": "application/json"
  },
  "body": "eyJ1c2VyX2lkIjogMX0=",
  "is_binary": false
}
```

---

### `error` (Server → Client)

```json
{
  "type": "error",
  "message_id": "...",
  "code": "AUTH_FAILED",
  "detail": "Invalid API key."
}
```

**Error codes:**

| Code | Description |
|---|---|
| `AUTH_FAILED` | Invalid or missing API key |
| `SUBDOMAIN_CONFLICT` | Requested subdomain already in use |
| `TUNNEL_LIMIT_EXCEEDED` | User or server limit reached |
| `PROTOCOL_ERROR` | Unexpected message or order |
| `INVALID_MESSAGE` | Message failed validation |

---

### `disconnect` (Either → Either)

```json
{
  "type": "disconnect",
  "message_id": "...",
  "reason": "client_stop"
}
```

**Reason strings:** `client_stop`, `server_shutdown`, `heartbeat_timeout`, `api_disconnect`

---

## Connection Lifecycle

```
Client                                    Server
  │                                         │
  │── WebSocket connect ──────────────────▶ │
  │── register ──────────────────────────▶  │
  │ ◀─────────────────────────── register_ack │
  │                                         │
  │   (browser sends HTTP request)          │
  │ ◀──────────────────────────── request   │
  │── response ─────────────────────────▶  │
  │                                         │
  │── heartbeat (every 15s) ─────────────▶ │
  │ ◀───────────────────────── heartbeat_ack │
  │                                         │
  │── disconnect ────────────────────────▶  │
  │── WebSocket close ───────────────────▶  │
```

---

## Binary Payloads

When a request or response body cannot be decoded as UTF-8, it is Base64-encoded:

```json
{
  "body": "iVBORw0KGgoAAAANSUhEUgAA...",
  "is_binary": true
}
```

The receiver decodes with `base64.b64decode(body)`.

---

## Concurrency

Multiple `request` messages may be in-flight simultaneously. The `request_id` field
is used to match each `response` to its originating request. The client should
process requests concurrently (asyncio tasks) rather than sequentially.
