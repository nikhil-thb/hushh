"""Unit tests for the shared wire protocol."""

from __future__ import annotations

import base64
import json
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from shared.protocol import (
    DisconnectMessage,
    ErrorMessage,
    HeartbeatAckMessage,
    HeartbeatMessage,
    MessageType,
    RegisterAckMessage,
    RegisterMessage,
    RequestMessage,
    ResponseMessage,
    parse_client_message,
    parse_server_message,
    serialize_message,
)


class TestRegisterMessage:
    def test_valid(self) -> None:
        msg = RegisterMessage(api_key="hushh_abc123", local_port=3000)
        assert msg.type == MessageType.REGISTER
        assert msg.local_port == 3000
        assert msg.requested_subdomain is None

    def test_with_subdomain(self) -> None:
        msg = RegisterMessage(
            api_key="hushh_abc123",
            local_port=8080,
            requested_subdomain="myapi",
        )
        assert msg.requested_subdomain == "myapi"

    def test_invalid_subdomain_too_short(self) -> None:
        with pytest.raises(ValidationError):
            RegisterMessage(api_key="key", local_port=3000, requested_subdomain="ab")

    def test_invalid_subdomain_uppercase(self) -> None:
        with pytest.raises(ValidationError):
            RegisterMessage(api_key="key", local_port=3000, requested_subdomain="MyApi")

    def test_invalid_port_zero(self) -> None:
        with pytest.raises(ValidationError):
            RegisterMessage(api_key="key", local_port=0)

    def test_invalid_port_too_high(self) -> None:
        with pytest.raises(ValidationError):
            RegisterMessage(api_key="key", local_port=99999)

    def test_serialization_roundtrip(self) -> None:
        msg = RegisterMessage(api_key="hushh_test", local_port=3000)
        serialized = serialize_message(msg)
        data = json.loads(serialized)
        assert data["type"] == "register"
        assert data["local_port"] == 3000


class TestRequestMessage:
    def test_method_normalized(self) -> None:
        msg = RequestMessage.from_raw(
            method="get",
            path="/api",
            query="",
            headers={},
            body=b"",
        )
        assert msg.method == "GET"

    def test_text_body(self) -> None:
        msg = RequestMessage.from_raw(
            method="POST",
            path="/submit",
            query="",
            headers={"content-type": "text/plain"},
            body=b"hello world",
        )
        assert msg.is_binary is False
        assert msg.body == "hello world"
        assert msg.decode_body() == b"hello world"

    def test_binary_body(self) -> None:
        raw = bytes([0xFF, 0xFE, 0x00, 0x01])
        msg = RequestMessage.from_raw(
            method="POST",
            path="/upload",
            query="",
            headers={},
            body=raw,
        )
        assert msg.is_binary is True
        assert msg.decode_body() == raw

    def test_with_query(self) -> None:
        msg = RequestMessage.from_raw(
            method="GET",
            path="/search",
            query="q=test&page=1",
            headers={},
            body=b"",
        )
        assert msg.query == "q=test&page=1"


class TestResponseMessage:
    def test_text_response(self) -> None:
        rid = uuid4()
        msg = ResponseMessage.from_raw(
            request_id=rid,
            status_code=200,
            headers={"content-type": "application/json"},
            body=b'{"ok": true}',
        )
        assert msg.status_code == 200
        assert msg.is_binary is False
        assert msg.decode_body() == b'{"ok": true}'

    def test_binary_response(self) -> None:
        rid = uuid4()
        raw = b"\x89PNG\r\n"
        msg = ResponseMessage.from_raw(
            request_id=rid,
            status_code=200,
            headers={"content-type": "image/png"},
            body=raw,
        )
        assert msg.is_binary is True
        assert msg.decode_body() == raw

    def test_invalid_status_code(self) -> None:
        with pytest.raises(ValidationError):
            ResponseMessage(
                request_id=uuid4(),
                status_code=999,
                headers={},
                body="",
            )


class TestDiscriminatedUnion:
    def test_parse_client_register(self) -> None:
        data = {
            "type": "register",
            "message_id": str(uuid4()),
            "api_key": "hushh_test",
            "local_port": 3000,
        }
        msg = parse_client_message(data)
        assert isinstance(msg, RegisterMessage)

    def test_parse_client_heartbeat(self) -> None:
        data = {"type": "heartbeat", "message_id": str(uuid4())}
        msg = parse_client_message(data)
        assert isinstance(msg, HeartbeatMessage)

    def test_parse_server_register_ack(self) -> None:
        data = {
            "type": "register_ack",
            "message_id": str(uuid4()),
            "subdomain": "abc123",
            "tunnel_url": "https://abc123.hushh.online",
        }
        msg = parse_server_message(data)
        assert isinstance(msg, RegisterAckMessage)
        assert msg.subdomain == "abc123"

    def test_parse_server_error(self) -> None:
        data = {
            "type": "error",
            "message_id": str(uuid4()),
            "code": "AUTH_FAILED",
            "detail": "Bad key",
        }
        msg = parse_server_message(data)
        assert isinstance(msg, ErrorMessage)
        assert msg.code == "AUTH_FAILED"

    def test_parse_invalid_type(self) -> None:
        from pydantic import ValidationError

        data = {"type": "unknown_type", "message_id": str(uuid4())}
        with pytest.raises((ValidationError, KeyError, Exception)):
            parse_client_message(data)
