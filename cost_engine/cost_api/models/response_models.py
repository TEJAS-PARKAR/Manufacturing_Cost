"""
Pydantic response models for the Manufacturing Cost Engine API.
Structures the cost breakdown returned by the engine.
"""

from pydantic import BaseModel, Field
from typing import Optional


class CostBreakdown(BaseModel):
    """
    Detailed cost breakdown for a single part.
    """
    raw_material_cost: float = Field(
        ...,
        description="Cost of raw material = finished_weight × material_rate",
    )
    conversion_cost: float = Field(
        ...,
        description="Total cost of manufacturing operations = sum(count × rate)",
    )
    coating_cost: float = Field(
        ...,
        description="Cost of surface treatment = area × coating_rate",
    )
    overhead: float = Field(
        ...,
        description="Overhead = 10% of conversion cost",
    )
    icc: float = Field(
        ...,
        description="ICC (Inspection/Compliance Cost) = 1% of raw material cost",
    )
    rejection: float = Field(
        ...,
        description="Rejection allowance = 1% of (raw material + conversion cost)",
    )
    profit: float = Field(
        ...,
        description="Profit = 10% of (raw material + conversion cost)",
    )
    total_cost: float = Field(
        ...,
        description="Total cost = sum of all cost components",
    )


class CostEstimationResponse(BaseModel):
    """
    Complete response from the /estimate-cost endpoint.
    """
    part_name: str = Field(
        ...,
        description="Name of the part",
    )
    material: str = Field(
        ...,
        description="Material grade used",
    )
    finished_weight_kg: float = Field(
        ...,
        description="Finished weight used for calculation (provided or auto-calculated)",
    )
    area_m2: float = Field(
        ...,
        description="Surface area used for calculation (provided or auto-calculated)",
    )
    cost_breakdown: CostBreakdown = Field(
        ...,
        description="Detailed cost breakdown",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Any warnings or notes about the calculation",
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
