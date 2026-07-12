"""
Material cost calculator module.
Calculates raw material cost based on weight and material rate.
"""

import logging

logger = logging.getLogger(__name__)


class MaterialCostCalculator:
    """
    Calculates the raw material cost for a part.
    """

    def __init__(self, material_rates: dict[str, float]):
        self.material_rates = material_rates

    def calculate(self, material: str, finished_weight_kg: float) -> tuple[float, list[str]]:
        warnings = []
        material_upper = material.strip().upper()

        rate = self.material_rates.get(material_upper)
        if rate is None:
            raise ValueError(
                f"Material '{material}' not found in rate database. "
                f"Available materials: {sorted(self.material_rates.keys())}"
            )

        cost = finished_weight_kg * rate

        logger.info(
            "Material cost: %.4f kg x %.2f INR/kg = %.2f INR [%s]",
            finished_weight_kg, rate, cost, material_upper,
        )

        return round(cost, 2), warnings
