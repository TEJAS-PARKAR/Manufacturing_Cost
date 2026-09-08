from io import BytesIO

from openpyxl import Workbook

from backend.models import SupplierSessionResponse
from backend.services.negotiation_service import SupplierNegotiationService


def test_session_memory_resumes_supplier_context_across_sessions() -> None:
    service = SupplierNegotiationService()

    first_session = service.start_session(employee_id="EMP1001", part_number="123456789012")
    assert first_session["session_key"] == ("EMP1001", "123456789012")

    service.record_supplier_message(
        employee_id="EMP1001",
        part_number="123456789012",
        message="My part needs 1200 pieces, material is CRCA and coating is powder coating.",
    )

    resumed = service.get_session_context(employee_id="EMP1001", part_number="123456789012")

    assert resumed["employee_id"] == "EMP1001"
    assert resumed["part_number"] == "123456789012"
    assert len(resumed["history"]) >= 1
    assert resumed["summary"]


def test_quantity_is_optional_in_supplier_negotiation() -> None:
    service = SupplierNegotiationService()

    result = service.record_supplier_message(
        employee_id="EMP1001",
        part_number="123456789012",
        message="Material is CRCA, material rate is 65, powder coating, laser cutting, dimensions are 250 x 200 x 2.",
    )

    assert "quantity" not in result["missing_fields"]
    assert "quantity" not in result["extracted_data"]


def test_excel_upload_extracts_costing_fields_into_session() -> None:
    service = SupplierNegotiationService()

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Costing"
    worksheet.append(["quantity", "material", "material_rate", "coating", "process_information"])
    worksheet.append([1200, "CRCA", 65, "POWDER COATING", "LASER CUTTING"])

    buffer = BytesIO()
    workbook.save(buffer)
    payload = buffer.getvalue()

    result = service.ingest_excel(
        employee_id="EMP1001",
        part_number="123456789012",
        file_bytes=payload,
        filename="costing.xlsx",
    )

    assert result["extracted_data"]["quantity"] == 1200
    assert result["extracted_data"]["material"] == "CRCA"
    assert result["extracted_data"]["material_rate"] == 65.0
    assert result["extracted_data"]["coating"] == "POWDER COATING"


def test_excel_upload_builds_raw_table_and_interpretation_layers() -> None:
    service = SupplierNegotiationService()

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Supplier Quote"
    worksheet.append(["Part Number", "Qty", "Material Grade", "Rate / Kg", "Surface Finish", "Process"])
    worksheet.append(["ABC-001", 1200, "CRCA", 65, "Powder Coating", "Laser Cutting"])

    buffer = BytesIO()
    workbook.save(buffer)
    payload = buffer.getvalue()

    result = service.ingest_excel(
        employee_id="EMP1001",
        part_number="123456789012",
        file_bytes=payload,
        filename="quote.xlsx",
    )

    assert "raw_table" not in result
    assert result["excel_interpretation"]["quantity"] == 1200
    assert result["excel_interpretation"]["material"] == "CRCA"
    assert result["excel_interpretation"]["material_rate"] == 65.0
    assert result["excel_interpretation"]["coating"] == "POWDER COATING"

    internal_session = service._ensure_session(
        employee_id="EMP1001",
        part_number="123456789012",
    )
    assert internal_session["raw_table"]["sheet_name"] == "Supplier Quote"
    assert internal_session["raw_table"]["headers"] == ["Part Number", "Qty", "Material Grade", "Rate / Kg", "Surface Finish", "Process"]


def test_wrapped_llm_extracted_data_is_preserved_in_response() -> None:
    service = SupplierNegotiationService()
    service._interpret_with_llm = lambda raw_table, already_extracted=None: {
        "extracted_data": {
            "quantity": 1200,
            "material": "CRCA",
            "material_rate": 65,
            "coating": "POWDER COATING",
        }
    }

    result = service._interpret_excel_table({"headers": [], "rows": []})

    assert result["quantity"] == 1200
    assert result["material"] == "CRCA"
    assert result["material_rate"] == 65.0
    assert result["coating"] == "POWDER COATING"


