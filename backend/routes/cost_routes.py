# pyrefly: ignore [missing-import]
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.models import (
    ChatCostRequest,
    ChatCostResponse,
    CostEstimateRequest,
    CostEstimateResponse,
    ErrorResponse,
    SupplierMessageRequest,
    SupplierSessionRequest,
    SupplierSessionResponse,
)
from backend.services.chat_service import ChatCostService
from backend.services.cost_service import CostService
from backend.services.negotiation_service import SupplierNegotiationService

router = APIRouter(tags=["Costing"])
service = CostService()
chat_service = ChatCostService()
negotiation_service = SupplierNegotiationService()


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


@router.post(
    "/supplier/session/start",
    response_model=SupplierSessionResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def start_supplier_session(payload: SupplierSessionRequest) -> SupplierSessionResponse:
    try:
        result = negotiation_service.start_session(payload.employee_id, payload.part_number)
        return SupplierSessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/supplier/session/context",
    response_model=SupplierSessionResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def get_supplier_session_context(employee_id: str, part_number: str) -> SupplierSessionResponse:
    try:
        result = negotiation_service.get_session_context(employee_id, part_number)
        return SupplierSessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/supplier/session/message",
    response_model=SupplierSessionResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def supplier_session_message(payload: SupplierMessageRequest) -> SupplierSessionResponse:
    try:
        result = negotiation_service.record_supplier_message(payload.employee_id, payload.part_number, payload.message)
        return SupplierSessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/supplier/session/upload-excel",
    response_model=SupplierSessionResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def supplier_session_upload_excel(employee_id: str, part_number: str, file: UploadFile = File(...)) -> SupplierSessionResponse:
    try:
        content = await file.read()
        result = negotiation_service.ingest_excel(employee_id, part_number, content, file.filename or "costing.xlsx")
        return SupplierSessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/supplier/session/submit-review",
    response_model=SupplierSessionResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def submit_supplier_session(employee_id: str, part_number: str) -> SupplierSessionResponse:
    try:
        result = negotiation_service.submit_for_review(employee_id, part_number)
        return SupplierSessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/supplier/session/review",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def get_supplier_review_dashboard(employee_id: str, part_number: str) -> dict:
    try:
        return negotiation_service.get_review_dashboard(employee_id, part_number)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/supplier/session/approve",
    response_model=SupplierSessionResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def approve_supplier_session(employee_id: str, part_number: str, payload: dict | None = None) -> SupplierSessionResponse:
    try:
        approval_payload = payload or {"approved_values": {}}
        result = negotiation_service.approve_cost_inputs(employee_id, part_number, approval_payload)
        return SupplierSessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
