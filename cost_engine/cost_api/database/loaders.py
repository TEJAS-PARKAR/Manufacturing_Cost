"""
Database loader module.
Loads rate tables from Excel files using Pandas and OpenPyXL.
"""

import logging
from pathlib import Path
import pandas as pd

from cost_api.config import (
    DEFAULT_MATERIAL_RATES,
    DEFAULT_PROCESS_RATES,
    DEFAULT_COATING_RATES,
)

logger = logging.getLogger(__name__)

DATABASE_DIR = Path(__file__).parent


class RateDatabase:
    """
    Loads and provides access to rate tables from Excel files.
    """

    def __init__(self):
        self.material_rates: dict[str, float] = {}
        self.process_rates: dict[str, float] = {}
        self.coating_rates: dict[str, float] = {}

        self._load_all()

    def _load_all(self) -> None:
        self.material_rates = self._load_material_rates()
        self.process_rates = self._load_process_rates()
        self.coating_rates = self._load_coating_rates()

        logger.info(
            "Rate database loaded: %d materials, %d processes, %d coatings",
            len(self.material_rates),
            len(self.process_rates),
            len(self.coating_rates),
        )

    def _load_material_rates(self) -> dict[str, float]:
        filepath = DATABASE_DIR / "materials.xlsx"
        try:
            df = pd.read_excel(filepath, engine="openpyxl")
            rates = {}
            for _, row in df.iterrows():
                material = str(row["Material"]).strip().upper()
                rate = float(row["Rate_per_kg"])
                rates[material] = rate
            logger.info("Loaded %d material rates from %s", len(rates), filepath)
            return rates
        except FileNotFoundError:
            logger.warning("Material rates file not found: %s. Using defaults.", filepath)
            return DEFAULT_MATERIAL_RATES.copy()
        except Exception as e:
            logger.error("Error loading material rates: %s. Using defaults.", e)
            return DEFAULT_MATERIAL_RATES.copy()

    def _load_process_rates(self) -> dict[str, float]:
        filepath = DATABASE_DIR / "process_rates.xlsx"
        try:
            df = pd.read_excel(filepath, engine="openpyxl")
            rates = {}
            for _, row in df.iterrows():
                process = str(row["Process"]).strip().lower()
                cost = float(row["Cost"])
                rates[process] = cost
            logger.info("Loaded %d process rates from %s", len(rates), filepath)
            return rates
        except FileNotFoundError:
            logger.warning("Process rates file not found: %s. Using defaults.", filepath)
            return DEFAULT_PROCESS_RATES.copy()
        except Exception as e:
            logger.error("Error loading process rates: %s. Using defaults.", e)
            return DEFAULT_PROCESS_RATES.copy()

    def _load_coating_rates(self) -> dict[str, float]:
        filepath = DATABASE_DIR / "coating_rates.xlsx"
        try:
            df = pd.read_excel(filepath, engine="openpyxl")
            rates = {}
            for _, row in df.iterrows():
                coating = str(row["Coating"]).strip().lower().replace(" ", "_")
                rate = float(row["Rate_per_m2"])
                rates[coating] = rate
            logger.info("Loaded %d coating rates from %s", len(rates), filepath)
            return rates
        except FileNotFoundError:
            logger.warning("Coating rates file not found: %s. Using defaults.", filepath)
            return DEFAULT_COATING_RATES.copy()
        except Exception as e:
            logger.error("Error loading coating rates: %s. Using defaults.", e)
            return DEFAULT_COATING_RATES.copy()

    def get_material_rate(self, material: str) -> float | None:
        return self.material_rates.get(material.strip().upper())

    def get_process_rate(self, process: str) -> float | None:
        return self.process_rates.get(process.strip().lower())

    def get_coating_rate(self, coating: str) -> float | None:
        return self.coating_rates.get(coating.strip().lower())

    def reload(self) -> None:
        logger.info("Reloading rate database...")
        self._load_all()
