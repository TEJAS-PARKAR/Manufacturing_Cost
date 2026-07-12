"""
Conversion cost calculator module.
Calculates total cost of all manufacturing operations.
"""

import logging

logger = logging.getLogger(__name__)


class ConversionCostCalculator:
    """
    Calculates the total conversion (manufacturing) cost.
    """

    def __init__(self, process_rates: dict[str, float]):
        self.process_rates = process_rates

    def calculate(self, operations: dict[str, int]) -> tuple[float, list[str]]:
        warnings = []
        total_cost = 0.0

        for op_name, count in operations.items():
            if count <= 0:
                continue

            op_lower = op_name.strip().lower()
            rate = self.process_rates.get(op_lower)

            if rate is None:
                warnings.append(
                    f"Process '{op_name}' not found in rate database. Skipping."
                )
                logger.warning("Unknown process '%s' skipped.", op_name)
                continue

            op_cost = count * rate
            total_cost += op_cost

            logger.debug(
                "  %s: %d x %.2f = %.2f INR",
                op_lower, count, rate, op_cost,
            )

        logger.info("Conversion cost: %.2f INR", total_cost)

        return round(total_cost, 2), warnings
