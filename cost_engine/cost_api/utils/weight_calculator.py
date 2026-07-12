"""
Weight calculation utility.
Calculates finished weight from part dimensions and material density.
"""

import logging
from cost_api.config import MATERIAL_DENSITIES, DEFAULT_DENSITY

logger = logging.getLogger(__name__)


class WeightCalculator:
    """
    Calculates part weight from dimensions and material density.
    """

    @staticmethod
    def calculate_weight_kg(
        length_mm: float,
        width_mm: float,
        thickness_mm: float,
        material: str,
    ) -> float:
        """
        Calculate part weight in kilograms from dimensions and material.
        """
        if length_mm <= 0 or width_mm <= 0 or thickness_mm <= 0:
            raise ValueError(
                f"All dimensions must be positive. "
                f"Got L={length_mm}, W={width_mm}, T={thickness_mm}"
            )

        # Look up material density
        material_upper = material.strip().upper()
        density = MATERIAL_DENSITIES.get(material_upper, DEFAULT_DENSITY)

        if material_upper not in MATERIAL_DENSITIES:
            logger.warning(
                "Density for material '%s' not found. Using default density: %.1f kg/m3",
                material, DEFAULT_DENSITY,
            )

        # Calculate volume in m³ (convert from mm³)
        volume_mm3 = length_mm * width_mm * thickness_mm
        volume_m3 = volume_mm3 / 1_000_000_000

        # Calculate weight
        weight_kg = volume_m3 * density

        logger.debug(
            "Weight calculation: %.2f × %.2f × %.2f mm = %.9f m3 × %.1f kg/m3 = %.4f kg",
            length_mm, width_mm, thickness_mm, volume_m3, density, weight_kg,
        )

        return round(weight_kg, 4)
