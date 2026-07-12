"""
Profit calculator module.
Calculates profit margin based on raw material and conversion costs.
"""

import logging
from cost_api.config import PROFIT_PERCENTAGE

logger = logging.getLogger(__name__)


class ProfitCostCalculator:
    """
    Calculates the profit component of the total cost.
    """

    def __init__(self, profit_pct: float = PROFIT_PERCENTAGE):
        self.profit_pct = profit_pct

    def calculate(
        self,
        raw_material_cost: float,
        conversion_cost: float,
    ) -> float:
        base = raw_material_cost + conversion_cost
        profit = self.profit_pct * base
        logger.info(
            "Profit: %.1f%% x (%.2f + %.2f) = %.2f INR",
            self.profit_pct * 100, raw_material_cost, conversion_cost, profit,
        )
        return round(profit, 2)
