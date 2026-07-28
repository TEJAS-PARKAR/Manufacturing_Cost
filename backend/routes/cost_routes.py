# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status

from backend.models import (
    ChatCostRequest,
    ChatCostResponse,
    CostEstimateRequest,
    CostEstimateResponse,
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    SupplierMessageRequest,
    SupplierSessionRequest,
    SupplierSessionResponse,
)
from backend.services.auth_service import create_token, verify_token
from backend.services.chat_service import ChatCostService
from backend.services.cost_service import CostService
from backend.services.negotiation_service import SupplierNegotiationService
from backend.services.user_service import UserService

router = APIRouter(tags=["Costing"])
service = CostService()
chat_service = ChatCostService()
negotiation_service = SupplierNegotiationService()
user_service = UserService()

def get_identity(authorization: str = Header(default="")) -> dict:
    """Validate the Bearer token and return {sub, role, exp}."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or malformed token")
    token = authorization.split(" ", 1)[1].strip()
    identity = verify_token(token)
    if identity is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return identity


def require_own_or_tata(identity: dict, employee_id: str) -> None:
    """Supplier may only access their own employee_id; Tata may access any."""
    if identity["role"] == "tata":
        return
    if identity["role"] == "supplier" and identity["sub"] == employee_id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this resource")


def require_tata(identity: dict) -> None:
    """Only Tata reviewers may perform review/approve/reject."""
    if identity["role"] != "tata":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tata reviewer role required")

@router.post("/login", response_model=LoginResponse,
             responses={401: {"model": ErrorResponse}})
def login(payload: LoginRequest) -> LoginResponse:
    role = user_service.authenticate_and_get_role(payload.username, payload.password)
    if role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = create_token(subject=payload.username, role=role)
    return LoginResponse(token=token, role=role, username=payload.username)

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


@router.post("/supplier/session/start", response_model=SupplierSessionResponse,
             responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def start_supplier_session(payload: SupplierSessionRequest,
                           identity: dict = Depends(get_identity)) -> SupplierSessionResponse:
    require_own_or_tata(identity, payload.employee_id)
    try:
        result = negotiation_service.start_session(payload.employee_id, payload.part_number)
        return SupplierSessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/supplier/session/context", response_model=SupplierSessionResponse,
            responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def get_supplier_session_context(employee_id: str, part_number: str,
                                 identity: dict = Depends(get_identity)) -> SupplierSessionResponse:
    require_own_or_tata(identity, employee_id)
    try:
        result = negotiation_service.get_session_context(employee_id, part_number)
        return SupplierSessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/supplier/session/message", response_model=SupplierSessionResponse,
             responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def supplier_session_message(payload: SupplierMessageRequest,
                             identity: dict = Depends(get_identity)) -> SupplierSessionResponse:
    require_own_or_tata(identity, payload.employee_id)
    try:
        result = negotiation_service.record_supplier_message(payload.employee_id, payload.part_number, payload.message)
        return SupplierSessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/supplier/session/upload-excel", response_model=SupplierSessionResponse,
             responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def supplier_session_upload_excel(employee_id: str, part_number: str,
                                        file: UploadFile = File(...),
                                        identity: dict = Depends(get_identity)) -> SupplierSessionResponse:
    require_own_or_tata(identity, employee_id)
    try:
        content = await file.read()
        result = negotiation_service.ingest_excel(employee_id, part_number, content, file.filename or "costing.xlsx")
        return SupplierSessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/supplier/session/submit-review", response_model=SupplierSessionResponse,
             responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def submit_supplier_session(employee_id: str, part_number: str,
                            identity: dict = Depends(get_identity)) -> SupplierSessionResponse:
    require_own_or_tata(identity, employee_id)
    try:
        result = negotiation_service.submit_for_review(employee_id, part_number)
        return SupplierSessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/supplier/session/negotiate")
def negotiate(payload: SupplierMessageRequest,
              identity: dict = Depends(get_identity)):
    require_own_or_tata(identity, payload.employee_id)
    return negotiation_service.run_negotiation(payload.employee_id, payload.part_number, payload.message)

@router.get("/supplier/session/review",
            responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def get_supplier_review_dashboard(employee_id: str, part_number: str,
                                  identity: dict = Depends(get_identity)) -> dict:
    require_tata(identity)
    try:
        return negotiation_service.get_review_dashboard(employee_id, part_number)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/supplier/session/approve", response_model=SupplierSessionResponse,
             responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def approve_supplier_session(employee_id: str, part_number: str, payload: dict | None = None,
                             identity: dict = Depends(get_identity)) -> SupplierSessionResponse:
    require_tata(identity)
    try:
        approval_payload = payload or {"approved_values": {}}
        result = negotiation_service.approve_cost_inputs(employee_id, part_number, approval_payload)
        return SupplierSessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/supplier/session/reject")
def reject_offer(employee_id: str, part_number: str,
                 reason: str = "Cost exceeds expected benchmark",
                 identity: dict = Depends(get_identity)):
    require_tata(identity)
    return negotiation_service.reject_offer(employee_id, part_number, reason)