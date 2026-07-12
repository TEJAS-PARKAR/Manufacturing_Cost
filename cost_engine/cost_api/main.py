"""
Main FastAPI application file.
Defines endpoints, CORS, database reload, and handles API execution.
"""

import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from cost_api.config import API_TITLE, API_VERSION
from cost_api.database.loaders import RateDatabase
from cost_api.costing.cost_engine import CostEngine
from cost_api.models.request_models import CostEstimationRequest
from cost_api.models.response_models import CostEstimationResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="Rule-based costing engine for manufacturing parts.",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Rate Database & Cost Engine
try:
    logger.info("Initializing Rate Database and Cost Engine...")
    db = RateDatabase()
    cost_engine = CostEngine(db)
    logger.info("Cost Engine successfully initialized.")
except Exception as e:
    logger.error("Failed to initialize database or engine: %s", e, exc_info=True)
    raise RuntimeError(f"Engine Startup Failure: {e}")


@app.get("/", tags=["Health"])
async def root():
    """Health check and engine info endpoint."""
    return {
        "status": "online",
        "engine": API_TITLE,
        "version": API_VERSION,
        "database": {
            "materials": list(db.material_rates.keys()),
            "processes": list(db.process_rates.keys()),
            "coatings": list(db.coating_rates.keys()),
        }
    }


@app.post(
    "/estimate-cost",
    response_model=CostEstimationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Input Data"},
        500: {"model": ErrorResponse, "description": "Internal Calculation Error"},
    },
    tags=["Costing"],
)
async def estimate_cost(request: CostEstimationRequest):
    """
    Estimate the manufacturing cost of a part.
    """
    try:
        response = cost_engine.estimate_cost(request)
        return response
    except ValueError as ve:
        logger.error("Validation error during estimation: %s", ve)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation Error: {str(ve)}",
        )
    except Exception as e:
        logger.error("Unexpected cost estimation error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation Error: {str(e)}",
        )


@app.post("/reload-rates", tags=["Administration"])
async def reload_rates():
    """
    Reload rate tables.
    """
    try:
        db.reload()
        global cost_engine
        cost_engine = CostEngine(db)
        logger.info("Rates successfully reloaded and engine updated.")
        return {
            "status": "success",
            "message": "Rate databases reloaded successfully",
            "active_materials_count": len(db.material_rates),
            "active_processes_count": len(db.process_rates),
            "active_coatings_count": len(db.coating_rates),
        }
    except Exception as e:
        logger.error("Failed to reload rates: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reload Error: {str(e)}",
        )
