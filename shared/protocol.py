"""
Hushh Tunnel Wire Protocol
==========================

All messages exchanged between the tunnel server and CLI client are JSON-encoded
Pydantic v2 models with a discriminated ``type`` field.

Binary payloads (request/response bodies) are Base64-encoded strings.

Message Flow
------------
Client → Server:
    REGISTER      → server allocates subdomain, returns REGISTER_ACK
    HEARTBEAT     → server replies HEARTBEAT_ACK
    RESPONSE      → carries forwarded HTTP response back to the browser
    DISCONNECT    → graceful teardown

Server → Client:
    REGISTER_ACK  → confirms registration, carries public tunnel URL
    HEARTBEAT_ACK → keepalive confirmation
    REQUEST       → carries incoming HTTP request to be forwarded to localhost
    ERROR         → signals a protocol or routing error
    DISCONNECT    → server-initiated teardown
"""

from __future__ import annotations

import base64
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Message types
# ---------------------------------------------------------------------------


class MessageType(StrEnum):
    """Enumeration of all protocol message types."""

    REGISTER = "register"
    REGISTER_ACK = "register_ack"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    DISCONNECT = "disconnect"


# ---------------------------------------------------------------------------
# Base message
# ---------------------------------------------------------------------------


class BaseMessage(BaseModel):
    """Common fields present in every wire message."""

    model_config = {"extra": "forbid"}

    message_id: UUID = Field(default_factory=uuid4, description="Unique message identifier.")


# ---------------------------------------------------------------------------
# Client → Server
# ---------------------------------------------------------------------------


class RegisterMessage(BaseMessage):
    """
    Sent by the client immediately after WebSocket connection to claim a tunnel.

    If ``requested_subdomain`` is *None*, the server generates a random one.
    """

    type: Literal[MessageType.REGISTER] = MessageType.REGISTER
    api_key: str = Field(..., description="Client API key for authentication.")
    requested_subdomain: str | None = Field(
        None,
        min_length=3,
        max_length=63,
        pattern=r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$",
        description="Optional desired subdomain slug.",
    )
    client_version: str = Field("0.1.0", description="Client version string.")
    local_port: int = Field(..., ge=1, le=65535, description="Local port being tunneled.")


class HeartbeatMessage(BaseMessage):
    """Periodic keepalive sent by the client."""

    type: Literal[MessageType.HEARTBEAT] = MessageType.HEARTBEAT


class ResponseMessage(BaseMessage):
    """
    HTTP response forwarded from the local service back through the tunnel.

    ``body`` is Base64-encoded if the response body contains binary data.
    """

    type: Literal[MessageType.RESPONSE] = MessageType.RESPONSE
    request_id: UUID = Field(..., description="Matches the ``request_id`` of the originating RequestMessage.")
    status_code: int = Field(..., ge=100, le=599)
    headers: dict[str, str] = Field(default_factory=dict)
    body: str = Field("", description="Base64-encoded response body.")
    is_binary: bool = Field(False, description="True when body is Base64-encoded binary.")

    def decode_body(self) -> bytes:
        """Return the raw body bytes."""
        if self.is_binary:
            return base64.b64decode(self.body)
        return self.body.encode()

    @classmethod
    def from_raw(
        cls,
        request_id: UUID,
        status_code: int,
        headers: dict[str, str],
        body: bytes,
    ) -> ResponseMessage:
        """Construct a ResponseMessage from raw bytes, encoding body as needed."""
        try:
            text = body.decode("utf-8")
            return cls(
                request_id=request_id,
                status_code=status_code,
                headers=headers,
                body=text,
                is_binary=False,
            )
        except UnicodeDecodeError:
            return cls(
                request_id=request_id,
                status_code=status_code,
                headers=headers,
                body=base64.b64encode(body).decode("ascii"),
                is_binary=True,
            )


class DisconnectMessage(BaseMessage):
    """Sent by either party to signal graceful teardown."""

    type: Literal[MessageType.DISCONNECT] = MessageType.DISCONNECT
    reason: str = Field("", description="Human-readable disconnect reason.")


# ---------------------------------------------------------------------------
# Server → Client
# ---------------------------------------------------------------------------


