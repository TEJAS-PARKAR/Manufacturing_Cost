from __future__ import annotations


class OverheadCostCalculator:
    def calculate(self, process_cost: float, material_cost: float) -> float:
        overhead_rate = 0.18
        return round((process_cost + material_cost) * overhead_rate, 2)
