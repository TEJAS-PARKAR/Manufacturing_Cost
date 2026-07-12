"""
Pydantic request models for the Manufacturing Cost Engine API.
Validates and structures incoming cost estimation requests.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class OperationsModel(BaseModel):
    """
    Manufacturing operations with their counts.
    """
    shearing: int = Field(default=0, ge=0, description="Number of shearing operations")
    blanking: int = Field(default=0, ge=0, description="Number of blanking operations")
    piercing: int = Field(default=0, ge=0, description="Number of piercing operations")
    forming: int = Field(default=0, ge=0, description="Number of forming operations")
    bending: int = Field(default=0, ge=0, description="Number of bending operations")
    welding: int = Field(default=0, ge=0, description="Number of welding operations")
    machining: int = Field(default=0, ge=0, description="Number of machining operations")
    cutting: int = Field(default=0, ge=0, description="Number of cutting operations")

    def get_active_operations(self) -> dict[str, int]:
        """Return only operations with count > 0."""
        return {
            name: count
            for name, count in self.model_dump().items()
            if count > 0
        }

    def has_any_operation(self) -> bool:
        """Check if at least one operation is specified."""
        return any(count > 0 for count in self.model_dump().values())


class CostEstimationRequest(BaseModel):
    """
    Input model for the /estimate-cost endpoint.
    """
    part_name: str = Field(
        ...,
        min_length=1,
        description="Name of the part being estimated",
    )
    material: str = Field(
        ...,
        min_length=1,
        description="Material grade (e.g., E46, CR4, SS304)",
    )
    length_mm: float = Field(
        ...,
        gt=0,
        description="Part length in millimeters",
    )
    width_mm: float = Field(
        ...,
        gt=0,
        description="Part width in millimeters",
    )
    thickness_mm: float = Field(
        ...,
        gt=0,
        description="Part thickness in millimeters",
    )
    finished_weight_kg: Optional[float] = Field(
        default=None,
        gt=0,
        description="Finished weight in kg. Auto-calculated if not provided.",
    )
    area_m2: Optional[float] = Field(
        default=None,
        gt=0,
        description="Surface area in m². Auto-calculated if not provided.",
    )
    operations: OperationsModel = Field(
        default_factory=OperationsModel,
        description="Manufacturing operations and their counts",
    )
    surface_treatment: Optional[str] = Field(
        default=None,
        description="Surface treatment type (e.g., powder_coating, zinc_plating)",
    )
    quantity: Optional[int] = Field(
        default=None,
        gt=0,
        description="Number of parts (for reference only)",
    )

    @field_validator("material")
    @classmethod
    def normalize_material(cls, v: str) -> str:
        """Normalize material name to uppercase for consistent lookups."""
        return v.strip().upper()

    @field_validator("surface_treatment")
    @classmethod
    def normalize_surface_treatment(cls, v: Optional[str]) -> Optional[str]:
        """Normalize surface treatment to lowercase snake_case."""
        if v is None or v.strip() == "":
            return None
        return v.strip().lower().replace(" ", "_")
