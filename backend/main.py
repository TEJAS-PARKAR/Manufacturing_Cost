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

app = FastAPI(
    title="AI-Powered Supplier Negotiation & Cost Estimation Copilot API",
    version="2.0.0",
    description="Supplier negotiation workflow for document extraction, memory-preserving discussions, review routing, and Tata Motors cost validation.",
)

# Use configured CORS origins from .env, fallback to localhost defaults
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
