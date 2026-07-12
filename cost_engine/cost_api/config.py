"""
Configuration module for the Manufacturing Cost Engine.
Contains default rates, percentages, and material densities.

These values are used as fallbacks when Excel rate files
are not available or when a lookup fails.
"""

import logging

logger = logging.getLogger(__name__)

# Default Material Rates (INR per kg)
DEFAULT_MATERIAL_RATES: dict[str, float] = {
    "E46": 60.3,
    "CR4": 58.0,
    "SS304": 210.0,
    "SS316": 250.0,
    "MS": 55.0,
    "AL6061": 180.0,
}

# Default Process Rates (INR per operation)
DEFAULT_PROCESS_RATES: dict[str, float] = {
    "shearing": 1.86,
    "blanking": 1.60,
    "piercing": 1.60,
    "forming": 1.60,
    "welding": 6.50,
    "machining": 5.00,
    "cutting": 2.50,
    "bending": 1.60,
}

# Default Coating Rates (INR per m²)
DEFAULT_COATING_RATES: dict[str, float] = {
    "powder_coating": 102.04,
    "primer": 28.00,
    "zinc_plating": 17.50,
    "chrome_plating": 85.00,
    "painting": 45.00,
    "anodizing": 60.00,
    "galvanizing": 35.00,
    "heat_treatment": 25.00,
}

# Material Densities (kg/m³)
MATERIAL_DENSITIES: dict[str, float] = {
    "E46": 7850.0,
    "CR4": 7850.0,
    "SS304": 8000.0,
    "SS316": 8000.0,
    "MS": 7850.0,
    "AL6061": 2700.0,
}

DEFAULT_DENSITY: float = 7850.0

# Overhead / Cost Percentages
OVERHEAD_PERCENTAGE: float = 0.10
ICC_PERCENTAGE: float = 0.01
REJECTION_PERCENTAGE: float = 0.01
PROFIT_PERCENTAGE: float = 0.10

# API Configuration
API_HOST: str = "0.0.0.0"
API_PORT: int = 8000
API_TITLE: str = "Manufacturing Cost Engine"
API_VERSION: str = "1.0.0"
