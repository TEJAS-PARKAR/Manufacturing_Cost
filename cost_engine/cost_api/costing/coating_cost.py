"""
Coating cost calculator module.
Calculates surface treatment cost based on area and coating rate.
"""

import logging

logger = logging.getLogger(__name__)


class CoatingCostCalculator:
    """
    Calculates the surface treatment / coating cost.
    """

    def __init__(self, coating_rates: dict[str, float]):
        self.coating_rates = coating_rates

    def calculate(
        self,
        surface_treatment: str | None,
        area_m2: float,
    ) -> tuple[float, list[str]]:
        warnings = []

        if not surface_treatment:
            logger.info("No surface treatment specified. Coating cost = 0.")
            return 0.0, warnings

        coating_lower = surface_treatment.strip().lower()
        rate = self.coating_rates.get(coating_lower)

        if rate is None:
            warnings.append(
                f"Coating '{surface_treatment}' not found in rate database. "
                f"Coating cost set to 0. "
                f"Available coatings: {sorted(self.coating_rates.keys())}"
            )
            logger.warning("Unknown coating '%s'. Cost = 0.", surface_treatment)
            return 0.0, warnings

        cost = area_m2 * rate

        logger.info(
            "Coating cost: %.9f m2 x %.2f INR/m2 = %.2f INR [%s]",
            area_m2, rate, cost, coating_lower,
        )

        return round(cost, 2), warnings
