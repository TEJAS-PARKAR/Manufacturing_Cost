# AI-Powered Supplier Negotiation & Cost Estimation Copilot

This repository now supports the requested multi-stage supplier negotiation workflow for Tata Motors procurement teams.

## What the platform now does

- Starts or resumes a negotiation session using the supplier employee ID and 12-digit part number.
- Lets a supplier upload a costing Excel sheet for automated extraction of dimensions, material, material rate, quantity, coating, process information, and weight when available.
- Uses a two-stage Excel pipeline: raw table extraction first, then an interpretation layer for structured cost fields.
- Supports LLM-assisted extraction through Groq when a Groq API key is configured, with heuristic fallback when it is not.
- Flags missing mandatory fields and maintains per-session discussion memory.
- Stores supplier messages, extracted data, session summaries, and review recommendations by employee ID and part number.
- Supports separate supplier and Tata Motors workspaces with distinct login credentials.
- Submits the session for Tata Motors review and enables approval of validated cost inputs.
- Produces benchmark comparisons and procurement recommendations such as accept, review, or negotiate further.

## Key backend pieces

- [backend/services/negotiation_service.py](backend/services/negotiation_service.py) handles session memory, Excel intake, raw-table extraction, LLM/heuristic interpretation, summary generation, and review recommendations.
- [backend/routes/cost_routes.py](backend/routes/cost_routes.py) exposes the supplier session APIs and review/approval endpoints.
- [backend/models.py](backend/models.py) defines the negotiation request and response schemas.
- [frontend/app.py](frontend/app.py) provides the supplier and Tata Motors Streamlit interfaces.

## Main workflow

1. Open the app and choose either the Supplier or Tata Motors portal.
2. Log in with the matching credentials for the selected portal.
3. Start or resume a supplier session using the employee ID and part number.
4. Upload the costing Excel file.
5. The system extracts the raw table and interprets it into structured negotiation fields.
6. Continue the conversation; the session summary and history are preserved.
7. Submit the session for review.
8. Tata Motors users can inspect benchmark recommendations and approve the final validated cost inputs.

## Quick start

### Recommended: use the included scripts

```bash
./scripts/setup.sh
source .venv/bin/activate
./scripts/start_backend.sh
./scripts/start_frontend.sh
```

### Alternative manual start

```bash
python3 -m pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
streamlit run frontend/app.py
```

## Environment variables

Set the following before running the app if you want the LLM-backed extraction to use Groq:

```bash
export GROQ_API_KEY="your_groq_api_key"
export GROQ_MODEL="llama-3.1-8b-instant"
```

Optional portal credentials:

```bash
export SUPPLIER_USERNAME="supplier"
export SUPPLIER_PASSWORD="supplier123"
export TATA_USERNAME="tata"
export TATA_PASSWORD="tata123"
```

Optional MongoDB Atlas persistence:

```bash
export MONGODB_URI="mongodb+srv://<user>:<password>@<cluster>/<db>?retryWrites=true&w=majority"
export MONGODB_DB_NAME="manufacturing_cost"
export MONGODB_COLLECTION="supplier_sessions"
```

If a Groq key is not configured, the app will continue to work with its built-in heuristic extraction fallback. If MongoDB is not configured, sessions remain in memory for the current process.

## Production note

The current implementation uses in-memory session storage by default. For production, you can enable MongoDB Atlas persistence and a managed LLM orchestration layer for higher durability and multi-instance support.

