from __future__ import annotations

import hashlib
import os
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

    def register_user(self, username: str, password: str) -> dict[str, Any]:
        if not username or not password:
            raise ValueError("username and password are required")

        if self.collection is None:
            raise RuntimeError("MongoDB connection is not available")

        existing = self.collection.find_one({"username": username})
        if existing is not None:
            raise ValueError("username already exists")

        user_doc = {
            "username": username,
            "password_hash": self._hash_password(password),
            "created_at": self._now_iso(),
        }
        self.collection.insert_one(user_doc)
        return {"username": username, "password_hash": user_doc["password_hash"]}

    def authenticate_user(self, username: str, password: str) -> bool:
        if self.collection is None:
            return False
        user_doc = self.collection.find_one({"username": username})
        if user_doc is None:
            return False
        return self._hash_password(password) == user_doc.get("password_hash")

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _now_iso(self) -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
