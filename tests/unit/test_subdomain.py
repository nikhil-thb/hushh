"""Unit tests for subdomain generation and validation."""

from __future__ import annotations

from server.core.tunnel_manager import _SUBDOMAIN_ALPHABET, _SUBDOMAIN_PATTERN


class TestSubdomainPattern:
    def test_valid_lowercase(self) -> None:
        assert _SUBDOMAIN_PATTERN.match("abc123")

    def test_valid_with_hyphens(self) -> None:
        assert _SUBDOMAIN_PATTERN.match("my-cool-api")

    def test_invalid_starts_with_hyphen(self) -> None:
        assert not _SUBDOMAIN_PATTERN.match("-myapi")

    def test_invalid_ends_with_hyphen(self) -> None:
        assert not _SUBDOMAIN_PATTERN.match("myapi-")

    def test_invalid_uppercase(self) -> None:
        assert not _SUBDOMAIN_PATTERN.match("MyApi")

    def test_invalid_too_short(self) -> None:
        assert not _SUBDOMAIN_PATTERN.match("ab")

    def test_valid_exactly_three_chars(self) -> None:
        assert _SUBDOMAIN_PATTERN.match("abc")

    def test_valid_numbers_only(self) -> None:
        assert _SUBDOMAIN_PATTERN.match("12345678")

    def test_invalid_special_chars(self) -> None:
        assert not _SUBDOMAIN_PATTERN.match("my_api")
        assert not _SUBDOMAIN_PATTERN.match("my.api")


class TestSubdomainAlphabet:
    def test_alphabet_is_lowercase(self) -> None:
        assert _SUBDOMAIN_ALPHABET == _SUBDOMAIN_ALPHABET.lower()

    def test_alphabet_has_digits(self) -> None:
        assert any(c.isdigit() for c in _SUBDOMAIN_ALPHABET)

    def test_alphabet_no_special(self) -> None:
        for c in _SUBDOMAIN_ALPHABET:
            assert c.isalnum(), f"Unexpected char: {c!r}"
