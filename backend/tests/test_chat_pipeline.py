from backend.services.chat_service import ChatCostService


def test_heuristic_extraction_handles_plain_english_request() -> None:
    service = ChatCostService()
    result = service.extract_structured_data(
        "I need 100 mounting brackets, 200 by 100 by 50 mm, made from CRCA steel, laser cut and bent 3 times."
    )

    assert result["quantity"] == 100
    assert result["length"] == 200.0
    assert result["width"] == 100.0
    assert result["height"] == 50.0
    assert result["material"]["type"] == "CRCA"
    assert "laser_cutting" in result["processes"]
    assert "bending" in result["processes"]


def test_prediction_pipeline_returns_reasonable_cost() -> None:
    service = ChatCostService()
    result = service.handle_message(
        "Produce 50 parts, 120 by 80 by 10 mm, aluminum, drilling 4 holes and painting."
    )

    assert result["extracted_data"]["quantity"] == 50
    assert result["prediction"]["predicted_cost"] > 0
    assert result["prediction"]["model"] == "xgboost"
