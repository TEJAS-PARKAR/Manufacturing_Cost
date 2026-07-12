# Manufacturing Cost Engine

A high-performance, rule-based costing engine for sheet metal and machined parts. 
Built using Python 3.11+, FastAPI, Pydantic, and Pandas.

## Key Features

- **Rule-Based Costing**: No neural networks or ML. Calculates cost using precise engineering costing formulas.
- **Excel Database Loading**: Reads material, process, and coating rates from Excel sheets (`.xlsx`).
- **Input Validation**: Automatically validates inputs using Pydantic schemas.
- **Auto-Calculations**: Computes part volume, surface area, and finished weight if they are not supplied in the payload.
- **Graceful Failure**: Falls back to internal config defaults if database Excel files are missing or lookup fails.
- **Hot-Reloadable Rates**: Exposes a `/reload-rates` administration endpoint to reload Excel rate sheets on-the-fly without service restart.

---

## Directory Structure

```
cost_engine/
│
├── cost_api/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Constants, default rates & densities
│   │
│   ├── costing/
│   │   ├── material_cost.py    # Raw Material cost calculator
│   │   ├── conversion_cost.py  # Processing/conversion calculator
│   │   ├── coating_cost.py     # Surface treatment calculator
│   │   ├── overhead_cost.py    # Overhead, ICC, and Rejection calculations
│   │   ├── profit_cost.py      # Profit component calculations
│   │   └── cost_engine.py      # Central calculator orchestrator
│   │
│   ├── database/
│   │   ├── loaders.py          # Excel sheet loader
│   │   ├── generate_excel.py   # Script to generate template rate sheets
│   │   ├── materials.xlsx      # Materials database
│   │   ├── process_rates.xlsx  # Process/Operation rates database
│   │   └── coating_rates.xlsx  # Coating/Plating rates database
│   │
│   ├── models/
│   │   ├── request_models.py   # Pydantic input models
│   │   └── response_models.py  # Pydantic response models
│   │
│   └── utils/
│       ├── area_calculator.py  # m² surface area calculations
│       ├── weight_calculator.py# Finished weight calculator
│       └── validators.py       # Input warnings check logic
│
└── requirements.txt
```

---

## Costing Formulas

The engine uses the following industrial calculations:

1. **Raw Material Cost** = `Finished Weight (kg)` × `Material Rate (per kg)`
2. **Conversion Cost** = `Σ (Process Count × Process Rate)`
3. **Coating Cost** = `Area (m²)` × `Coating Rate (per m²)`
4. **Overheads** = 10% of `Conversion Cost`
5. **ICC** = 1% of `Raw Material Cost`
6. **Rejection Cost** = 1% of (`Raw Material Cost` + `Conversion Cost`)
7. **Profit Margin** = 10% of (`Raw Material Cost` + `Conversion Cost`)
8. **Total Cost** = `Raw Material` + `Conversion` + `Coating` + `Overhead` + `ICC` + `Rejection` + `Profit`

---

## Setup & Startup Instructions

### Prerequisites
- Python 3.11 or later installed.
- Pip (Python Package Manager).

### 1. Install Dependencies
Navigate to the `cost_engine` directory and install the packages listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Generate Rate Databases (First Time)
To bootstrap the database folder with sample Excel files containing rate cards, run:
```bash
python -m cost_api.database.generate_excel
```
This will create `materials.xlsx`, `process_rates.xlsx`, and `coating_rates.xlsx` inside `cost_api/database/` with valid industrial default records.

### 3. Start the API Server
Run the FastAPI development server using Uvicorn:
```bash
uvicorn cost_api.main:app --host 0.0.0.0 --port 8000 --reload
```

- **API Documentation (Swagger)**: Navigate to `http://localhost:8000/docs` to test endpoints interactively.
- **API Base URL**: `http://localhost:8000`

---

## Endpoint API Spec

### POST `/estimate-cost`

#### Request Payload Example
```json
{
  "part_name": "Clamp",
  "material": "E46",
  "length_mm": 280,
  "width_mm": 75,
  "thickness_mm": 10,
  "finished_weight_kg": 1.25,
  "area_m2": 0.031923567,
  "operations": {
    "shearing": 1,
    "blanking": 1,
    "piercing": 1,
    "forming": 2,
    "welding": 0
  },
  "surface_treatment": "powder_coating"
}
```

#### Response Example
```json
{
  "part_name": "Clamp",
  "material": "E46",
  "finished_weight_kg": 1.25,
  "area_m2": 0.031923567,
  "cost_breakdown": {
    "raw_material_cost": 75.38,
    "conversion_cost": 7.86,
    "coating_cost": 3.26,
    "overhead": 0.79,
    "icc": 0.75,
    "rejection": 0.83,
    "profit": 8.32,
    "total_cost": 97.19
  },
  "notes": []
}
```