class RegisterAckMessage(BaseMessage):
    """Confirms tunnel registration and communicates the public URL."""

    type: Literal[MessageType.REGISTER_ACK] = MessageType.REGISTER_ACK
    subdomain: str
    tunnel_url: str = Field(..., description="Full public HTTPS URL, e.g. https://abc.hushh.online")
    server_version: str = Field("0.1.0")


class HeartbeatAckMessage(BaseMessage):
    """Server reply to a HeartbeatMessage."""

    type: Literal[MessageType.HEARTBEAT_ACK] = MessageType.HEARTBEAT_ACK


class RequestMessage(BaseMessage):
    """
    An incoming HTTP request forwarded from the browser through the tunnel.

    The client is expected to forward this to ``localhost:<port>`` and reply
    with a matching :class:`ResponseMessage`.
    """

    type: Literal[MessageType.REQUEST] = MessageType.REQUEST
    request_id: UUID = Field(default_factory=uuid4)
    method: str = Field(..., description="HTTP method in upper-case.")
    path: str = Field(..., description="Request path, e.g. /api/v1/users")
    query: str = Field("", description="Raw query string without leading '?'.")
    headers: dict[str, str] = Field(default_factory=dict)
    body: str = Field("", description="Base64-encoded request body.")
    is_binary: bool = Field(False)

    @field_validator("method")
    @classmethod
    def normalize_method(cls, v: str) -> str:
        return v.upper()

    def decode_body(self) -> bytes:
        """Return the raw body bytes."""
        if self.is_binary:
            return base64.b64decode(self.body)
        return self.body.encode()

    @classmethod
    def from_raw(
        cls,
        *,
        method: str,
        path: str,
        query: str,
        headers: dict[str, str],
        body: bytes,
        request_id: UUID | None = None,
    ) -> RequestMessage:
        """Construct from raw bytes."""
        rid = request_id or uuid4()
        try:
            text = body.decode("utf-8")
            return cls(
                request_id=rid,
                method=method,
                path=path,
                query=query,
                headers=headers,
                body=text,
                is_binary=False,
            )
        except UnicodeDecodeError:
            return cls(
                request_id=rid,
                method=method,
                path=path,
                query=query,
                headers=headers,
                body=base64.b64encode(body).decode("ascii"),
                is_binary=True,
            )


class ErrorMessage(BaseMessage):
    """Protocol or server-side error."""

    type: Literal[MessageType.ERROR] = MessageType.ERROR
    code: str = Field(..., description="Machine-readable error code, e.g. 'AUTH_FAILED'.")
    detail: str = Field("", description="Human-readable description.")


# ---------------------------------------------------------------------------
# Discriminated union — used for parsing incoming messages
# ---------------------------------------------------------------------------

# All message types that a server can receive from the client
ClientMessage = Annotated[
    RegisterMessage | HeartbeatMessage | ResponseMessage | DisconnectMessage,
    Field(discriminator="type"),
]

# All message types that a client can receive from the server
ServerMessage = Annotated[
    RegisterAckMessage | HeartbeatAckMessage | RequestMessage | ErrorMessage | DisconnectMessage,
    Field(discriminator="type"),
]

# Combined union used for generic parsing
AnyMessage = Annotated[
    RegisterMessage | RegisterAckMessage | HeartbeatMessage | HeartbeatAckMessage | RequestMessage | ResponseMessage | ErrorMessage | DisconnectMessage,
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_client_message(data: dict[str, Any]) -> ClientMessage:
    """Parse a raw dict into the appropriate client-originated message."""
    from pydantic import TypeAdapter

    adapter: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)
    return adapter.validate_python(data)


def parse_server_message(data: dict[str, Any]) -> ServerMessage:
    """Parse a raw dict into the appropriate server-originated message."""
    from pydantic import TypeAdapter

    adapter: TypeAdapter[ServerMessage] = TypeAdapter(ServerMessage)
    return adapter.validate_python(data)


def serialize_message(msg: BaseMessage) -> str:
    """Serialize any message to a JSON string for transmission."""
    return msg.model_dump_json()