def test_empty_llm_interpretation_falls_back_to_headers() -> None:
    service = SupplierNegotiationService()
    service._interpret_with_llm = lambda raw_table, already_extracted=None: {
        "quantity": None,
        "material": None,
        "material_rate": None,
        "coating": None,
        "process_information": None,
    }

    result = service._interpret_excel_table({
        "headers": ["quantity", "material", "material_rate", "coating", "process_information"],
        "rows": [[1200, "CRCA", 65, "POWDER COATING", "LASER CUTTING"]],
    })

    assert result["quantity"] == 1200
    assert result["material"] == "CRCA"
    assert result["material_rate"] == 65.0
    assert result["coating"] == "POWDER COATING"


def test_session_response_preserves_allowance_gate_state() -> None:
    service = SupplierNegotiationService()

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Costing"
    worksheet.append([
        "quantity",
        "material",
        "material_rate",
        "coating",
        "process_information",
        "part_length",
        "part_width",
        "part_thickness",
        "sheet_length",
        "sheet_width",
    ])
    worksheet.append([1200, "CRCA", 65, "POWDER COATING", "LASER CUTTING", 250, 200, 2, 1250, 2500])

    buffer = BytesIO()
    workbook.save(buffer)
    payload = buffer.getvalue()

    result = service.ingest_excel(
        employee_id="EMP1001",
        part_number="123456789012",
        file_bytes=payload,
        filename="costing.xlsx",
    )

    response = SupplierSessionResponse(**result)
    assert response.awaiting_allowance_response is True


def test_session_response_excludes_raw_excel_rows() -> None:
    service = SupplierNegotiationService()

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Supplier Quote"
    worksheet.append(["Part Number", "Qty", "Material Grade", "Rate / Kg", "Surface Finish", "Process"])
    worksheet.append(["ABC-001", 1200, "CRCA", 65, "Powder Coating", "Laser Cutting"])

    buffer = BytesIO()
    workbook.save(buffer)
    payload = buffer.getvalue()

    result = service.ingest_excel(
        employee_id="EMP1001",
        part_number="123456789012",
        file_bytes=payload,
        filename="quote.xlsx",
    )

    public_response = SupplierSessionResponse(**result)
    public_payload = public_response.model_dump(exclude_none=True)

    assert "raw_table" not in public_payload
    assert public_payload["extracted_data"]["material"] == "CRCA"


def test_dataset_1_excel_extraction() -> None:
    import os
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "dataset-1.xlsx")
    if not os.path.exists(file_path):
        return

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    service = SupplierNegotiationService()
    result = service.ingest_excel(
        employee_id="EMP_TEST",
        part_number="123456789012",
        file_bytes=file_bytes,
        filename="dataset-1.xlsx",
    )

    extracted = result["extracted_data"]
    # Verify dimensions are accurate (not corrupted by Blanking press operation)
    assert extracted["part_thickness"] == 2.0
    assert extracted["part_width"] == 95.0
    assert extracted["part_length"] == 214.0
    assert extracted["dimensions"] == [2.0, 95.0, 214.0]

    # Verify material, grade, and rate
    assert "DD 1079" in extracted["material"]
    assert extracted["material_rate"] == 58.76

    # Verify key cost breakdown fields
    assert extracted["raw_material_cost"] == 16.7
    assert extracted["conversion_cost"] == 3.29
    assert extracted["coating_cost"] == 4.2
    assert extracted["coating"] == "PLATING"
    assert extracted["overhead_cost"] == 0.33
    assert extracted["icc_cost"] == 0.33
    assert extracted["rejection_cost"] == 0.4
    assert extracted["profit"] == 2.0
    assert extracted["total_cost"] == 35.1

    # Verify no mandatory fields are missing
    assert result["missing_fields"] == []

