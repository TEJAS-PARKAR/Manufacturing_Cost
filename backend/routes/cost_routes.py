from fastapi import APIRouter, HTTPException, status

from backend.models import CostEstimateRequest, CostEstimateResponse, ErrorResponse
from backend.services.cost_service import CostService

router = APIRouter(tags=["Costing"])
service = CostService()


@router.get("/health", include_in_schema=False)
def health() -> dict:
    return {"status": "ok", "service": "manufacturing-cost-api"}


@router.post(
    "/estimate-cost",
    response_model=CostEstimateResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def estimate_cost(payload: CostEstimateRequest) -> CostEstimateResponse:
    try:
        result = service.estimate(payload)
        return CostEstimateResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
