from __future__ import annotations

from backend.cost_engine.final_cost import CostEstimator
from backend.models import CostEstimateRequest


class CostService:
    def __init__(self) -> None:
        self.estimator = CostEstimator()

    def estimate(self, request: CostEstimateRequest) -> dict:
        if not request.processes:
            raise ValueError("At least one process must be selected.")
        return self.estimator.estimate(request)
