"""LiteLLM provider routing through the Orogen gateway.

This is a thin shim — LiteLLM already speaks OpenAI-shaped HTTP, and our gateway is
OpenAI-compatible. The shim's value is:
  1. Injecting customer_nonce / x-useful-nonce header automatically.
  2. Surfacing useful_receipt + useful_verification on the response.
  3. Mapping `useful/<model>` prefix to our gateway base URL.
"""

from __future__ import annotations

import os
from typing import Any

from orogen_sdk import generate_nonce, verify_receipt
from orogen_sdk.nonce import current_timestamp_ms
from orogen_sdk.types import Receipt


class OrogenProvider:
    """Provider object held by LiteLLM. Stateless beyond config."""

    DEFAULT_BASE_URL = "https://gateway.orogen.network/v1"
    MODEL_PREFIX = "useful/"

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("OROGEN_API_KEY")
        self.base_url = (base_url or os.environ.get("OROGEN_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")

    def supports(self, model: str) -> bool:
        return model.startswith(self.MODEL_PREFIX)

    def normalize_model(self, model: str) -> str:
        """Strip `useful/` prefix before posting to gateway."""
        if model.startswith(self.MODEL_PREFIX):
            return model[len(self.MODEL_PREFIX) :]
        return model

    def build_request(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        extra: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        """Return (url, headers, body) ready for an HTTP POST."""
        if not self.api_key:
            raise RuntimeError("OROGEN_API_KEY not set")
        nonce = (extra or {}).get("customer_nonce") or (extra or {}).get("useful_nonce") or generate_nonce()
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "x-useful-nonce": nonce,
            "x-useful-nonce-ts-ms": str(current_timestamp_ms()),
        }
        body: dict[str, Any] = {
            "model": self.normalize_model(model),
            "messages": messages,
            "customer_nonce": nonce,
        }
        if extra:
            for k in ("temperature", "max_tokens", "stream", "seed"):
                if k in extra and extra[k] is not None:
                    body[k] = extra[k]
            for k in ("useful_tier", "useful_region", "useful_max_price_per_million", "useful_verify_receipt"):
                if k in extra and extra[k] is not None:
                    body[k] = extra[k]
                    if k == "useful_tier":
                        headers["x-useful-tier"] = str(extra[k])
                    elif k == "useful_region":
                        headers["x-useful-region"] = str(extra[k])
        url = f"{self.base_url}/chat/completions"
        return url, headers, body

    def parse_response(
        self,
        raw: dict[str, Any],
        *,
        expected_nonce: str | None = None,
        operator_pubkey_hex: str | None = None,
    ) -> dict[str, Any]:
        """Parse + optionally verify; return augmented OpenAI-shaped dict.

        `verify_receipt` requires a `Receipt` model and (for real signature
        verification) the operator's ed25519 public key. Without
        `operator_pubkey_hex`, only the shape check runs and `overall` is
        False — never silently report success.
        """
        raw_receipt = raw.get("useful_receipt")
        if raw_receipt and raw.get("useful_verify_receipt"):
            try:
                receipt = (
                    raw_receipt
                    if isinstance(raw_receipt, Receipt)
                    else Receipt.model_validate(raw_receipt)
                )
                verification = verify_receipt(
                    receipt,
                    operator_pubkey_hex=operator_pubkey_hex,
                    expected_nonce=expected_nonce,
                )
                raw["useful_verification"] = verification.model_dump()
            except Exception as exc:
                raw["useful_verification"] = {
                    "error": f"verify_receipt failed: {type(exc).__name__}: {exc}",
                    "overall": False,
                }
        return raw


def register() -> None:
    """Register the provider with LiteLLM, if available.

    LiteLLM doesn't expose a stable provider-plugin API at the moment; the simplest
    integration is via model-list config + api_base override. This function is a
    stub for when LiteLLM ships a plugin API; today it documents the registration
    intent without changing runtime behavior.
    """
    # See https://docs.litellm.ai/docs/providers — current path is config.yaml.
    # When the plugin API ships, hook here.
    return None
