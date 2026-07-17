from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

try:
    from pymongo import MongoClient
except Exception:  # pragma: no cover - optional dependency guard
    MongoClient = None


def load_environment() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_environment()


class MongoConnection:
    _client = None
    _database = None

    @classmethod
    def _build_uri(cls) -> Optional[str]:
        uri = os.getenv("MONGODB_URI", "").strip()
        if uri:
            if "<" not in uri and ">" not in uri:
                return uri

            username = os.getenv("MONGODB_USERNAME", "").strip()
            password = os.getenv("MONGODB_PASSWORD", "").strip()
            if username and password:
                uri = uri.replace("<tml_username>", username)
                uri = uri.replace("<username>", username)
                uri = uri.replace("<tml_password>", password)
                uri = uri.replace("<password>", password)
                return uri
            return None

        username = os.getenv("MONGODB_USERNAME", "").strip()
        password = os.getenv("MONGODB_PASSWORD", "").strip()
        host = os.getenv("MONGODB_HOST") or os.getenv("MONGODB_CLUSTER") or "localhost"
        if username and password:
            return (
                f"mongodb+srv://{quote_plus(username)}:{quote_plus(password)}@{host}/"
                f"?retryWrites=true&w=majority&appName=CostNegotiator"
            )
        return None

    @classmethod
    def get_client(cls):
        if cls._client is not None:
            return cls._client
        if MongoClient is None:
            return None

        uri = cls._build_uri()
        if not uri:
            return None

        try:
            cls._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            cls._client.admin.command("ping")
        except Exception:
            cls._client = None
        return cls._client

    @classmethod
    def get_database(cls, database_name: Optional[str] = None):
        if cls._database is not None:
            return cls._database

        client = cls.get_client()
        if client is None:
            return None

        db_name = database_name or os.getenv("MONGODB_DB_NAME", "manufacturing_cost")
        cls._database = client[db_name]
        return cls._database

    @classmethod
    def get_collection(cls, collection_name: str, database_name: Optional[str] = None):
        database = cls.get_database(database_name)
        if database is None:
            return None
        return database[collection_name]
