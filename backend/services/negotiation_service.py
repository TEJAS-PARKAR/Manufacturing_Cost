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
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        collection_name = os.getenv("MONGODB_COLLECTION", "supplier_sessions")
        self.mongo_collection = MongoConnection.get_collection(collection_name)

    
    def start_session(
        self,
        employee_id: str,
        part_number: str
    ) -> dict[str, Any]:

        key = self._session_key(
            employee_id,
            part_number
        )

        # Check memory first
        session = self.sessions.get(key)

        if session is not None:
            return self._serialize_session(session)

        # Check MongoDB before creating
        if self.mongo_collection is not None:

            doc = self.mongo_collection.find_one(
                {
                    "_id": self._storage_key(
                        employee_id,
                        part_number
                    )
                }
            )

            if doc is not None:
                session = self._hydrate_session(doc)

                self.sessions[key] = session

                print("✅ Existing session loaded from MongoDB")

                return self._serialize_session(session)

        # Create new session only if nothing found
        
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
                "benchmark_reference": self._default_benchmark(
                    employee_id,
                    part_number
                ),
            },
            "negotiation": {
                "supplier_quote": 0,
                "predicted_cost": 0,
                "variance": 0,
                "ai_recommendation": "",
                "counter_offer": 0,
                "status": "pending",
                "rounds": []
            }
        }


        self.sessions[key] = session

        self._persist_session(session)

        print("✅ New session created")
        
        print("PERSISTING SESSION")
        print(session["employee_id"])
        print(session["part_number"])
        print(session["extracted_data"])
        print("HISTORY:", len(session["history"]))

        return self._serialize_session(session)

    
    def get_session_context(
        self,
        employee_id: str,
        part_number: str
    ) -> dict[str, Any]:
        session = self._ensure_session(
            employee_id,
            part_number
        )
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
        
        print("PERSISTING SESSION")
        print(session["employee_id"])
        print(session["part_number"])
        print(session["extracted_data"])
        print("HISTORY:", len(session["history"]))

        return self._serialize_session(session)

    
    def ingest_excel(self, employee_id, part_number, file_bytes, filename):
        session = self._ensure_session(
            employee_id,
            part_number
        )
        raw_table = self._extract_raw_table(file_bytes)
        print("\nRAW TABLE:")
        print(raw_table)
        interpretation = self._interpret_excel_table(
            raw_table
        )
        print("\nINTERPRETATION:")
        print(interpretation)
        session["raw_table"] = raw_table
        session["excel_interpretation"] = interpretation
        session["extracted_data"].update(
            interpretation
        )
        session["missing_fields"] = self._identify_missing_fields(
            session["extracted_data"]
        )
        print("AFTER RECALCULATION:")
        print(session["missing_fields"])
        session["summary"] = self._build_summary(
            session
        )
        session["negotiation"] = (
            self.generate_negotiation_recommendation(
                session["extracted_data"]
            )
        )
        print("\nEXTRACTED DATA AFTER UPDATE:")
        print(session["extracted_data"])
        self._persist_session(session)
        return self._serialize_session(session)

    
    def generate_negotiation_recommendation(
        self,
        extracted_data
    ):

        supplier_quote = float(
            extracted_data.get("total_cost", 0)
        )

        expected_cost = round(
            (
                float(extracted_data.get("raw_material_cost", 0))
                +
                float(extracted_data.get("conversion_cost", 0))
                +
                float(extracted_data.get("coating_cost", 0))
            ),
            2
        )

        variance = 0

        if expected_cost > 0:
            variance = round(
                (
                    (supplier_quote - expected_cost)
                    / expected_cost
                ) * 100,
                2
            )

        if variance <= 5:
            recommendation = "approve"
            counter_offer = supplier_quote

        elif variance <= 15:
            recommendation = "negotiate"
            counter_offer = round(
                expected_cost * 1.03,
                2
            )

        else:
            recommendation = "reject"
            counter_offer = expected_cost

        return {
            "supplier_quote": supplier_quote,
            "predicted_cost": expected_cost,
            "variance": variance,
            "ai_recommendation": recommendation,
            "counter_offer": counter_offer,
            "status": "active",
            "rounds": []
        }

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
        
        print("PERSISTING SESSION")
        print(session["employee_id"])
        print(session["part_number"])
        print(session["extracted_data"])
        print("HISTORY:", len(session["history"]))

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
        
        print("PERSISTING SESSION")
        print(session["employee_id"])
        print(session["part_number"])
        print(session["extracted_data"])
        print("HISTORY:", len(session["history"]))

        return self._serialize_session(session)

    
    def _ensure_session(self, employee_id: str, part_number: str) -> dict[str, Any]:

        key = self._session_key(employee_id, part_number)

        print("=" * 50)
        print("EMPLOYEE:", employee_id)
        print("PART:", part_number)

        storage_key = self._storage_key(
            employee_id,
            part_number
        )

        print("SEARCHING FOR _id:", storage_key)

        session = self.sessions.get(key)

        if session is not None:
            print("FOUND IN MEMORY")
            return session

        if self.mongo_collection is not None:

            print(
                "DOCUMENT COUNT:",
                self.mongo_collection.count_documents({})
            )

            doc = self.mongo_collection.find_one(
                {"_id": storage_key}
            )

            print("DOCUMENT FOUND:", doc is not None)

            if doc:
                print("DOCUMENT ID:", doc.get("_id"))

                session = self._hydrate_session(doc)

                self.sessions[key] = session

                print("LOADED FROM MONGO")

                return session

        print("CREATING NEW SESSION")

        return self.start_session(
            employee_id,
            part_number
        )


    def _serialize_session(self, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "employee_id": session["employee_id"],
            "part_number": session["part_number"],
            "session_key": session["session_key"],
            "status": session["status"],
            "extracted_data": session["extracted_data"],
            "excel_interpretation": session.get("excel_interpretation", {}),
            "history": session["history"],
            "summary": session["summary"],
            "missing_fields": session["missing_fields"],
            "review": session["review"],
            "negotiation": session.get(
                "negotiation",
                {}
            )
        }

    def _storage_key(self, employee_id: str, part_number: str) -> str:
        return f"{employee_id.strip()}::{part_number.strip()}"

    
    def _persist_session(self, session: dict[str, Any]) -> None:

        if self.mongo_collection is None:
            print("NO MONGO COLLECTION")
            return

        doc = self._serialize_session(session)

        doc["_id"] = self._storage_key(
            session["employee_id"],
            session["part_number"]
        )

        print("\n========== WRITING ==========")
        print("ID:", doc["_id"])
        print("EXTRACTED DATA:", doc["extracted_data"])
        print("HISTORY LENGTH:", len(doc["history"]))

        result = self.mongo_collection.replace_one(
            {"_id": doc["_id"]},
            doc,
            upsert=True
        )

        print("MATCHED:", result.matched_count)
        print("MODIFIED:", result.modified_count)
        print("UPSERTED:", result.upserted_id)
        print("========== DONE ==========\n")


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


    def _extract_dimensions_from_raw_table(self, rows):
        for row in rows:
            text = " ".join(
                str(x)
                for x in row
                if x is not None
            ).upper()
            if (
                "TH" in text
                and "WD" in text
                and "LG" in text
            ):
                nums = []
                for item in row:
                    try:
                        nums.append(float(item))
                    except Exception:
                        pass
                if len(nums) >= 3:
                    return {
                        "thickness": nums[0],
                        "width": nums[1],
                        "length": nums[2],
                        "dimensions": nums[:3]
                    }
        return {}


    def _interpret_excel_table(self, raw_table: dict[str, Any]) -> dict[str, Any]:
        llm_result = self._interpret_with_llm(raw_table)
        dimensions = self._extract_dimensions_from_raw_table(
            raw_table.get("rows", [])
        )
        llm_result.update(dimensions)
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
                                    material
                                    material_grade
                                    material_rate
                                    thickness
                                    width
                                    length
                                    IMPORTANT:
                                    Thickness may appear as:
                                    Th
                                    Th.

                                    Width may appear as:
                                    Wd
                                    Wd.

                                    Length may appear as:
                                    Lg
                                    Lg.

                                    Example:

                                    Th. 2
                                    Wd. 95
                                    Lg. 214

                                    Return:

                                    {
                                        "thickness": 2,
                                        "width": 95,
                                        "length": 214
                                    }

                                    Never omit these values if present.

                                    finished_weight
                                    scrap_weight
                                    coating
                                    coating_cost
                                    raw_material_cost
                                    process_information
                                    conversion_cost
                                    total_cost
                                    Extract all manufacturing operations under
                                    "Conversion Cost".
                                    Return them as process_information.
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
                "response_format": {
                    "type": "json_object"
                },

            }
            print("ROWS SENT TO GROQ:", len(raw_table.get("rows", [])))
            print("COLUMNS:", len(raw_table.get("headers", [])))
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )
            if response.status_code != 200:
                print("GROQ ERROR RESPONSE:")
                print(response.text)
            response.raise_for_status()
            print("STATUS CODE:", response.status_code)
            print("RAW RESPONSE:")
            print(response.text[:5000])
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
            print("\nFULL GROQ OUTPUT")
            print(json.dumps(parsed, indent=4))
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
        
        if (
            values.get("thickness") is not None
            and values.get("width") is not None
            and values.get("length") is not None
        ):
            normalized["dimensions"] = [
                float(values["thickness"]),
                float(values["width"]),
                float(values["length"]),
            ]
        material = self._normalize_material(values.get("material"))
        if material:
            normalized["material"] = material
        if values.get("material_rate") is not None:
            try:
                normalized["material_rate"] = float(values["material_rate"])
            except Exception:
                pass
        coating = self._normalize_coating(values.get("coating"))
        if coating:
            normalized["coating"] = coating
        process_information = values.get("process_information")
        if process_information:
            processes = []
            for item in process_information:
                if isinstance(item, dict):
                    processes.append(
                        {
                            "process": item.get("process"),
                            "cost": item.get("cost", 0)
                        }
                    )
                elif isinstance(item, str):
                    processes.append(
                        {
                            "process": self._normalize_process(item),
                            "cost": 0
                        }
                    )
            normalized["process_information"] = processes

        
        # Additional fields extracted by Groq
        for field in [
            "material_grade",
            "thickness",
            "width",
            "length",
            "finished_weight",
            "scrap_weight",
            "coating_cost",
            "raw_material_cost",
            "conversion_cost",
            "total_cost",
        ]:
            if values.get(field) is not None:
                normalized[field] = values[field]

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

        
    def reject_offer(
        self,
        employee_id: str,
        part_number: str,
        reason: str = "Cost exceeds expected benchmark"
    ):
        session = self._ensure_session(
            employee_id,
            part_number
        )
        session["status"] = "rejected"
        session["negotiation"]["status"] = "rejected"
        session["history"].append(
            {
                "role": "tata",
                "message": f"Offer rejected. Reason: {reason}",
                "timestamp": self._now_iso()
            }
        )
        session["negotiation"]["rounds"].append(
            {
                "action": "reject",
                "reason": reason,
                "timestamp": self._now_iso()
            }
        )
        session["summary"] = (
            f"Quotation rejected by Tata Motors. "
            f"Reason: {reason}"
        )
        self._persist_session(session)
        return self._serialize_session(session)


    def negotiate_with_supplier(self, extracted_data, supplier_message, history):
        quote = float(
            extracted_data.get("total_cost", 0)
        )
        expected = (
            float(extracted_data.get("raw_material_cost", 0))
            + float(extracted_data.get("conversion_cost", 0))
            + float(extracted_data.get("coating_cost", 0))
        )
        variance = 0
        if expected > 0:
            variance = round(
                ((quote - expected) / expected) * 100,
                2
            )
        prompt = f"""You are a Tata Motors Procurement Negotiation Expert.

        Part Details:
        {json.dumps(extracted_data, indent=2)}

        Supplier Quote:
        {quote}

        Expected Cost:
        {expected}

        Variance:
        {variance}%

        Negotiation History:
        {json.dumps(history, indent=2)}

        Supplier Message:
        {supplier_message}

        Respond professionally.

        Return JSON only:

        {{
            "reply":"",
            "counter_offer":0,
            "status":"continue"
        }}
        """
        payload = {
        "model": self.groq_model,
        "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Tata Motors procurement "
                        "negotiation specialist."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,
            "response_format": {
                "type": "json_object"
            }
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        content = (
            response.json()
            ["choices"][0]
            ["message"]["content"]
        )
        content = content.strip()
        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()
        return json.loads(content)

    def _negotiate_heuristic(self, extracted_data: dict, supplier_message: str) -> dict:
        """Rule-based fallback negotiation when no LLM key is configured."""
        quote = float(extracted_data.get("total_cost", 0))
        expected = round(
            float(extracted_data.get("raw_material_cost", 0))
            + float(extracted_data.get("conversion_cost", 0))
            + float(extracted_data.get("coating_cost", 0)),
            2,
        )
        variance = 0.0
        if expected > 0:
            variance = round(((quote - expected) / expected) * 100, 2)

        if variance <= 5:
            reply = (
                f"Thank you for your message. Your quoted cost of ₹{quote} is within our "
                f"acceptable range. We are pleased to move forward with these terms."
            )
            counter_offer = quote
            status = "accept"
        elif variance <= 15:
            counter = round(expected * 1.03, 2)
            reply = (
                f"Thank you for your message. Your quoted cost of ₹{quote} is slightly above "
                f"our benchmark. We propose a counter-offer of ₹{counter}. "
                f"Please review and confirm."
            )
            counter_offer = counter
            status = "continue"
        else:
            reply = (
                f"Your quoted cost of ₹{quote} exceeds our benchmark by {variance}%. "
                f"Our expected cost is ₹{expected}. Please revise your costing sheet "
                f"and provide a more competitive offer."
            )
            counter_offer = expected
            status = "continue"

        return {"reply": reply, "counter_offer": counter_offer, "status": status}

    def run_negotiation(self, employee_id, part_number, supplier_message):

        session = self._ensure_session(
            employee_id,
            part_number
        )

        expected_cost = round(
            float(session["extracted_data"].get("raw_material_cost", 0))
            + float(session["extracted_data"].get("conversion_cost", 0))
            + float(session["extracted_data"].get("coating_cost", 0)),
            2
        )

        supplier_offer = self._extract_offer_from_message(
            supplier_message
        )

        print("SUPPLIER MESSAGE:", supplier_message)
        print("SUPPLIER OFFER:", supplier_offer)
        print("EXPECTED COST:", expected_cost)

        if supplier_offer is not None:

            variance = 0

            if expected_cost > 0:
                variance = round(
                    ((supplier_offer - expected_cost) / expected_cost) * 100,
                    2
                )

            print("VARIANCE:", variance)

            if variance <= 5:

                result = {
                    "reply": (
                        f"Thank you. Your revised offer of "
                        f"₹{supplier_offer:.2f} is within our "
                        f"acceptable range. The quotation "
                        f"can now be submitted for approval."
                    ),
                    "counter_offer": supplier_offer,
                    "status": "accepted"
                }

                session["status"] = "submitted_for_review"

            elif variance <= 15:

                counter_offer = round(
                    expected_cost * 1.03,
                    2
                )

                result = {
                    "reply": (
                        f"Thank you for revising the offer to "
                        f"₹{supplier_offer:.2f}. We are close "
                        f"to agreement. Our counter-offer is "
                        f"₹{counter_offer:.2f}."
                    ),
                    "counter_offer": counter_offer,
                    "status": "continue"
                }

            else:

                result = {
                    "reply": (
                        f"Your offer of ₹{supplier_offer:.2f} "
                        f"remains significantly above our "
                        f"expected cost of ₹{expected_cost:.2f}. "
                        f"Please provide a more competitive offer."
                    ),
                    "counter_offer": expected_cost,
                    "status": "continue"
                }

        else:

            if self.groq_api_key:

                result = self.negotiate_with_supplier(
                    session["extracted_data"],
                    supplier_message,
                    session["negotiation"]["rounds"]
                )

            else:

                result = self._negotiate_heuristic(
                    session["extracted_data"],
                    supplier_message
                )

        session["negotiation"]["status"] = result["status"]

        session["negotiation"]["rounds"].append(
            {
                "role": "supplier",
                "message": supplier_message,
                "timestamp": self._now_iso()
            }
        )

        session["negotiation"]["rounds"].append(
            {
                "role": "buyer_ai",
                "message": result["reply"],
                "counter_offer": result["counter_offer"],
                "timestamp": self._now_iso()
            }
        )

        session["history"].append(
            {
                "role": "supplier",
                "message": supplier_message
            }
        )

        session["history"].append(
            {
                "role": "assistant",
                "message": result["reply"]
            }
        )

        session["negotiation"]["counter_offer"] = result["counter_offer"]

        self._persist_session(session)

        return {
            "reply": result["reply"],
            "session": self._serialize_session(session)
        }


    def _extract_offer_from_message(self, message: str):
        message = message.lower()

        patterns = [
            r"(\d+(?:\.\d+)?)\s*rupees",
            r"(\d+(?:\.\d+)?)\s*rs",
            r"(\d+(?:\.\d+)?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass

        return None