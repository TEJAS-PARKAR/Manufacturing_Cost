from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class MaterialInput(BaseModel):
    type: Optional[str] = Field(default=None, description="Material grade or family")
    density: float = Field(..., gt=0, description="Density in kg/m³")
    rate_per_kg: float = Field(..., gt=0, description="Material rate in INR/kg")

    @field_validator("type")
    @classmethod
    def normalize_material_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized.upper() if normalized else None


class ProcessInput(BaseModel):
    name: str = Field(..., min_length=1, description="Process identifier")
    quantity: int = Field(default=1, ge=1, description="Number of times the process is applied")
    bends: Optional[int] = Field(default=None, ge=0, description="Number of bends for bending")
    holes: Optional[int] = Field(default=None, ge=0, description="Number of holes for drilling")
    machining_hours: Optional[float] = Field(default=None, ge=0, description="Machining hours")
    coating_thickness_um: Optional[float] = Field(default=None, ge=0, description="Coating thickness in microns")

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "_")


class CostEstimateRequest(BaseModel):
    part_name: Optional[str] = Field(default=None, description="Name of the part")
    quantity: int = Field(..., gt=0, description="Production quantity")
    length: float = Field(..., gt=0, description="Length in mm")
    width: float = Field(..., gt=0, description="Width in mm")
    height: float = Field(..., gt=0, description="Height in mm")
    thickness: float = Field(..., gt=0, description="Thickness in mm")
    material: MaterialInput
    processes: List[ProcessInput] = Field(default_factory=list)

    @field_validator("part_name")
    @classmethod
    def normalize_part_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized if normalized else None


class CostComponent(BaseModel):
    name: str
    amount: float


class CostBreakdown(BaseModel):
    raw_material_cost: float
    process_cost: float
    overhead_cost: float
    total_manufacturing_cost: float
    cost_per_piece: float


class CostEstimateResponse(BaseModel):
    part_name: str
    quantity: int
    material: dict
    processes: List[dict]
    cost_breakdown: CostBreakdown
    notes: List[str] = Field(default_factory=list)


class ChatCostRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Plain-language request from the user")


class ChatCostResponse(BaseModel):
    extracted_data: Dict[str, Any]
    prediction: Dict[str, Any]
    notes: List[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
