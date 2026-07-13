from __future__ import annotations


class ProcessCostCalculator:
    def calculate(self, processes: list[dict]) -> float:
        rates = {
            "laser_cutting": 25.0,
            "bending": 20.0,
            "welding": 60.0,
            "drilling": 10.0,
            "machining": 80.0,
            "powder_coating": 15.0,
            "painting": 12.0,
            "assembly": 30.0,
        }
        total = 0.0
        for process in processes:
            name = process["name"]
            quantity = process.get("quantity", 1)
            rate = rates.get(name, 18.0)
            if name == "bending":
                bends = process.get("bends") or 0
                total += rate * quantity + bends * 5.0
            elif name == "drilling":
                holes = process.get("holes") or 0
                total += rate * quantity + holes * 2.0
            elif name == "machining":
                hours = process.get("machining_hours") or 0.0
                total += rate * quantity * max(hours, 1.0)
            elif name in {"powder_coating", "painting"}:
                thickness = process.get("coating_thickness_um") or 0.0
                total += rate * quantity + thickness * 0.01
            else:
                total += rate * quantity
        return round(total, 2)
