from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.cost_routes import router

app = FastAPI(
    title="AI-Powered Supplier Negotiation & Cost Estimation Copilot API",
    version="2.0.0",
    description="Supplier negotiation workflow for document extraction, memory-preserving discussions, review routing, and Tata Motors cost validation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
