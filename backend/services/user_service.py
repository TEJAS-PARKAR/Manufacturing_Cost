from __future__ import annotations

import hashlib
import os
import secrets
from typing import Any, Optional

from backend.services.mongo_service import MongoConnection


class UserService:
    def __init__(self, collection=None, users_collection_name: Optional[str] = None) -> None:
        self.collection = collection
        self.users_collection_name = users_collection_name or os.getenv("MONGODB_USERS_COLLECTION", "users")
        if self.collection is None:
            self.collection = MongoConnection.get_collection(self.users_collection_name)
        if self.collection is not None:
            try:
                self.collection.create_index([("username", 1)], unique=True)
            except Exception:
                pass

    def register_user(self, username: str, password: str, role: str = "supplier") -> dict[str, Any]:
        if not username or not password:
            raise ValueError("username and password are required")
        if role not in ("supplier", "tata"):
            raise ValueError("role must be 'supplier' or 'tata'")

        if self.collection is None:
            raise RuntimeError("MongoDB connection is not available")

        existing = self.collection.find_one({"username": username})
        if existing is not None:
            raise ValueError("username already exists")

        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)
        user_doc = {
            "username": username,
            "password_salt": salt,
            "password_hash": password_hash,
            "role": role,
            "created_at": self._now_iso(),
        }
        self.collection.insert_one(user_doc)
        return {"username": username, "role": role}
    
    def authenticate_and_get_role(self, username: str, password: str) -> Optional[str]:
        """Return the user's role if credentials are valid, else None."""
        if self.collection is None:
            return None
        user_doc = self.collection.find_one({"username": username})
        if user_doc is None:
            return None
        salt = user_doc.get("password_salt", "")
        if self._hash_password(password, salt) == user_doc.get("password_hash"):
            return user_doc.get("role", "supplier")
        return None

    def authenticate_user(self, username: str, password: str) -> bool:
        if self.collection is None:
            return False
        user_doc = self.collection.find_one({"username": username})
        if user_doc is None:
            return False
        salt = user_doc.get("password_salt", "")
        return self._hash_password(password, salt) == user_doc.get("password_hash")

    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations=100_000
        ).hex()

    def _now_iso(self) -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
