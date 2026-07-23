# AI-Powered Supplier Negotiation & Cost Estimation Copilot

A procurement negotiation platform for Tata Motors, enabling supplier costing sheet upload, LLM-assisted extraction, multi-round negotiation, and buyer review/approval workflows.

## How to run

Two services run simultaneously:

| Service | Command | Port |
|---------|---------|------|
| Backend API (FastAPI) | `uvicorn backend.main:app --host 0.0.0.0 --port 8000` | 8000 |
| Frontend (Streamlit) | `streamlit run frontend/app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true` | 5000 |

Both are configured as Replit workflows (`Backend API` and `Start application`).

## Login credentials

**Supplier portal**
- Username: `supplier` (or `SUPPLIER_USERNAME` env var)
- Password: `supplier123` (or `SUPPLIER_PASSWORD` env var)

**Tata Motors portal**
- Username: `tata` (or `TATA_USERNAME` env var)
- Password: `tata123` (or `TATA_PASSWORD` env var)

## Environment variables (optional)

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Enables LLM-assisted Excel extraction and AI negotiation replies (falls back to heuristics if not set) |
| `GROQ_MODEL` | Groq model name (default: `llama-3.1-8b-instant`) |
| `MONGODB_URI` | MongoDB Atlas URI for persistent session storage (uses in-memory by default) |
| `MONGODB_DB_NAME` | MongoDB database name (default: `manufacturing_cost`) |
| `MONGODB_COLLECTION` | Collection name (default: `supplier_sessions`) |

## Negotiation workflow

1. Choose **Supplier** portal and log in.
2. Enter Employee ID and Part Number → click **Start / Resume Session**.
3. Upload a costing Excel sheet and click **Process Excel Sheet**.
4. Chat with the AI negotiation assistant in the chat box.
5. Click **Submit for Tata Review** when ready.
6. Switch to **Tata Motors** portal → **Load Review Dashboard** → Approve or Reject.

## Stack

- **Backend**: FastAPI + Pydantic v2, Uvicorn
- **Frontend**: Streamlit + Plotly
- **Cost engine**: Custom Python (material / process / overhead calculators + XGBoost regressor)
- **LLM**: Groq API (optional), heuristic fallback always available
- **Persistence**: MongoDB Atlas (optional), in-memory by default

## User preferences

- Keep existing project structure and stack — do not restructure or migrate.
