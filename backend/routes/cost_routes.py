from fastapi import APIRouter, HTTPException, status

from backend.models import (
    ChatCostRequest,
    ChatCostResponse,
    CostEstimateRequest,
    CostEstimateResponse,
    ErrorResponse,
)
from backend.services.chat_service import ChatCostService
from backend.services.cost_service import CostService

router = APIRouter(tags=["Costing"])
service = CostService()
chat_service = ChatCostService()


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


@router.post(
    "/chat-cost",
    response_model=ChatCostResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def chat_cost(payload: ChatCostRequest) -> ChatCostResponse:
    try:
        result = chat_service.handle_message(payload.message)
        return ChatCostResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
