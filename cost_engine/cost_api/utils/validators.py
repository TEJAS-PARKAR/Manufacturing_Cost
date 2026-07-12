"""
Input validation utilities for the Manufacturing Cost Engine.
"""

import logging

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Validates cost estimation inputs against known rate databases.
    """

    def __init__(
        self,
        known_materials: set[str],
        known_processes: set[str],
        known_coatings: set[str],
    ):
        """
        Initialize validator with known lookup values.
        """
        self.known_materials = known_materials
        self.known_processes = known_processes
        self.known_coatings = known_coatings

    def validate_material(self, material: str) -> list[str]:
        """
        Check if material exists in the rate database.
        """
        warnings = []
        material_upper = material.strip().upper()
        if material_upper not in self.known_materials:
            warnings.append(
                f"Material '{material}' not found in rate database. "
                f"Available materials: {sorted(self.known_materials)}"
            )
            logger.warning("Unknown material: %s", material)
        return warnings

    def validate_operations(self, operations: dict[str, int]) -> list[str]:
        """
        Check if all operations exist in the process rate database.
        """
        warnings = []
        for op_name, count in operations.items():
            if count > 0 and op_name.lower() not in self.known_processes:
                warnings.append(
                    f"Process '{op_name}' not found in rate database. "
                    f"It will be skipped. "
                    f"Available processes: {sorted(self.known_processes)}"
                )
                logger.warning("Unknown process: %s", op_name)
        return warnings

    def validate_coating(self, coating: str | None) -> list[str]:
        """
        Check if surface treatment exists in the coating rate database.
        """
        warnings = []
        if coating and coating.strip().lower() not in self.known_coatings:
            warnings.append(
                f"Coating '{coating}' not found in rate database. "
                f"Coating cost will be 0. "
                f"Available coatings: {sorted(self.known_coatings)}"
            )
            logger.warning("Unknown coating: %s", coating)
        return warnings
