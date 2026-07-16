# Manufacturing Cost Copilot

A chatbot-style manufacturing cost estimation system that accepts free-form text, extracts manufacturing details, and predicts cost using a lightweight XGBoost-based workflow.

- **Frontend:** Streamlit chat interface
- **Backend:** FastAPI with Pydantic validation
- **Extraction Layer:** Heuristic parser with optional OpenAI-style LLM integration
- **Prediction Layer:** Deterministic cost engine plus XGBoost-based estimation

## Project Structure

```
backend/
├── main.py                      # FastAPI app and CORS middleware
├── models.py                    # Pydantic request/response schemas
├── routes/
│   └── cost_routes.py          # API endpoints for structured and chat requests
├── services/
│   ├── cost_service.py         # Business logic for deterministic costing
│   └── chat_service.py         # Free-text extraction and prediction workflow
└── cost_engine/
    ├── material_cost.py        # Material cost calculations
    ├── process_cost.py         # Process-specific cost logic
    ├── overhead_cost.py        # Overhead and markup calculations
    └── final_cost.py           # Cost aggregation and response building

frontend/
└── app.py                       # Streamlit chat-based UI
```

## Quick Start

### Recommended: run with the included scripts

These scripts create a local environment and launch both services:

```bash
./scripts/setup.sh
./scripts/start_backend.sh
./scripts/start_frontend.sh
```

### Alternative manual start

If you prefer to run things manually:

```bash
python3 -m pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
streamlit run frontend/app.py
```

The backend will be available at http://127.0.0.1:8000 and the Streamlit app will open at http://localhost:8501.

## How It Works

1. **Enter a Prompt:** Type a natural-language request such as “I need 100 mounting brackets, 200 by 100 by 50 mm, made from CRCA steel, laser cut and bent 3 times.”
2. **Extract Details:** The backend parses the request for quantity, dimensions, material, and manufacturing processes.
3. **Predict Cost:** The system combines the deterministic cost engine with an XGBoost-based regression model for a cost estimate.
4. **View Results:** The Streamlit UI shows the extracted details and the predicted cost.

## API Endpoints

### POST /estimate-cost

Use this for structured JSON requests.

**Example request:**

```json
{
  "part_name": "Mounting Bracket",
  "quantity": 100,
  "length": 200,
  "width": 100,
  "height": 50,
  "thickness": 2,
  "material": {
    "type": "CRCA",
    "density": 7850,
    "rate_per_kg": 65
  },
  "processes": [
    {"name": "laser_cutting"},
    {"name": "bending", "bends": 4}
  ]
}
```

### POST /chat-cost

Use this for free-form chat-style prompts.

**Example request:**

```json
{
  "message": "Produce 50 parts, 120 by 80 by 10 mm, aluminum, drilling 4 holes and painting."
}
```

**Example response:**

```json
{
  "extracted_data": {
    "quantity": 50,
    "length": 120,
    "width": 80,
    "height": 10,
    "material": {
      "type": "ALUMINUM",
      "density": 2700,
      "rate_per_kg": 220
    },
    "processes": ["drilling", "painting"]
  },
  "prediction": {
    "model": "xgboost",
    "predicted_cost": 1234.56,
    "units": "INR",
    "deterministic_reference": 1200.0
  },
  "notes": [
    "The request was parsed from free-form text.",
    "An XGBoost regressor was used for the cost prediction."
  ]
}
```

## Supported Manufacturing Processes

- laser_cutting
- bending
- welding
- drilling
- machining
- powder_coating
- painting
- assembly

## Environment Variables

Create a .env file (optional) to override the frontend API endpoint:

```bash
API_BASE_URL=http://127.0.0.1:8000
```

If you want to use an OpenAI-compatible LLM for stronger extraction, set:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

## Notes

- The app now works as a chatbot-style cost estimator.
- Extraction is heuristic by default and can be improved with an LLM provider.
- The deterministic cost engine remains available for structured requests.
- The project is verified to run with the current test suite.

## License

This project is part of the Manufacturing Cost Estimation suite.
