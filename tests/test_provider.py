"""Tests for litellm_orogen_provider."""

from __future__ import annotations

import os

import pytest

from litellm_orogen_provider.provider import OrogenProvider


def test_supports_prefix() -> None:
    p = OrogenProvider(api_key="test")
    assert p.supports("useful/llama-3.1-70b")
    assert not p.supports("openai/gpt-4")
    assert not p.supports("gpt-4")


def test_normalize_strips_prefix() -> None:
    p = OrogenProvider(api_key="test")
    assert p.normalize_model("useful/llama-3.1-70b") == "llama-3.1-70b"
    assert p.normalize_model("llama-3.1-70b") == "llama-3.1-70b"


def test_build_request_includes_nonce() -> None:
    p = OrogenProvider(api_key="test", base_url="https://example.test/v1")
    url, headers, body = p.build_request(
        model="useful/llama-3.1-70b",
        messages=[{"role": "user", "content": "hi"}],
        extra={"temperature": 0.7, "useful_tier": "dc-standard"},
    )
    assert url == "https://example.test/v1/chat/completions"
    assert headers["Authorization"] == "Bearer test"
    assert "x-useful-nonce" in headers
    assert headers["x-useful-tier"] == "dc-standard"
    assert body["model"] == "llama-3.1-70b"
    assert body["temperature"] == 0.7
    assert body["customer_nonce"] == headers["x-useful-nonce"]
    # Deprecated alias is no longer sent on the wire (security audit M-W-06).
    assert "useful_nonce" not in body


def test_build_request_preserves_explicit_nonce() -> None:
    p = OrogenProvider(api_key="test")
    explicit = "0x" + "ab" * 32
    _, headers, body = p.build_request(
        model="useful/llama-3.1-70b",
        messages=[{"role": "user", "content": "hi"}],
        extra={"customer_nonce": explicit},
    )
    assert headers["x-useful-nonce"] == explicit
    assert body["customer_nonce"] == explicit
    assert "useful_nonce" not in body


def test_build_request_accepts_legacy_nonce_key() -> None:
    # Backwards-compat: callers passing the legacy `useful_nonce` extra still work,
    # but the wire field is always emitted as `customer_nonce` now.
    p = OrogenProvider(api_key="test")
    explicit = "0x" + "cd" * 32
    _, headers, body = p.build_request(
        model="useful/llama-3.1-70b",
        messages=[{"role": "user", "content": "hi"}],
        extra={"useful_nonce": explicit},
    )
    assert headers["x-useful-nonce"] == explicit
    assert body["customer_nonce"] == explicit
    assert "useful_nonce" not in body


def test_build_request_requires_api_key() -> None:
    # Ensure no env var leaks in
    old = os.environ.pop("OROGEN_API_KEY", None)
    try:
        p = OrogenProvider()
        with pytest.raises(RuntimeError):
            p.build_request(model="useful/llama-3.1-70b", messages=[])
    finally:
        if old:
            os.environ["OROGEN_API_KEY"] = old


def test_parse_response_passthrough_when_no_receipt() -> None:
    p = OrogenProvider(api_key="test")
    out = p.parse_response({"id": "x", "object": "chat.completion"})
    assert "useful_verification" not in out
