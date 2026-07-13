from __future__ import annotations

from backend.cost_engine.material_cost import MaterialCostCalculator
from backend.cost_engine.process_cost import ProcessCostCalculator
from backend.cost_engine.overhead_cost import OverheadCostCalculator


class CostEstimator:
    def __init__(self) -> None:
        self.material_calculator = MaterialCostCalculator()
        self.process_calculator = ProcessCostCalculator()
        self.overhead_calculator = OverheadCostCalculator()

    def estimate(self, request: object) -> dict:
        dimensions = {
            "length": request.length,
            "width": request.width,
            "height": request.height,
            "thickness": request.thickness,
        }
        material_summary = self.material_calculator.calculate(
            material={
                "type": request.material.type or "UNKNOWN",
                "density": request.material.density,
                "rate_per_kg": request.material.rate_per_kg,
            },
            dimensions=dimensions,
            quantity=request.quantity,
        )
        process_cost = self.process_calculator.calculate([p.model_dump() for p in request.processes])
        overhead_cost = self.overhead_calculator.calculate(process_cost, material_summary["raw_material_cost_total"])
        total_cost = round(material_summary["raw_material_cost_total"] + process_cost + overhead_cost, 2)
        cost_per_piece = round(total_cost / request.quantity, 2)
        return {
            "part_name": request.part_name or "Unnamed Part",
            "quantity": request.quantity,
            "material": {
                "type": request.material.type or "UNKNOWN",
                "density": request.material.density,
                "rate_per_kg": request.material.rate_per_kg,
            },
            "processes": [p.model_dump() for p in request.processes],
            "cost_breakdown": {
                "raw_material_cost": round(material_summary["raw_material_cost_total"], 2),
                "process_cost": round(process_cost, 2),
                "overhead_cost": round(overhead_cost, 2),
                "total_manufacturing_cost": round(total_cost, 2),
                "cost_per_piece": round(cost_per_piece, 2),
            },
            "notes": [
                "Calculation uses deterministic rule-based estimates.",
                "Material cost is based on volume and density.",
            ],
        }
