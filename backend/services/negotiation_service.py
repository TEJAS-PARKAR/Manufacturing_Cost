from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from io import BytesIO
import re
from typing import Any

import pandas as pd


class SupplierNegotiationService:
    REQUIRED_FIELDS = [
        "quantity",
        "dimensions",
        "material",
        "material_rate",
        "coating",
        "process_information",
    ]

    INTERNAL_BENCHMARKS = {
        "CRCA": {"material_rate": 65.0, "process_cost": 120.0, "overhead": 55.0},
        "ALUMINUM": {"material_rate": 220.0, "process_cost": 190.0, "overhead": 80.0},
        "STAINLESS": {"material_rate": 300.0, "process_cost": 250.0, "overhead": 100.0},
    }

    def __init__(self) -> None:
        self.sessions: dict[tuple[str, str], dict[str, Any]] = {}

    def start_session(self, employee_id: str, part_number: str) -> dict[str, Any]:
        key = self._session_key(employee_id, part_number)
        session = self.sessions.get(key)
        if session is None:
            session = {
                "employee_id": employee_id,
                "part_number": part_number,
                "session_key": key,
                "status": "active",
                "extracted_data": {},
                "history": [],
                "summary": "New negotiation session started.",
                "missing_fields": self.REQUIRED_FIELDS,
                "review": {
                    "recommendation": "review",
                    "benchmark_reference": self._default_benchmark(employee_id, part_number),
                },
            }
            self.sessions[key] = session
        return self._serialize_session(session)

    def get_session_context(self, employee_id: str, part_number: str) -> dict[str, Any]:
        key = self._session_key(employee_id, part_number)
        session = self.sessions.get(key)
        if session is None:
            return self.start_session(employee_id, part_number)
        return self._serialize_session(session)

    def record_supplier_message(self, employee_id: str, part_number: str, message: str) -> dict[str, Any]:
        session = self._ensure_session(employee_id, part_number)
        parsed = self._extract_from_message(message)
        session["extracted_data"].update(parsed)
        session["history"].append(
            {
                "role": "supplier",
                "message": message,
                "timestamp": self._now_iso(),
            }
        )
        session["missing_fields"] = self._identify_missing_fields(session["extracted_data"])
        session["summary"] = self._build_summary(session)
        session["review"]["recommendation"] = self._recommendation(session["extracted_data"])
        return self._serialize_session(session)

    def ingest_excel(self, employee_id: str, part_number: str, file_bytes: bytes, filename: str) -> dict[str, Any]:
        session = self._ensure_session(employee_id, part_number)
        buffer = BytesIO(file_bytes)
        dataframe = pd.read_excel(buffer)
        parsed = self._extract_from_dataframe(dataframe)
        session["extracted_data"].update(parsed)
        session["history"].append(
            {
                "role": "system",
                "message": f"Excel sheet '{filename}' processed for cost extraction.",
                "timestamp": self._now_iso(),
            }
        )
        session["missing_fields"] = self._identify_missing_fields(session["extracted_data"])
        session["summary"] = self._build_summary(session)
        session["review"]["recommendation"] = self._recommendation(session["extracted_data"])
        return self._serialize_session(session)

    def submit_for_review(self, employee_id: str, part_number: str) -> dict[str, Any]:
        session = self._ensure_session(employee_id, part_number)
        session["status"] = "submitted_for_review"
        session["history"].append(
            {
                "role": "system",
                "message": "Supplier session submitted to Tata Motors review dashboard.",
                "timestamp": self._now_iso(),
            }
        )
        session["summary"] = self._build_summary(session)
        return self._serialize_session(session)

    def get_review_dashboard(self, employee_id: str, part_number: str) -> dict[str, Any]:
        session = self._ensure_session(employee_id, part_number)
        return {
            "session": self._serialize_session(session),
            "recommendation": self._recommendation(session["extracted_data"]),
            "benchmark_comparison": self._benchmark_comparison(session["extracted_data"]),
        }

    def approve_cost_inputs(self, employee_id: str, part_number: str, approval_payload: dict[str, Any]) -> dict[str, Any]:
        session = self._ensure_session(employee_id, part_number)
        approved = approval_payload.get("approved_values", {})
        session["extracted_data"].update(approved)
        session["status"] = "approved"
        session["history"].append(
            {
                "role": "tata",
                "message": "Approved cost inputs updated into final validated estimate.",
                "timestamp": self._now_iso(),
            }
        )
        session["summary"] = self._build_summary(session)
        return self._serialize_session(session)

    def _ensure_session(self, employee_id: str, part_number: str) -> dict[str, Any]:
        key = self._session_key(employee_id, part_number)
        session = self.sessions.get(key)
        if session is None:
            return self.start_session(employee_id, part_number)
        return session

    def _serialize_session(self, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "employee_id": session["employee_id"],
            "part_number": session["part_number"],
            "session_key": session["session_key"],
            "status": session["status"],
            "extracted_data": session["extracted_data"],
            "history": session["history"],
            "summary": session["summary"],
            "missing_fields": session["missing_fields"],
            "review": session["review"],
        }

    def _session_key(self, employee_id: str, part_number: str) -> tuple[str, str]:
        return (employee_id.strip(), part_number.strip())

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _build_summary(self, session: dict[str, Any]) -> str:
        data = session["extracted_data"]
        material = data.get("material") or "pending"
        quantity = data.get("quantity") or "pending"
        dimensions = data.get("dimensions") or "pending"
        coating = data.get("coating") or "pending"
        return (
            f"Supplier {session['employee_id']} is discussing part {session['part_number']}. "
            f"Current extracted context: quantity={quantity}, material={material}, dimensions={dimensions}, coating={coating}."
        )

    def _identify_missing_fields(self, extracted_data: dict[str, Any]) -> list[str]:
        missing = []
        if not extracted_data.get("quantity"):
            missing.append("quantity")
        if not extracted_data.get("dimensions"):
            missing.append("dimensions")
        if not extracted_data.get("material"):
            missing.append("material")
        if not extracted_data.get("material_rate"):
            missing.append("material_rate")
        if not extracted_data.get("coating"):
            missing.append("coating")
        if not extracted_data.get("process_information"):
            missing.append("process_information")
        return missing

    def _recommendation(self, extracted_data: dict[str, Any]) -> str:
        material_rate = float(extracted_data.get("material_rate") or 0)
        benchmark = self.INTERNAL_BENCHMARKS.get((extracted_data.get("material") or "").upper(), {}).get("material_rate", 0.0)
        if benchmark and material_rate > 0:
            if material_rate <= benchmark * 1.05:
                return "accept"
            if material_rate <= benchmark * 1.15:
                return "review"
            return "negotiate_further"
        return "review"

    def _default_benchmark(self, employee_id: str, part_number: str) -> dict[str, Any]:
        return {
            "employee_id": employee_id,
            "part_number": part_number,
            "raw_material_rate": 65.0,
            "process_cost": 120.0,
            "coating_cost": 40.0,
            "benchmark_note": "Internal Tata Motors benchmark reference loaded for review.",
        }

    def _extract_from_message(self, message: str) -> dict[str, Any]:
        normalized = message.lower()
        extracted: dict[str, Any] = {}
        quantity_match = re.search(r"(\d+(?:,\d+)*)\s*(pieces?|pcs?|units?|qty)", normalized)
        if quantity_match:
            extracted["quantity"] = int(quantity_match.group(1).replace(",", ""))

        dimension_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:x|by|×)\s*(\d+(?:\.\d+)?)\s*(?:x|by|×)\s*(\d+(?:\.\d+)?)", normalized)
        if dimension_match:
            extracted["dimensions"] = [
                float(dimension_match.group(1)),
                float(dimension_match.group(2)),
                float(dimension_match.group(3)),
            ]

        material_map = {
            "crca": "CRCA",
            "mild steel": "MILD STEEL",
            "stainless": "STAINLESS",
            "aluminum": "ALUMINUM",
        }
        for keyword, value in material_map.items():
            if keyword in normalized:
                extracted["material"] = value
                break

        coating_keywords = {
            "powder coating": "POWDER COATING",
            "painting": "PAINTING",
            "zinc": "ZINC COATING",
            "chrome": "CHROME COATING",
        }
        for keyword, value in coating_keywords.items():
            if keyword in normalized:
                extracted["coating"] = value
                break

        process_keywords = []
        if "laser" in normalized or "cut" in normalized:
            process_keywords.append("LASER CUTTING")
        if "bend" in normalized:
            process_keywords.append("BENDING")
        if "weld" in normalized:
            process_keywords.append("WELDING")
        if "drill" in normalized or "hole" in normalized:
            process_keywords.append("DRILLING")
        if process_keywords:
            extracted["process_information"] = process_keywords

        rate_match = re.search(r"material rate\s*(?:is|=|:)?\s*(\d+(?:\.\d+)?)", normalized)
        if rate_match:
            extracted["material_rate"] = float(rate_match.group(1))

        return extracted

    def _extract_from_dataframe(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        normalized_columns = {str(column).strip().lower().replace(" ", "_").replace("-", "_"): column for column in dataframe.columns}

        parsed: dict[str, Any] = {}
        quantity_candidates = [
            normalized_columns.get("quantity"),
            normalized_columns.get("qty"),
            normalized_columns.get("qty_pcs"),
            normalized_columns.get("pieces"),
        ]
        for candidate in quantity_candidates:
            if candidate and not dataframe[candidate].isna().all():
                parsed["quantity"] = int(float(dataframe[candidate].dropna().iloc[0]))
                break

        dimension_columns = [
            normalized_columns.get("length"),
            normalized_columns.get("width"),
            normalized_columns.get("height"),
            normalized_columns.get("thickness"),
        ]
        values = []
        for column in dimension_columns:
            if column and not dataframe[column].isna().all():
                values.append(float(dataframe[column].dropna().iloc[0]))
        if values:
            parsed["dimensions"] = values[:3]

        material_column = normalized_columns.get("material") or normalized_columns.get("material_grade")
        if material_column and not dataframe[material_column].isna().all():
            parsed["material"] = str(dataframe[material_column].dropna().iloc[0]).upper()

        material_rate_column = normalized_columns.get("material_rate") or normalized_columns.get("rate_per_kg")
        if material_rate_column and not dataframe[material_rate_column].isna().all():
            parsed["material_rate"] = float(dataframe[material_rate_column].dropna().iloc[0])

        coating_column = normalized_columns.get("coating") or normalized_columns.get("surface_coating")
        if coating_column and not dataframe[coating_column].isna().all():
            parsed["coating"] = str(dataframe[coating_column].dropna().iloc[0]).upper()

        process_column = normalized_columns.get("process_information") or normalized_columns.get("process")
        if process_column and not dataframe[process_column].isna().all():
            parsed["process_information"] = [str(value).upper() for value in dataframe[process_column].dropna().astype(str).tolist()]

        weight_column = normalized_columns.get("weight") or normalized_columns.get("part_weight")
        if weight_column and not dataframe[weight_column].isna().all():
            parsed["weight"] = float(dataframe[weight_column].dropna().iloc[0])

        return parsed

    def _benchmark_comparison(self, extracted_data: dict[str, Any]) -> dict[str, Any]:
        material = (extracted_data.get("material") or "CRCA").upper()
        rate = float(extracted_data.get("material_rate") or 0)
        benchmark = self.INTERNAL_BENCHMARKS.get(material, {"material_rate": 65.0, "process_cost": 120.0})
        benchmark_rate = float(benchmark.get("material_rate", 0.0))
        variance = round(rate - benchmark_rate, 2) if benchmark_rate else 0.0
        return {
            "supplier_material_rate": rate,
            "internal_benchmark_rate": benchmark_rate,
            "variance": variance,
            "recommendation": self._recommendation(extracted_data),
        }
