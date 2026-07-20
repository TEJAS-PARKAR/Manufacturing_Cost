from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

try:
    # pyrefly: ignore [missing-import]
    from pymongo import MongoClient
except Exception:  # pragma: no cover - optional dependency guard
    MongoClient = None


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


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

        print("MongoClient imported:", MongoClient is not None)

        if MongoClient is None:
            print("pymongo not installed")
            return None

        uri = cls._build_uri()
        print("Generated URI:", uri)

        if not uri:
            print("No Mongo URI generated")
            return None

        try:
            cls._client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000
            )

            cls._client.admin.command("ping")

            print("✅ MongoDB Connected Successfully")

            return cls._client

        except Exception as e:
            print("❌ MongoDB Connection Failed")
            print("ERROR:", str(e))
            cls._client = None
            return None


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
