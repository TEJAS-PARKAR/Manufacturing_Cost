from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Token lifetime (seconds). 8 hours by default.
TOKEN_TTL_SECONDS = int(os.getenv("AUTH_TOKEN_TTL", "28800"))


def _secret() -> bytes:
    secret = os.getenv("AUTH_SECRET", "").strip()
    if not secret:
        # Fail loud — never sign tokens with an empty/guessable key.
        raise RuntimeError("AUTH_SECRET is not configured on the server.")
    return secret.encode("utf-8")


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(subject: str, role: str) -> str:
    """Create a signed, stateless token: payload.signature (HMAC-SHA256)."""
    payload = {
        "sub": subject,
        "role": role,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(_secret(), payload_b64.encode("ascii"), hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{payload_b64}.{signature_b64}"


def verify_token(token: str) -> Optional[dict[str, Any]]:
    """Return the payload dict if the token is valid & unexpired, else None."""
    try:
        payload_b64, signature_b64 = token.split(".", 1)
        expected_sig = hmac.new(_secret(), payload_b64.encode("ascii"), hashlib.sha256).digest()
        actual_sig = _b64url_decode(signature_b64)
        # constant-time comparison prevents timing attacks
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None