"""
Prometheus metrics for the Hushh Tunnel server.

All metrics are registered here and imported by other modules.
The ``/metrics`` endpoint is mounted in ``server/main.py``.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# ── Tunnel metrics ────────────────────────────────────────────────────────────

TUNNEL_CONNECTED_TOTAL = Counter(
    "hushh_tunnel_connections_total",
    "Total number of tunnel connections established.",
)

TUNNEL_DISCONNECTED_TOTAL = Counter(
    "hushh_tunnel_disconnections_total",
    "Total number of tunnel disconnections.",
)

TUNNEL_ACTIVE_GAUGE = Gauge(
    "hushh_tunnels_active",
    "Current number of active tunnels.",
)

TUNNEL_IDLE_EVICTIONS_TOTAL = Counter(
    "hushh_tunnel_idle_evictions_total",
    "Tunnels evicted due to heartbeat timeout.",
)

# ── Request metrics ───────────────────────────────────────────────────────────

HTTP_REQUESTS_TOTAL = Counter(
    "hushh_http_requests_total",
    "Total HTTP requests proxied through tunnels.",
    ["method", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "hushh_http_request_duration_seconds",
    "Histogram of proxied HTTP request durations.",
    ["method"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

HTTP_REQUEST_SIZE_BYTES = Histogram(
    "hushh_http_request_size_bytes",
    "Histogram of incoming HTTP request body sizes.",
    buckets=[1_024, 10_240, 102_400, 1_048_576, 10_485_760, 52_428_800],
)

HTTP_RESPONSE_SIZE_BYTES = Histogram(
    "hushh_http_response_size_bytes",
    "Histogram of HTTP response body sizes from local services.",
    buckets=[1_024, 10_240, 102_400, 1_048_576, 10_485_760, 52_428_800],
)

HTTP_TUNNEL_NOT_FOUND_TOTAL = Counter(
    "hushh_http_tunnel_not_found_total",
    "Requests that arrived for an unknown / offline tunnel.",
)

HTTP_REQUEST_TIMEOUT_TOTAL = Counter(
    "hushh_http_request_timeout_total",
    "Requests that timed out waiting for a tunnel response.",
)

# ── Auth metrics ──────────────────────────────────────────────────────────────

AUTH_SUCCESS_TOTAL = Counter(
    "hushh_auth_success_total",
    "Successful authentications.",
    ["method"],
)

AUTH_FAILURE_TOTAL = Counter(
    "hushh_auth_failure_total",
    "Failed authentication attempts.",
    ["method"],
)
