# Manufacturing Cost Estimation

A deterministic, form-based manufacturing cost estimation system using:

- **Frontend:** Streamlit with a professional manufacturing costing form
- **Backend:** FastAPI with Pydantic validation
- **Cost Engine:** Modular Python calculator for material, process, and overhead costs
- **No LLM/Chatbot:** Pure structured form → JSON → deterministic cost calculation

## Project Structure

```
backend/
├── main.py                      # FastAPI app and CORS middleware
├── models.py                    # Pydantic request/response schemas
├── routes/
│   └── cost_routes.py          # API endpoint routing
├── services/
│   └── cost_service.py         # Business logic layer
└── cost_engine/
    ├── material_cost.py        # Material cost calculations
    ├── process_cost.py         # Process-specific cost logic
    ├── overhead_cost.py        # Overhead and markup calculations
    └── final_cost.py           # Cost aggregation and response building

frontend/
└── app.py                       # Streamlit UI application
```

## Quick Start

### Recommended: run with the included scripts

This project includes helper scripts that create a local virtual environment and run the app from it, so you avoid global `streamlit`/`uvicorn` path issues on any machine.

```bash
./scripts/setup.sh
./scripts/start_backend.sh
./scripts/start_frontend.sh
```

### Alternative manual start

If you want to run without the helper scripts:

```bash
python3 -m pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
streamlit run frontend/app.py
```

The backend will be available at `http://127.0.0.1:8000` and the Streamlit app typically opens at `http://localhost:8501`.

## How It Works

1. **Fill the Form:** Enter part dimensions, material properties, and select manufacturing processes
2. **Submit:** Click "Estimate Cost" to send structured JSON to the backend
3. **Calculate:** FastAPI backend validates and passes data to the cost engine
4. **Receive Results:** Cost breakdown and per-piece estimates are displayed

## API Endpoint

### POST `/estimate-cost`

**Request Body:**

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

**Response:**

```json
{
  "part_name": "Mounting Bracket",
  "quantity": 100,
  "material": {
    "type": "CRCA",
    "density": 7850,
    "rate_per_kg": 65
  },
  "processes": [
    {"name": "laser_cutting", "quantity": 1},
    {"name": "bending", "quantity": 1, "bends": 4}
  ],
  "cost_breakdown": {
    "raw_material_cost": 2041.0,
    "process_cost": 65.0,
    "overhead_cost": 379.08,
    "total_manufacturing_cost": 2485.08,
    "cost_per_piece": 24.85
  },
  "notes": [
    "Calculation uses deterministic rule-based estimates.",
    "Material cost is based on volume and density."
  ]
}
```

## Supported Manufacturing Processes

- **laser_cutting**
- **bending** (specify `bends` count)
- **welding**
- **drilling** (specify `holes` count)
- **machining** (specify `machining_hours`)
- **powder_coating** (specify `coating_thickness_um`)
- **painting** (specify `coating_thickness_um`)
- **assembly**

## Environment Variables

Create a `.env` file (optional):

```
API_BASE_URL=http://127.0.0.1:8000
```

## Notes

- **Deterministic:** All cost calculations are rule-based and reproducible
- **No External APIs:** Runs completely locally, no OpenAI or LLM dependencies
- **Extensible:** Add new processes by extending `process_cost.py`
- **Production-Ready:** Full validation, error handling, and type hints

## License

This project is part of the Manufacturing Cost Estimation suite.
