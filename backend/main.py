from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.cost_routes import router

app = FastAPI(
    title="Manufacturing Cost Copilot API",
    version="1.0.0",
    description="Chat-driven manufacturing cost estimation with LLM-style extraction and XGBoost-powered prediction.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
