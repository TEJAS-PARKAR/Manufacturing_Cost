# AI-Powered Supplier Negotiation & Cost Estimation Copilot

This repository now supports the requested multi-stage supplier negotiation workflow for Tata Motors procurement teams.

## What the platform now does

- Starts or resumes a negotiation session using the supplier employee ID and 12-digit part number.
- Lets a supplier upload a costing Excel sheet for automated extraction of dimensions, material, material rate, quantity, coating, process information, and weight when available.
- Flags missing mandatory fields and maintains per-session discussion memory.
- Stores supplier messages, extracted data, session summaries, and review recommendations by employee ID and part number.
- Submits the session for Tata Motors review.
- Produces benchmark comparisons and procurement recommendations such as accept, review, or negotiate further.

## Key backend pieces

- `backend/services/negotiation_service.py` handles session memory, Excel intake, extract-and-validate logic, summary generation, and review recommendations.
- `backend/routes/cost_routes.py` exposes the supplier session APIs.
- `backend/models.py` defines the negotiation request and response schemas.

## Main API flow

1. Start a supplier session using the employee ID and part number.
2. Upload the costing Excel file.
3. The system extracts available information and identifies missing mandatory fields.
4. Continue the conversation; the session summary and history are preserved.
5. Submit the session for review.
6. Tata Motors users can inspect benchmark recommendations and approve the final validated cost inputs.

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

## Production note

The current implementation stores session state in memory. For production, it should be backed by MongoDB Atlas persistence and a managed LLM orchestration layer.

