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
# Explicit origins from .env (optional, for custom/fixed domains)
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

# Configurable regex for dynamic origins (Codespaces, Vercel, etc.)
# Set CORS_ORIGIN_REGEX in .env to match your specific deployment domains.
cors_origin_regex = (
    r"https://.*\.app\.github\.dev"
    r"|https://.*\.vercel\.app"
    r"|http://localhost:\d+"
    r"|http://127\.0\.0\.1:\d+"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
