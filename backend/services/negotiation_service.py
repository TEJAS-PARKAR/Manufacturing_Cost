from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import json
import os
import re
from typing import Any

import pandas as pd
import requests
from openpyxl import load_workbook

from backend.services.mongo_service import MongoConnection


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
        self.groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL") or os.getenv("OPENAI_MODEL", "llama-3.1-8b-instant")
        collection_name = os.getenv("MONGODB_COLLECTION", "supplier_sessions")
        self.mongo_collection = MongoConnection.get_collection(collection_name)

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
                "raw_table": {},
                "excel_interpretation": {},
                "history": [],
                "summary": "New negotiation session started.",
                "missing_fields": self.REQUIRED_FIELDS,
                "review": {
                    "recommendation": "review",
                    "benchmark_reference": self._default_benchmark(employee_id, part_number),
                },
            }
            self.sessions[key] = session
            self._persist_session(session)
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
        self._persist_session(session)
        return self._serialize_session(session)

    def ingest_excel(self, employee_id: str, part_number: str, file_bytes: bytes, filename: str) -> dict[str, Any]:
        session = self._ensure_session(employee_id, part_number)
        raw_table = self._extract_raw_table(file_bytes)
        interpretation = self._interpret_excel_table(raw_table)

        session["raw_table"] = raw_table
        session["excel_interpretation"] = interpretation
        session["extracted_data"].update(interpretation)
        session["history"].append(
            {
                "role": "system",
                "message": f"Excel sheet '{filename}' processed through raw-table extraction and interpretation.",
                "timestamp": self._now_iso(),
            }
        )
        session["missing_fields"] = self._identify_missing_fields(session["extracted_data"])
        session["summary"] = self._build_summary(session)
        session["review"]["recommendation"] = self._recommendation(session["extracted_data"])
        self._persist_session(session)
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
        self._persist_session(session)
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
        self._persist_session(session)
        return self._serialize_session(session)

    def _ensure_session(self, employee_id: str, part_number: str) -> dict[str, Any]:
        key = self._session_key(employee_id, part_number)
        session = self.sessions.get(key)
        if session is not None:
            return session
        if self.mongo_collection is not None:
            doc = self.mongo_collection.find_one({"_id": self._storage_key(employee_id, part_number)})
            if doc is not None:
                session = self._hydrate_session(doc)
                self.sessions[key] = session
                return session
        return self.start_session(employee_id, part_number)

    def _serialize_session(self, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "employee_id": session["employee_id"],
            "part_number": session["part_number"],
            "session_key": session["session_key"],
            "status": session["status"],
            "extracted_data": session["extracted_data"],
            "raw_table": session.get("raw_table", {}),
            "excel_interpretation": session.get("excel_interpretation", {}),
            "history": session["history"],
            "summary": session["summary"],
            "missing_fields": session["missing_fields"],
            "review": session["review"],
        }

    def _storage_key(self, employee_id: str, part_number: str) -> str:
        return f"{employee_id.strip()}::{part_number.strip()}"

    def _persist_session(self, session: dict[str, Any]) -> None:
        if self.mongo_collection is None:
            return
        doc = self._serialize_session(session)
        doc["_id"] = self._storage_key(session["employee_id"], session["part_number"])
        self.mongo_collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    def _hydrate_session(self, document: dict[str, Any]) -> dict[str, Any]:
        session = dict(document)
        session.pop("_id", None)
        session_key = session.get("session_key")
        if isinstance(session_key, list):
            session["session_key"] = tuple(session_key)
        return session

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

    def _extract_raw_table(self, file_bytes: bytes) -> dict[str, Any]:
        buffer = BytesIO(file_bytes)
        workbook = load_workbook(buffer, data_only=True)
        worksheet = workbook.active
        rows = [list(row) for row in worksheet.iter_rows(values_only=True)]
        headers = [self._clean_cell(value) for value in rows[0]] if rows else []
        data_rows = []
        for row in rows[1:]:
            data_rows.append([self._clean_cell(value) for value in row])

        dataframe = pd.DataFrame(data_rows, columns=headers) if headers else pd.DataFrame(data_rows)
        return {
            "sheet_name": worksheet.title,
            "headers": headers,
            "rows": data_rows,
            "row_count": len(data_rows),
            "column_count": len(headers),
            "dataframe_preview": dataframe.to_dict(orient="records"),
        }

    def _interpret_excel_table(self, raw_table: dict[str, Any]) -> dict[str, Any]:
        llm_result = self._interpret_with_llm(raw_table)
        if llm_result:
            return self._normalize_interpreted_values(llm_result)

        headers = [self._normalize_header(header) for header in raw_table.get("headers", [])]
        rows = raw_table.get("rows", [])
        if not headers or not rows:
            return {}

        first_row = rows[0]
        lookup: dict[str, Any] = {}
        for index, header in enumerate(headers):
            lookup[self._normalize_header_key(header)] = first_row[index] if index < len(first_row) else None

        interpreted: dict[str, Any] = {}
        quantity = self._extract_quantity_from_lookup(lookup)
        if quantity is not None:
            interpreted["quantity"] = quantity

        dimensions = self._extract_dimensions_from_lookup(lookup)
        if dimensions:
            interpreted["dimensions"] = dimensions

        material = self._extract_material_from_lookup(lookup)
        if material:
            interpreted["material"] = material

        material_rate = self._extract_numeric_from_lookup(lookup, ["material_rate", "rate_per_kg", "rate", "rate_kg"])
        if material_rate is not None:
            interpreted["material_rate"] = material_rate

        coating = self._extract_coating_from_lookup(lookup)
        if coating:
            interpreted["coating"] = coating

        process_information = self._extract_process_information_from_lookup(lookup)
        if process_information:
            interpreted["process_information"] = process_information

        return interpreted

    def _interpret_with_llm(self, raw_table: dict[str, Any]) -> dict[str, Any]:
        if not self.groq_api_key:
            return {}
        try:
            payload = {
                "model": self.groq_model,
                "messages": [
                    
                                {
                                    "role": "system",
                                    "content": """
                                    You are an expert in Tata Motors supplier costing sheets.

                                    Analyze the entire costing sheet.

                                    Extract:

                                    quantity
                                    dimensions
                                    material
                                    material_grade
                                    material_rate
                                    thickness
                                    width
                                    length
                                    finished_weight
                                    scrap_weight
                                    coating
                                    coating_cost
                                    raw_material_cost
                                    process_information
                                    conversion_cost
                                    total_cost

                                    Return ONLY valid JSON.
                                    Use null where unavailable.
                                    """
                                },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "sheet_name": raw_table.get("sheet_name"),
                                "headers": raw_table.get("headers"),
                                "rows": raw_table.get("rows", []),
                            },
                            ensure_ascii=False,
                        ),
                    },
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
            
            content = response.json()["choices"][0]["message"]["content"]
            
            print("========== GROQ RESPONSE ==========")
            print(content)
            print("===================================")

            content = content.strip()

            if content.startswith("```"):
                content = re.sub(r"^```json", "", content)
                content = content.replace("```", "")
                content = content.strip()

            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except Exception as e:
            print("========== GROQ ERROR ==========")
            print(str(e))
            return {}
        return {}

    def _normalize_interpreted_values(self, values: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        if values.get("quantity") is not None:
            normalized["quantity"] = int(float(values["quantity"]))
        if values.get("dimensions"):
            if isinstance(values["dimensions"], list):
                normalized["dimensions"] = [float(item) for item in values["dimensions"]]
        material = self._normalize_material(values.get("material"))
        if material:
            normalized["material"] = material
        if values.get("material_rate") is not None:
            normalized["material_rate"] = float(values["material_rate"])
        coating = self._normalize_coating(values.get("coating"))
        if coating:
            normalized["coating"] = coating
        process_information = values.get("process_information")
        if process_information:
            if isinstance(process_information, str):
                normalized["process_information"] = [self._normalize_process(process_information)]
            elif isinstance(process_information, list):
                normalized["process_information"] = [self._normalize_process(item) for item in process_information if self._normalize_process(item)]
        return normalized

    def _normalize_header(self, header: Any) -> str:
        return str(header).strip() if header is not None else ""

    def _normalize_header_key(self, header: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "_", header.strip().lower())
        return normalized.strip("_")

    def _clean_cell(self, value: Any) -> Any:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return value

    def _extract_quantity_from_lookup(self, lookup: dict[str, Any]) -> int | None:
        for key in ["quantity", "qty", "qty_pcs", "pieces", "piece_count"]:
            value = lookup.get(key)
            if value is not None and str(value).strip() != "":
                try:
                    return int(float(str(value)))
                except ValueError:
                    pass
        for value in lookup.values():
            if isinstance(value, (int, float)):
                return int(float(value))
        return None

    def _extract_dimensions_from_lookup(self, lookup: dict[str, Any]) -> list[float] | None:
        dimension_values = []
        for key in ["length", "width", "height", "thickness"]:
            value = lookup.get(key)
            if value is not None and str(value).strip() != "":
                try:
                    dimension_values.append(float(value))
                except (TypeError, ValueError):
                    continue
        if dimension_values:
            return dimension_values[:3]
        return None

    def _extract_numeric_from_lookup(self, lookup: dict[str, Any], keys: list[str]) -> float | None:
        for key in keys:
            value = lookup.get(key)
            if value is not None and str(value).strip() != "":
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return None

    def _extract_material_from_lookup(self, lookup: dict[str, Any]) -> str | None:
        for key in ["material", "material_grade", "material_type"]:
            value = lookup.get(key)
            if value is not None and str(value).strip() != "":
                return self._normalize_material(value)
        return None

    def _extract_coating_from_lookup(self, lookup: dict[str, Any]) -> str | None:
        for key in ["coating", "surface_coating", "surface_finish", "finish"]:
            value = lookup.get(key)
            if value is not None and str(value).strip() != "":
                return self._normalize_coating(value)
        return None

    def _extract_process_information_from_lookup(self, lookup: dict[str, Any]) -> list[str] | None:
        for key in ["process_information", "process", "processes"]:
            value = lookup.get(key)
            if value is not None and str(value).strip() != "":
                if isinstance(value, list):
                    normalized = [self._normalize_process(item) for item in value if self._normalize_process(item)]
                    if normalized:
                        return normalized
                normalized = self._normalize_process(value)
                if normalized:
                    return [normalized]
        return None

    def _normalize_material(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().upper()
        mapping = {
            "CRCA": "CRCA",
            "MILD STEEL": "MILD STEEL",
            "MILDSTEEL": "MILD STEEL",
            "STAINLESS": "STAINLESS",
            "ALUMINUM": "ALUMINUM",
        }
        if normalized in mapping:
            return mapping[normalized]
        if "CRCA" in normalized:
            return "CRCA"
        if "MILD STEEL" in normalized or "MILDSTEEL" in normalized:
            return "MILD STEEL"
        if "STAINLESS" in normalized:
            return "STAINLESS"
        if "ALUMINUM" in normalized:
            return "ALUMINUM"
        return normalized or None

    def _normalize_coating(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().upper()
        mapping = {
            "POWDER COATING": "POWDER COATING",
            "POWDER": "POWDER COATING",
            "PAINTING": "PAINTING",
            "ZINC": "ZINC COATING",
            "ZINC COATING": "ZINC COATING",
            "CHROME": "CHROME COATING",
            "CHROME COATING": "CHROME COATING",
        }
        if normalized in mapping:
            return mapping[normalized]
        if "POWDER" in normalized:
            return "POWDER COATING"
        if "PAINT" in normalized:
            return "PAINTING"
        if "ZINC" in normalized:
            return "ZINC COATING"
        if "CHROME" in normalized:
            return "CHROME COATING"
        return normalized or None

    def _normalize_process(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().upper()
        if not normalized:
            return None
        replacements = {
            "LASER CUT": "LASER CUTTING",
            "LASER CUTTING": "LASER CUTTING",
            "CUTTING": "LASER CUTTING",
            "BEND": "BENDING",
            "BENDING": "BENDING",
            "WELD": "WELDING",
            "WELDING": "WELDING",
            "DRILL": "DRILLING",
            "DRILLING": "DRILLING",
            "HOLE": "DRILLING",
        }
        for source, target in replacements.items():
            if source in normalized:
                return target
        return normalized

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
