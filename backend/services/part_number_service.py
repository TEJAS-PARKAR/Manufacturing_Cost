from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import warnings

from cryptography.fernet import Fernet, InvalidToken


_DEV_KEY: bytes | None = None


def _hmac_key() -> bytes:
    configured = os.getenv("PART_NUMBER_HMAC_KEY", "").strip()
    if configured:
        return configured.encode("utf-8")
    if os.getenv("ENVIRONMENT", "development").strip().lower() in {"production", "prod"}:
        raise RuntimeError("PART_NUMBER_HMAC_KEY is required in production.")
    global _DEV_KEY
    if _DEV_KEY is None:
        _DEV_KEY = secrets.token_bytes(32)
        warnings.warn(
            "PART_NUMBER_HMAC_KEY is not configured; using an ephemeral development key. "
            "Configure it for persistent session references.",
            RuntimeWarning,
            stacklevel=2,
        )
    return _DEV_KEY


def normalize_part_number(part_number: str) -> str:
    value = str(part_number).strip()
    if not value.isdigit() or len(value) != 12:
        raise ValueError("Part number must be exactly 12 digits (0-9 only).")
    return value


def part_number_hash(part_number: str) -> str:
    normalized = normalize_part_number(part_number)
    return hmac.new(_hmac_key(), normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def _encryption_key() -> bytes:
    configured = os.getenv("PART_NUMBER_ENCRYPTION_KEY", "").strip()
    if configured:
        try:
            Fernet(configured.encode("ascii"))
        except (ValueError, UnicodeEncodeError):
            raise RuntimeError("PART_NUMBER_ENCRYPTION_KEY must be a valid Fernet key.")
        return configured.encode("ascii")
    raise RuntimeError("PART_NUMBER_ENCRYPTION_KEY is required on the server.")


def encrypt_part_number(part_number: str) -> str:
    normalized = normalize_part_number(part_number)
    return Fernet(_encryption_key()).encrypt(normalized.encode("utf-8")).decode("ascii")


def decrypt_part_number(encrypted_part_number: str) -> str | None:
    try:
        value = Fernet(_encryption_key()).decrypt(
            str(encrypted_part_number).encode("ascii")
        ).decode("utf-8")
        return normalize_part_number(value)
    except (InvalidToken, UnicodeError, ValueError, TypeError):
        return None


def session_reference(employee_id: str, part_hash: str) -> str:
    return f"{employee_id.strip()}::{part_hash}"


def is_session_reference(value: str, employee_id: str) -> bool:
    prefix = f"{employee_id.strip()}::"
    suffix = str(value).strip()
    return suffix.startswith(prefix) and len(suffix[len(prefix):]) == 64 and all(
        character in "0123456789abcdef" for character in suffix[len(prefix):].lower()
    )


def part_hash_from_reference(value: str, employee_id: str) -> str:
    if not is_session_reference(value, employee_id):
        raise ValueError("Invalid session reference.")
    return str(value).strip().split("::", 1)[1]
