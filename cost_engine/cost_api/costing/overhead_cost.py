"""
Overhead cost calculator module.
Calculates overhead, ICC, and rejection costs.
"""

import logging
from cost_api.config import OVERHEAD_PERCENTAGE, ICC_PERCENTAGE, REJECTION_PERCENTAGE

logger = logging.getLogger(__name__)


class OverheadCostCalculator:
    """
    Calculates overhead-related costs.
    """

    def __init__(
        self,
        overhead_pct: float = OVERHEAD_PERCENTAGE,
        icc_pct: float = ICC_PERCENTAGE,
        rejection_pct: float = REJECTION_PERCENTAGE,
    ):
        self.overhead_pct = overhead_pct
        self.icc_pct = icc_pct
        self.rejection_pct = rejection_pct

    def calculate_overhead(self, conversion_cost: float) -> float:
        overhead = self.overhead_pct * conversion_cost
        logger.info(
            "Overhead: %.1f%% x %.2f = %.2f INR",
            self.overhead_pct * 100, conversion_cost, overhead,
        )
        return round(overhead, 2)

    def calculate_icc(self, raw_material_cost: float) -> float:
        icc = self.icc_pct * raw_material_cost
        logger.info(
            "ICC: %.1f%% x %.2f = %.2f INR",
            self.icc_pct * 100, raw_material_cost, icc,
        )
        return round(icc, 2)

    def calculate_rejection(
        self,
        raw_material_cost: float,
        conversion_cost: float,
    ) -> float:
        base = raw_material_cost + conversion_cost
        rejection = self.rejection_pct * base
        logger.info(
            "Rejection: %.1f%% x (%.2f + %.2f) = %.2f INR",
            self.rejection_pct * 100, raw_material_cost, conversion_cost, rejection,
        )
        return round(rejection, 2)
