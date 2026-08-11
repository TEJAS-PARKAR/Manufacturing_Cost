# AI-Powered Supplier Negotiation & Cost Estimation Copilot

This repository now supports the requested multi-stage supplier negotiation workflow for Tata Motors procurement teams.

## What the platform does

- Starts or resumes a negotiation session using the supplier employee ID and 12-digit part number.
- Lets a supplier upload a costing Excel sheet for automated extraction of **Sheet Dimensions** (Full Sheet Size), **Part Dimensions** (Shear Size), material, material rate, quantity, coating, process information, gross weight, and other cost components.
- Uses a two-stage Excel pipeline: raw table extraction first, then an interpretation layer for structured cost fields.
- Supports LLM-assisted extraction through Groq when a Groq API key is configured, with heuristic fallback when it is not.
- **Sheet Utilization Validation** — before any negotiation begins, validates whether the supplier is using the most efficient sheet size from a predefined list of approved sizes (`1250×2500`, `1500×2500`, `1250×2700`). If the current sheet is not optimal, negotiation is blocked and a recommendation is returned.
- **Cutting Allowance Confirmation** — asks the user whether extracted part dimensions already include cutting/shearing allowance. If not, applies the formula `effective_dim = dim + 1.5 × thickness` before computing utilization. **Negotiation chat is blocked until this question is answered.**
- **Server-Side Negotiation Gating** — the negotiation chatbot is locked server-side until: (1) a costing sheet has been uploaded, (2) the cutting allowance question has been answered, and (3) sheet size has been validated as optimal. This applies even if the session is resumed.
- Flags missing mandatory fields and maintains per-session discussion memory.
- Stores supplier messages, extracted data, session summaries, sheet optimization results, and review recommendations by employee ID and part number.
- Supports separate supplier and Tata Motors workspaces with distinct login credentials.
- Submits the session for Tata Motors review and enables approval of validated cost inputs.
- **Rejection Re-Entry** — when Tata Motors rejects a quotation, the rejection reason is stored and shown to the supplier. The supplier can reopen the session for re-negotiation, which resets the validation flow and requires a revised costing sheet.
- Produces benchmark comparisons and procurement recommendations such as accept, review, or negotiate further.
- All numeric values (dimensions, weights, costs, variance, counter-offers) are rounded to **2 decimal places** across the entire application.

## Key backend pieces

- [backend/services/negotiation_service.py](backend/services/negotiation_service.py) handles session memory, Excel intake, raw-table extraction, LLM/heuristic interpretation, **sheet optimization validation**, summary generation, and review recommendations.
- [backend/routes/cost_routes.py](backend/routes/cost_routes.py) exposes the supplier session APIs, **sheet optimization check**, and review/approval endpoints.
- [backend/models.py](backend/models.py) defines the negotiation request and response schemas.

## Frontend (React + Vite)

The frontend is a React single-page application built with Vite, located in `frontend/`. Key files:

- `frontend/src/App.jsx` — Root app with portal selection, authentication, and session state.
- `frontend/src/api.js` — API client wrapping all backend endpoints.
- `frontend/src/components/` — Modular components (Sidebar, LoginPage, SupplierPortal, TataPortal, CostChart, ChatHistory, etc.).
- `frontend/src/index.css` — Tata Motors branded design system.

## Main workflow

1. Open the app and choose either the Supplier or Tata Motors portal.
2. Log in with the matching credentials for the selected portal.
3. Start or resume a supplier session using the employee ID and part number.
4. Upload the costing Excel file.
5. The system extracts **Sheet Dimensions** (Full Sheet Size) and **Part Dimensions** (Shear Size) separately, along with all cost components.
6. The system asks: *"Do the extracted part dimensions already include cutting/shearing allowance?"* — **negotiation chat remains locked until this is answered.**
7. Sheet utilization is validated against approved sheet sizes. If the current sheet is not optimal, negotiation is blocked with a recommendation to revise.
8. If the sheet is optimal, continue the conversation; the session summary and history are preserved.
9. Submit the session for review.
10. Tata Motors users can inspect sheet optimization results, benchmark recommendations, and approve or reject the final validated cost inputs.
11. **If rejected**, the supplier sees the rejection reason and can reopen the session. Reopening resets the validation flow and requires a revised costing sheet upload.

### Sheet Optimization Logic

The system calculates how many parts fit on each approved sheet size using:

```
effective_length = part_length + 1.5 × thickness   (if allowance not included)
effective_width  = part_width  + 1.5 × thickness    (if allowance not included)

pieces_normal  = floor(sheet_L / eff_L) × floor(sheet_W / eff_W)
pieces_rotated = floor(sheet_L / eff_W) × floor(sheet_W / eff_L)
pieces = max(normal, rotated)

weight_per_part = (sheet_L × sheet_W × thickness × 7.85) / (10⁶ × pieces)
```

The sheet with the **most parts** (lowest weight per part) is selected as optimal. If the supplier's sheet does not match, negotiation is blocked until the costing sheet is revised.

## Quick start

### Using scripts (recommended)

**Linux / macOS:**
```bash
./scripts/setup.sh          # Install all dependencies (Python + Node.js)
./scripts/start_backend.sh  # Start the FastAPI backend on :8000
./scripts/start_frontend.sh # Start the React frontend on :5173
```

**Windows:**
```batch
scripts\setup.bat           :: Install all dependencies (Python + Node.js)
scripts\start_backend.bat   :: Start the FastAPI backend on :8000
scripts\start_frontend.bat  :: Start the React frontend on :5173
```

### Manual start

```bash
# Terminal 1: Backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

The frontend will open at `http://localhost:5173`.

## Environment variables

Set the following before running the app if you want the LLM-backed extraction to use Groq:

```bash
export GROQ_API_KEY="your_groq_api_key"
export GROQ_MODEL="llama-3.1-8b-instant"
```

Optional portal credentials:

```bash
export VITE_SUPPLIER_USERNAME=""
export VITE_SUPPLIER_PASSWORD=""
export VITE_TATA_USERNAME=""
export VITE_TATA_PASSWORD=""
```

Optional MongoDB Atlas persistence:

```bash
export MONGODB_URI="mongodb+srv://<user>:<password>@<cluster>/<db>?retryWrites=true&w=majority"
export MONGODB_DB_NAME="manufacturing_cost"
export MONGODB_COLLECTION="supplier_sessions"
```

Frontend environment variables (optional, create `frontend/.env`):

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_SUPPLIER_USERNAME=supplier
VITE_SUPPLIER_PASSWORD=supplier123
VITE_TATA_USERNAME=tata
VITE_TATA_PASSWORD=tata123
```

If a Groq key is not configured, the app will continue to work with its built-in heuristic extraction fallback. If MongoDB is not configured, sessions remain in memory for the current process.

## Production note

The current implementation uses in-memory session storage by default. For production, you can enable MongoDB Atlas persistence and a managed LLM orchestration layer for higher durability and multi-instance support.
