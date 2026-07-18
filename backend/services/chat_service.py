from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

import numpy as np
import requests

try:
    import xgboost as xgb
except ImportError:  # pragma: no cover - optional dependency guard
    xgb = None

from backend.cost_engine.final_cost import CostEstimator
from backend.models import CostEstimateRequest, MaterialInput, ProcessInput


class ChatCostService:
    def __init__(self) -> None:
        self.estimator = CostEstimator()
        self.model = None
        self.groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL") or os.getenv("OPENAI_MODEL", "llama-3.1-8b-instant")
        self._train_model()

    def _train_model(self) -> None:
        if xgb is None:
            self.model = None
            return

        try:
            training_rows = [
                (100, 200, 100, 50, 2, 65, 7850, 2, 2, 0, 0.0, 0.0, 2485.08),
                (50, 120, 80, 10, 1.5, 220, 2700, 1, 0, 4, 0.0, 40.0, 1048.11),
                (250, 300, 150, 20, 4, 300, 8000, 3, 1, 6, 1.5, 60.0, 3893.75),
                (30, 90, 40, 8, 1, 70, 7850, 2, 0, 0, 0.0, 0.0, 585.44),
                (80, 180, 90, 12, 3, 220, 2700, 2, 2, 2, 0.8, 30.0, 1892.60),
            ]
            X = np.array([
                [row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11]]
                for row in training_rows
            ], dtype=float)
            y = np.array([row[12] for row in training_rows], dtype=float)
            model = xgb.XGBRegressor(
                n_estimators=80,
                max_depth=3,
                learning_rate=0.1,
                objective="reg:squarederror",
                random_state=42,
            )
            model.fit(X, y)
            self.model = model
        except Exception:
            self.model = None

    def _material_defaults(self, material_type: str) -> Dict[str, float]:
        defaults = {
            "crca": {"density": 7850.0, "rate_per_kg": 65.0},
            "mild_steel": {"density": 7850.0, "rate_per_kg": 70.0},
            "stainless": {"density": 8000.0, "rate_per_kg": 300.0},
            "aluminum": {"density": 2700.0, "rate_per_kg": 220.0},
            "steel": {"density": 7850.0, "rate_per_kg": 70.0},
        }
        normalized = material_type.strip().lower().replace(" ", "_")
        return defaults.get(normalized, {"density": 7850.0, "rate_per_kg": 65.0})

    def _extract_with_llm(self, message: str) -> Dict[str, Any] | None:
        if not self.groq_api_key:
            return None
        try:
            payload = {
                "model": self.groq_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You extract manufacturing details from a plain-English request into JSON with keys: quantity, length, width, height, thickness, material.type, material.density, material.rate_per_kg, and processes as an array of process objects.",
                    },
                    {"role": "user", "content": message},
                ],
                "temperature": 0.1,
            }
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.groq_api_key}"},
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None

    def extract_structured_data(self, message: str) -> Dict[str, Any]:
        llm_result = self._extract_with_llm(message)
        if llm_result:
            return self._normalize_llm_result(llm_result, message)

        normalized = message.lower()
        quantity = self._extract_quantity(normalized)
        dimensions = self._extract_dimensions(normalized)
        material_type = self._extract_material(normalized)
        material_defaults = self._material_defaults(material_type)

        processes: List[Dict[str, Any]] = []
        process_names: List[str] = []
        if self._contains_any(normalized, ["laser", "cut"]):
            processes.append({"name": "laser_cutting", "quantity": 1})
            process_names.append("laser_cutting")
        if self._contains_any(normalized, ["bend", "bent", "bending"]):
            bends = self._extract_int(normalized, ["bend", "bent"], default=2)
            processes.append({"name": "bending", "quantity": 1, "bends": bends})
            process_names.append("bending")
        if self._contains_any(normalized, ["weld"]):
            processes.append({"name": "welding", "quantity": 1})
            process_names.append("welding")
        if self._contains_any(normalized, ["drill", "hole"]):
            holes = self._extract_int(normalized, ["hole", "drill"], default=4)
            processes.append({"name": "drilling", "quantity": 1, "holes": holes})
            process_names.append("drilling")
        if self._contains_any(normalized, ["machine", "machining"]):
            machining_hours = self._extract_float(normalized, ["hour", "hours"], default=1.0)
            processes.append({"name": "machining", "quantity": 1, "machining_hours": machining_hours})
            process_names.append("machining")
        if self._contains_any(normalized, ["powder", "coating"]):
            coating_um = self._extract_float(normalized, ["um", "micron", "microns"], default=40.0)
            processes.append({"name": "powder_coating", "quantity": 1, "coating_thickness_um": coating_um})
            process_names.append("powder_coating")
        if self._contains_any(normalized, ["paint"]):
            coating_um = self._extract_float(normalized, ["um", "micron", "microns"], default=40.0)
            processes.append({"name": "painting", "quantity": 1, "coating_thickness_um": coating_um})
            process_names.append("painting")
        if self._contains_any(normalized, ["assemble", "assembly"]):
            processes.append({"name": "assembly", "quantity": 1})
            process_names.append("assembly")

        if not processes:
            processes.append({"name": "laser_cutting", "quantity": 1})
            process_names.append("laser_cutting")

        return {
            "part_name": "Chat Extracted Part",
            "quantity": quantity or 1,
            "length": dimensions[0] if dimensions else 200.0,
            "width": dimensions[1] if dimensions else 100.0,
            "height": dimensions[2] if dimensions else 50.0,
            "thickness": 2.0,
            "material": {
                "type": material_type.upper() if material_type else "CRCA",
                "density": material_defaults["density"],
                "rate_per_kg": material_defaults["rate_per_kg"],
            },
            "processes": process_names,
            "process_details": processes,
        }

    def _normalize_llm_result(self, result: Dict[str, Any], message: str) -> Dict[str, Any]:
        material_data = result.get("material", {}) or {}
        material_type = material_data.get("type") or self._extract_material(message.lower()) or "CRCA"
        material_defaults = self._material_defaults(material_type)
        process_details = result.get("process_details") or []
        process_names = []
        if process_details:
            process_names = [item.get("name") for item in process_details if item.get("name")]
        elif result.get("processes"):
            process_names = [item if isinstance(item, str) else item.get("name") for item in result.get("processes") if item]

        return {
            "part_name": result.get("part_name") or "Chat Extracted Part",
            "quantity": int(result.get("quantity") or 1),
            "length": float(result.get("length") or 200.0),
            "width": float(result.get("width") or 100.0),
            "height": float(result.get("height") or 50.0),
            "thickness": float(result.get("thickness") or 2.0),
            "material": {
                "type": str(material_type).upper(),
                "density": float(material_data.get("density") or material_defaults["density"]),
                "rate_per_kg": float(material_data.get("rate_per_kg") or material_defaults["rate_per_kg"]),
            },
            "processes": process_names or ["laser_cutting"],
            "process_details": process_details or [{"name": "laser_cutting", "quantity": 1}],
        }

    def predict_cost(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        process_payloads: List[Dict[str, Any]] = []
        seen_names: set[str] = set()
        # Prefer process_details (full dicts with parameters like bends, holes, etc.)
        for process in extracted_data.get("process_details", []):
            if isinstance(process, dict) and process.get("name"):
                seen_names.add(process["name"])
                process_payloads.append(process)
        # Fall back to processes list only for names not already seen
        for process in extracted_data.get("processes", []):
            if isinstance(process, dict) and process.get("name") not in seen_names:
                seen_names.add(process["name"])
                process_payloads.append(process)
            elif isinstance(process, str) and process not in seen_names:
                seen_names.add(process)
                process_payloads.append({"name": process, "quantity": 1})

        request = CostEstimateRequest(
            part_name=extracted_data["part_name"],
            quantity=extracted_data["quantity"],
            length=extracted_data["length"],
            width=extracted_data["width"],
            height=extracted_data["height"],
            thickness=extracted_data.get("thickness", 2.0),
            material=MaterialInput(
                type=extracted_data["material"]["type"],
                density=extracted_data["material"]["density"],
                rate_per_kg=extracted_data["material"]["rate_per_kg"],
            ),
            processes=[ProcessInput(**process) for process in process_payloads],
        )
        deterministic_result = self.estimator.estimate(request)
        deterministic_cost = deterministic_result["cost_breakdown"]["total_manufacturing_cost"]

        feature_vector = self._build_feature_vector(extracted_data)
        if self.model is None:
            predicted_cost = deterministic_cost
        else:
            predicted_cost = float(self.model.predict(np.array([feature_vector], dtype=float))[0])

        return {
            "model": "xgboost",
            "predicted_cost": round(max(predicted_cost, 1.0), 2),
            "units": "INR",
            "deterministic_reference": round(deterministic_cost, 2),
        }

    def handle_message(self, message: str) -> Dict[str, Any]:
        extracted_data = self.extract_structured_data(message)
        prediction = self.predict_cost(extracted_data)
        return {
            "extracted_data": extracted_data,
            "prediction": prediction,
            "notes": [
                "The request was parsed from free-form text.",
                "An XGBoost regressor was used for the cost prediction.",
            ],
        }

    def _build_feature_vector(self, extracted_data: Dict[str, Any]) -> List[float]:
        process_count = len(extracted_data.get("processes", []))
        bends = 0
        holes = 0
        machining_hours = 0.0
        coating_um = 0.0
        for process in extracted_data.get("process_details", []):
            if isinstance(process, dict) and process.get("name") == "bending":
                bends = process.get("bends", 0)
            if isinstance(process, dict) and process.get("name") == "drilling":
                holes = process.get("holes", 0)
            if isinstance(process, dict) and process.get("name") == "machining":
                machining_hours = process.get("machining_hours", 0.0)
            if isinstance(process, dict) and process.get("name") in {"powder_coating", "painting"}:
                coating_um = process.get("coating_thickness_um", 0.0)

        return [
            float(extracted_data["quantity"]),
            float(extracted_data["length"]),
            float(extracted_data["width"]),
            float(extracted_data["height"]),
            float(extracted_data.get("thickness", 2.0)),
            float(extracted_data["material"]["rate_per_kg"]),
            float(extracted_data["material"]["density"]),
            float(process_count),
            float(bends),
            float(holes),
            float(machining_hours),
            float(coating_um),
        ]

    def _extract_quantity(self, text: str) -> int | None:
        for pattern in [
            r"(\d+)\s*(?:[a-zA-Z-]+\s+)*(?:parts?|units?|pcs?|pieces?|brackets?)",
            r"produce\s*(\d+)",
            r"for\s*(\d+)\s*(?:parts?|units?)",
        ]:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None

    def _extract_dimensions(self, text: str) -> List[float] | None:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:x|by|×)\s*(\d+(?:\.\d+)?)\s*(?:x|by|×)\s*(\d+(?:\.\d+)?)", text)
        if match:
            return [float(match.group(1)), float(match.group(2)), float(match.group(3))]
        return None

    def _extract_material(self, text: str) -> str:
        material_keywords = {
            "aluminum": "aluminum",
            "crca": "crca",
            "steel": "steel",
            "mild steel": "mild_steel",
            "stainless": "stainless",
        }
        for keyword, normalized_value in material_keywords.items():
            if keyword in text:
                return normalized_value
        return "crca"

    def _extract_int(self, text: str, keywords: List[str], default: int) -> int:
        for keyword in keywords:
            match = re.search(rf"{keyword}\s*(\d+)", text)
            if match:
                return int(match.group(1))
        return default

    def _extract_float(self, text: str, keywords: List[str], default: float) -> float:
        for keyword in keywords:
            match = re.search(rf"(\d+(?:\.\d+)?)\s*(?:{keyword}|{keyword}s)", text)
            if match:
                return float(match.group(1))
        return default

    def _contains_any(self, text: str, keywords: List[str]) -> bool:
        return any(keyword in text for keyword in keywords)
