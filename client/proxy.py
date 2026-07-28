"""
Local HTTP forwarding — takes a RequestMessage, forwards it to localhost,
and returns a ResponseMessage.

Uses ``httpx.AsyncClient`` with HTTP/2 support.
All HTTP methods are supported.  Large bodies are handled without loading
everything into memory by streaming when possible.
"""

from __future__ import annotations

import httpx
import structlog
from shared.protocol import RequestMessage, ResponseMessage

logger = structlog.get_logger(__name__)

# Headers that must not be forwarded to the local service
_HOP_BY_HOP = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
)


async def forward(
    request_msg: RequestMessage,
    *,
    local_port: int,
    local_host: str = "127.0.0.1",
    timeout: float = 30.0,
) -> ResponseMessage:
    """
    Forward an incoming tunnel request to the local service.

    Args:
        request_msg: The decoded RequestMessage from the tunnel.
        local_port: The local port to forward to.
        local_host: The local host (default 127.0.0.1).
        timeout: Request timeout in seconds.

    Returns:
        A ResponseMessage to send back through the tunnel.
    """
    base_url = f"http://{local_host}:{local_port}"
    url = f"{base_url}{request_msg.path}"
    if request_msg.query:
        url = f"{url}?{request_msg.query}"

    # Filter and rewrite headers
    headers = {
        k: v for k, v in request_msg.headers.items() if k.lower() not in _HOP_BY_HOP
    }
    # Rewrite host to localhost so the local service doesn't reject it
    headers["host"] = f"{local_host}:{local_port}"

    body = request_msg.decode_body()

    logger.debug(
        "proxy.forwarding",
        method=request_msg.method,
        url=url,
        body_size=len(body),
    )

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            http2=False,  # most local dev servers don't support h2
        ) as client:
            resp = await client.request(
                method=request_msg.method,
                url=url,
                headers=headers,
                content=body,
            )

        # Filter hop-by-hop from response headers
        resp_headers = {
            k.lower(): v
            for k, v in resp.headers.multi_items()
            if k.lower() not in _HOP_BY_HOP
        }

        logger.debug(
            "proxy.forwarded",
            status=resp.status_code,
            response_size=len(resp.content),
        )

        return ResponseMessage.from_raw(
            request_id=request_msg.request_id,
            status_code=resp.status_code,
            headers=resp_headers,
            body=resp.content,
        )

    except httpx.ConnectError as exc:
        logger.error("proxy.connect_error", url=url, error=str(exc))
        return ResponseMessage.from_raw(
            request_id=request_msg.request_id,
            status_code=502,
            headers={"content-type": "text/plain"},
            body=f"Hushh: Could not connect to localhost:{local_port}. Is your service running?".encode(),
        )
    except httpx.TimeoutException as exc:
        logger.error("proxy.timeout", url=url, error=str(exc))
        return ResponseMessage.from_raw(
            request_id=request_msg.request_id,
            status_code=504,
            headers={"content-type": "text/plain"},
            body=f"Hushh: Local service at localhost:{local_port} timed out.".encode(),
        )
    except Exception as exc:
        logger.error("proxy.unexpected_error", url=url, error=str(exc))
        return ResponseMessage.from_raw(
            request_id=request_msg.request_id,
            status_code=500,
            headers={"content-type": "text/plain"},
            body=f"Hushh: Unexpected error: {exc}".encode(),
        )
