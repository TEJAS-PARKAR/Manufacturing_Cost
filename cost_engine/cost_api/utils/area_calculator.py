"""
Area calculation utility.
Converts part dimensions from millimeters to square meters.
"""

import logging

logger = logging.getLogger(__name__)


class AreaCalculator:
    """
    Calculates surface area from part dimensions.
    Converts mm dimensions to m² for coating cost calculations.
    """

    @staticmethod
    def calculate_area_m2(length_mm: float, width_mm: float) -> float:
        """
        Calculate surface area in square meters from dimensions in millimeters.
        """
        if length_mm <= 0 or width_mm <= 0:
            raise ValueError(
                f"Dimensions must be positive. Got length={length_mm}, width={width_mm}"
            )

        area_mm2 = length_mm * width_mm
        area_m2 = area_mm2 / 1_000_000

        logger.debug(
            "Area calculation: %.2f mm × %.2f mm = %.9f m²",
            length_mm, width_mm, area_m2,
        )

        return round(area_m2, 9)
