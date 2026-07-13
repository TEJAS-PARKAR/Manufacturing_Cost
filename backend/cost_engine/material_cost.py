from __future__ import annotations

from math import pi


class MaterialCostCalculator:
    def calculate(self, material: dict, dimensions: dict, quantity: int) -> dict:
        length_m = dimensions["length"] / 1000.0
        width_m = dimensions["width"] / 1000.0
        thickness_m = dimensions["thickness"] / 1000.0
        volume_m3 = length_m * width_m * thickness_m
        mass_kg = volume_m3 * material["density"]
        raw_material_cost = mass_kg * material["rate_per_kg"]
        return {
            "mass_kg": round(mass_kg, 4),
            "volume_m3": round(volume_m3, 8),
            "raw_material_cost": round(raw_material_cost, 2),
            "raw_material_cost_total": round(raw_material_cost * quantity, 2),
        }
