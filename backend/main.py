import os
from pathlib import Path

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.cost_routes import router

_cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
_cors_origins = [origin.strip() for origin in _cors_origins_raw.split(",") if origin.strip()]

app = FastAPI(
    title="AI-Powered Supplier Negotiation & Cost Estimation Copilot API",
    version="2.0.0",
    description="Supplier negotiation workflow for document extraction, memory-preserving discussions, review routing, and Tata Motors cost validation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
