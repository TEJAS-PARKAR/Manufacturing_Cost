import os
from pathlib import Path

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import requests
# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _api_base_url() -> str:
    return os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


# ─────────────────────────────────────────────────────────────────────
# Custom CSS Theme — Tata Motors Branded
# ─────────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Sidebar branding ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1B2A 0%, #1B3A5C 50%, #274C77 100%);
}
section[data-testid="stSidebar"] * {
    color: #E0E6ED !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #E0E6ED !important;
    font-weight: 500;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15);
}

/* ── Header bar ── */
.main-header {
    background: linear-gradient(135deg, #1B3A5C 0%, #274C77 50%, #1B3A5C 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(27, 58, 92, 0.25);
}
.main-header h1 {
    color: #FFFFFF !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    padding: 0 !important;
    letter-spacing: -0.02em;
}
.main-header p {
    color: #A8C4E0 !important;
    font-size: 0.9rem !important;
    margin: 0.3rem 0 0 0 !important;
}

/* ── Status badges ── */
.status-badge {
    display: inline-block;
    padding: 0.35rem 1rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.status-active {
    background: rgba(0, 168, 107, 0.15);
    color: #00A86B;
    border: 1px solid rgba(0, 168, 107, 0.3);
}
.status-submitted {
    background: rgba(232, 179, 0, 0.15);
    color: #E8B300;
    border: 1px solid rgba(232, 179, 0, 0.3);
}
.status-approved {
    background: rgba(0, 168, 107, 0.15);
    color: #00A86B;
    border: 1px solid rgba(0, 168, 107, 0.3);
}
.status-rejected {
    background: rgba(220, 53, 69, 0.15);
    color: #DC3545;
    border: 1px solid rgba(220, 53, 69, 0.3);
}
.status-pending {
    background: rgba(108, 117, 125, 0.15);
    color: #6C757D;
    border: 1px solid rgba(108, 117, 125, 0.3);
}

/* ── Metric cards ── */
.metric-card {
    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
    border: 1px solid #e9ecef;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
.metric-card .label {
    color: #6C757D;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.4rem;
}
.metric-card .value {
    color: #1B3A5C;
    font-size: 1.4rem;
    font-weight: 700;
}
.metric-card.accent {
    border-left: 4px solid #E8B300;
}
.metric-card.success {
    border-left: 4px solid #00A86B;
}
.metric-card.danger {
    border-left: 4px solid #DC3545;
}

/* ── Chat messages ── */
.chat-supplier {
    background: #ffffff;
    border: 1px solid #dee2e6;
    border-left: 4px solid #1B3A5C;
    padding: 0.8rem 1rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 0.6rem;
    color: #212529;
}
.chat-assistant {
    background: #ffffff;
    border: 1px solid #dee2e6;
    border-left: 4px solid #00A86B;
    padding: 0.8rem 1rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 0.6rem;
    color: #212529;
}
.chat-system {
    background: #ffffff;
    border: 1px solid #dee2e6;
    border-left: 4px solid #E8B300;
    padding: 0.8rem 1rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 0.6rem;
    color: #212529;
}
.chat-role {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.3rem;
    color: #6C757D;
}
.chat-msg {
    font-size: 0.9rem;
    line-height: 1.5;
    color: #212529;
}
.chat-ts {
    font-size: 0.65rem;
    color: #999;
    margin-top: 0.4rem;
}

/* ── Section divider ── */
.section-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, #dee2e6, transparent);
    margin: 1.5rem 0;
}

/* ── Recommendation badges ── */
.rec-accept {
    background: linear-gradient(135deg, #00A86B, #28a745);
    color: white;
    padding: 0.6rem 1.5rem;
    border-radius: 8px;
    font-weight: 700;
    text-align: center;
    font-size: 1rem;
}
.rec-review {
    background: linear-gradient(135deg, #E8B300, #ffc107);
    color: #1a1a1a;
    padding: 0.6rem 1.5rem;
    border-radius: 8px;
    font-weight: 700;
    text-align: center;
    font-size: 1rem;
}
.rec-negotiate {
    background: linear-gradient(135deg, #DC3545, #e74c5c);
    color: white;
    padding: 0.6rem 1.5rem;
    border-radius: 8px;
    font-weight: 700;
    text-align: center;
    font-size: 1rem;
}

/* ── Login container ── */
.login-container {
    max-width: 420px;
    margin: 2rem auto;
    padding: 2rem;
    background: white;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    border: 1px solid #e9ecef;
}
.login-header {
    text-align: center;
    margin-bottom: 1.5rem;
}
.login-header h2 {
    color: #1B3A5C;
    font-weight: 700;
    margin: 0;
}
.login-header p {
    color: #6C757D;
    font-size: 0.85rem;
    margin-top: 0.3rem;
}

/* ── Progress stepper ── */
.stepper {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 1rem 0 1.5rem 0;
    padding: 0 1rem;
}
.step {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    position: relative;
}
.step-dot {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    color: white;
    z-index: 1;
}
.step-dot.done { background: #00A86B; }
.step-dot.current { background: #E8B300; animation: pulse 2s infinite; }
.step-dot.pending { background: #dee2e6; color: #999; }
.step-label {
    font-size: 0.7rem;
    margin-top: 0.4rem;
    color: #6C757D;
    font-weight: 500;
    text-align: center;
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(232,179,0,0.4); }
    50% { box-shadow: 0 0 0 8px rgba(232,179,0,0); }
}
</style>
"""


def _render_status_badge(status: str) -> str:
    """Return an HTML status badge for the given session status."""
    status_map = {
        "active": ("Active", "status-active"),
        "submitted_for_review": ("Submitted for Review", "status-submitted"),
        "approved": ("Approved", "status-approved"),
        "rejected": ("Rejected", "status-rejected"),
    }
    label, css_class = status_map.get(status, ("Pending", "status-pending"))
    return f'<span class="status-badge {css_class}">{label}</span>'


def _render_stepper(status: str) -> str:
    """Render a visual progress stepper based on session status."""
    steps = [
        ("1", "Session Started"),
        ("2", "Data Extracted"),
        ("3", "Submitted"),
        ("4", "Decision"),
    ]
    status_progress = {
        "active": 1,
        "submitted_for_review": 3,
        "approved": 4,
        "rejected": 4,
    }
    current_step = status_progress.get(status, 0)
    html = '<div class="stepper">'
    for i, (num, label) in enumerate(steps, 1):
        if i < current_step:
            dot_class = "done"
            icon = "✓"
        elif i == current_step:
            dot_class = "current"
            icon = num
        else:
            dot_class = "pending"
            icon = num
        html += f'''
        <div class="step">
            <div class="step-dot {dot_class}">{icon}</div>
            <div class="step-label">{label}</div>
        </div>'''
    html += '</div>'
    return html


def _metric_card(label: str, value, card_class: str = "") -> str:
    """Return HTML for a single styled metric card."""
    return f'''
    <div class="metric-card {card_class}">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
    </div>'''


def _render_session_status(session: dict) -> None:
    extracted = session.get("extracted_data", {})
    status = session.get("status", "active")

    # Status badge + stepper
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.5rem;">'
        f'<h3 style="margin:0;color:#1B3A5C;">Session Overview</h3>'
        f'{_render_status_badge(status)}'
        f'</div>',
        unsafe_allow_html=True
    )
    st.markdown(_render_stepper(status), unsafe_allow_html=True)

    # Metric cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(_metric_card("Part Number", session.get("part_number", "—")), unsafe_allow_html=True)
    with col2:
        st.markdown(_metric_card("Material", extracted.get("material", "—")), unsafe_allow_html=True)
    with col3:
        st.markdown(_metric_card("Material Rate", f'₹ {extracted.get("material_rate", "—")}', "accent"), unsafe_allow_html=True)
    with col4:
        total = extracted.get("total_cost", 0)
        st.markdown(_metric_card("Total Cost", f"₹ {round(total, 2) if total else '—'}", "success"), unsafe_allow_html=True)

    if session.get("missing_fields"):
        st.warning(f"Missing Fields: **{', '.join(session['missing_fields'])}**")
    else:
        st.success("All mandatory fields available.")


def render_cost_summary(session):
    extracted = session.get("extracted_data", {})
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### Costing Summary")
    data = {
        "Parameter": [
            "Material", "Material Rate", "Thickness", "Width", "Length",
            "Finished Weight", "Scrap Weight", "RM Cost",
            "Conversion Cost", "Coating Cost", "Total Cost",
        ],
        "Value": [
            str(extracted.get("material", "—")),
            str(extracted.get("material_rate", "—")),
            str(extracted.get("thickness", "—")),
            str(extracted.get("width", "—")),
            str(extracted.get("length", "—")),
            str(extracted.get("finished_weight", "—")),
            str(extracted.get("scrap_weight", "—")),
            str(extracted.get("raw_material_cost", "—")),
            str(extracted.get("conversion_cost", "—")),
            str(extracted.get("coating_cost", "—")),
            str(extracted.get("total_cost", "—")),
        ],
    }
    df = pd.DataFrame(data)
    st.dataframe(df, width="stretch", hide_index=True)


def render_cost_chart(session):
    extracted = session.get("extracted_data", {})
    rm = float(extracted.get("raw_material_cost", 0) or 0)
    conversion = float(extracted.get("conversion_cost", 0) or 0)
    coating = float(extracted.get("coating_cost", 0) or 0)

    if rm == 0 and conversion == 0 and coating == 0:
        return

    df = pd.DataFrame({
        "Cost Type": ["Raw Material", "Conversion", "Coating"],
        "Cost (₹)": [rm, conversion, coating],
    })
    fig = px.pie(
        df, names="Cost Type", values="Cost (₹)",
        title="Cost Breakdown",
        color_discrete_sequence=["#1B3A5C", "#E8B300", "#00A86B"],
        hole=0.4,
    )
    fig.update_layout(
        font_family="Inter",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=20, l=20, r=20),
    )
    st.plotly_chart(fig, width="stretch")


def _render_chat_history(history: list) -> None:
    """Render chat messages with clean, readable styled bubbles."""
    if not history:
        st.info("No messages yet. Start the conversation below.")
        return

    for item in history:
        role = item.get("role", "system")
        message = item.get("message", "")
        timestamp = item.get("timestamp", "")

        if role == "supplier":
            css_class = "chat-supplier"
            role_label = "Supplier"
        elif role == "assistant":
            css_class = "chat-assistant"
            role_label = "AI Buyer Agent"
        elif role == "tata":
            css_class = "chat-assistant"
            role_label = "Tata Motors"
        else:
            css_class = "chat-system"
            role_label = "System"

        ts_html = f'<div class="chat-ts">{timestamp}</div>' if timestamp else ""
        st.markdown(
            f'<div class="{css_class}">'
            f'<div class="chat-role">{role_label}</div>'
            f'<div class="chat-msg">{message}</div>'
            f'{ts_html}'
            f'</div>',
            unsafe_allow_html=True
        )


def main() -> None:
    st.set_page_config(
        page_title="Supplier Negotiation Copilot — Tata Motors",
        page_icon="TM",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    api_base_url = _api_base_url()

    # ── Header ──
    st.markdown(
        '<div class="main-header">'
        '<h1>AI-Powered Supplier Negotiation & Cost Estimation Copilot</h1>'
        '<p>Supplier-side intake | Excel extraction | Negotiation memory | Tata Motors review handoff</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # ── Initialize session state ──
    if "portal" not in st.session_state:
        st.session_state.portal = "Supplier"
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "authenticated_portal" not in st.session_state:
        st.session_state.authenticated_portal = None

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### Portal Access")
        st.markdown("---")
        portal = st.radio(
            "Choose your workspace",
            ["Supplier", "Tata Motors"],
            horizontal=False,
            key="portal_selector",
            help="Select the portal matching your role",
        )
        if portal != st.session_state.portal:
            st.session_state.authenticated = False
            st.session_state.authenticated_portal = None
        st.session_state.portal = portal

        if st.session_state.portal == "Supplier":
            st.caption("Upload cost sheets, negotiate pricing, and submit for review.")
        else:
            st.caption("Review supplier quotes, benchmark comparisons, and approve/reject.")

        st.markdown("---")

        # Logout button
        if st.session_state.authenticated:
            st.markdown(f"**Logged in as:** `{st.session_state.get('username', '—')}`")
            st.markdown(f"**Portal:** {st.session_state.portal}")
            if st.button("Logout", width="stretch"):
                st.session_state.authenticated = False
                st.session_state.authenticated_portal = None
                st.session_state.session = None
                if "review_dashboard" in st.session_state:
                    del st.session_state["review_dashboard"]
                st.rerun()

    # ── Login gate ──
    if not st.session_state.authenticated:
        portal_desc = (
            "Upload costing sheets and negotiate with Tata Motors AI buyer."
            if st.session_state.portal == "Supplier"
            else "Review supplier quotes, compare benchmarks, and make decisions."
        )

        st.markdown(
            f'<div class="login-container">'
            f'<div class="login-header">'
            f'<h2>{st.session_state.portal} Portal</h2>'
            f'<p>{portal_desc}</p>'
            f'</div></div>',
            unsafe_allow_html=True
        )

        col_login = st.columns([1, 2, 1])[1]
        with col_login:
            username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
            if st.button("Login", width="stretch", type="primary"):
                expected = {
                    "Supplier": {
                        "username": os.getenv("SUPPLIER_USERNAME", "supplier"),
                        "password": os.getenv("SUPPLIER_PASSWORD", "supplier123"),
                    },
                    "Tata Motors": {
                        "username": os.getenv("TATA_USERNAME", "tata"),
                        "password": os.getenv("TATA_PASSWORD", "tata123"),
                    },
                }[st.session_state.portal]
                if username == expected["username"] and password == expected["password"]:
                    st.session_state.authenticated = True
                    st.session_state.authenticated_portal = st.session_state.portal
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
        return

    # ── Session identification ──
    id_col1, id_col2 = st.columns(2)
    with id_col1:
        employee_id = st.text_input("Employee ID", placeholder="EMP1001", key="employee_id")
    with id_col2:
        part_number = st.text_input("Part Number", placeholder="123456789012", key="part_number")

    if st.button("Start / Resume Session", type="primary", width="stretch"):
        if employee_id and part_number:
            with st.spinner("Loading session..."):
                try:
                    response = requests.get(
                        f"{api_base_url}/supplier/session/context",
                        params={"employee_id": employee_id, "part_number": part_number},
                        timeout=45,
                    )
                    response.raise_for_status()
                    st.session_state.session = response.json()
                    st.rerun()
                except requests.exceptions.RequestException as exc:
                    st.error(f"Unable to reach the backend: {exc}")
        else:
            st.warning("Please enter both Employee ID and Part Number.")

    if "session" not in st.session_state:
        st.session_state.session = None

    # ═══════════════════════════════════════════════════════════════
    #  SUPPLIER PORTAL
    # ═══════════════════════════════════════════════════════════════
    if st.session_state.portal == "Supplier" and st.session_state.session is not None:
        _render_session_status(st.session_state.session)

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # ── Excel upload ──
        st.markdown("### Upload Costing Excel Sheet")
        uploaded_file = st.file_uploader(
            "Upload your costing Excel sheet",
            type=["xlsx", "xls"],
            label_visibility="collapsed",
        )

        # Cache uploaded file in session state to survive reruns
        if uploaded_file is not None:
            st.session_state["_cached_upload"] = {
                "name": uploaded_file.name,
                "data": uploaded_file.getvalue(),
                "type": uploaded_file.type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }

        cached = st.session_state.get("_cached_upload")
        if cached is not None:
            st.info(f"File ready: **{cached['name']}**")
            if st.button("Process Excel Sheet", type="primary"):
                with st.spinner("Extracting data from Excel sheet..."):
                    try:
                        files = {"file": (cached["name"], cached["data"], cached["type"])}
                        response = requests.post(
                            f"{api_base_url}/supplier/session/upload-excel",
                            params={"employee_id": employee_id, "part_number": part_number},
                            files=files,
                            timeout=60,
                        )
                        response.raise_for_status()
                        st.session_state.session = response.json()
                        # Clear cached upload after successful processing
                        del st.session_state["_cached_upload"]
                        st.success("Excel data extracted and merged into the session.")
                        st.rerun()
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Excel upload failed: {exc}")

        # ── Cost summary + chart (show after extraction) ──
        extracted = st.session_state.session.get("extracted_data", {})
        if extracted.get("total_cost"):
            chart_col, summary_col = st.columns([1, 1])
            with chart_col:
                render_cost_chart(st.session_state.session)
            with summary_col:
                render_cost_summary(st.session_state.session)

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # ── Negotiation chat ──
        st.markdown("### Negotiation Chat")
        _render_chat_history(st.session_state.session.get("history", []))

        supplier_message = st.chat_input("Enter supplier demand...")

        if supplier_message:
            with st.spinner("Processing your message..."):
                try:
                    response = requests.post(
                        f"{api_base_url}/supplier/session/negotiate",
                        json={
                            "employee_id": employee_id,
                            "part_number": part_number,
                            "message": supplier_message,
                        },
                        timeout=45,
                    )
                    response.raise_for_status()
                    api_result = response.json()
                    st.session_state.session = api_result["session"]
                    st.rerun()
                except requests.exceptions.RequestException as exc:
                    st.error(f"Message processing failed: {exc}")

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # ── Submit for review ──
        session_status = st.session_state.session.get("status", "active")
        if session_status == "active":
            st.markdown("### Submit for Review")
            st.info("Once submitted, your session will be visible to the Tata Motors review dashboard.")
            if st.button("Submit for Tata Motors Review", type="primary", width="stretch"):
                with st.spinner("Submitting session for review..."):
                    try:
                        response = requests.post(
                            f"{api_base_url}/supplier/session/submit-review",
                            params={"employee_id": employee_id, "part_number": part_number},
                            timeout=45,
                        )
                        response.raise_for_status()
                        st.session_state.session = response.json()
                        st.success("Session submitted to Tata Motors review dashboard!")
                        st.rerun()
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Submission failed: {exc}")
        elif session_status == "submitted_for_review":
            st.info("This session has been submitted for Tata Motors review. Awaiting decision.")
        elif session_status == "approved":
            st.success("This session has been **approved** by Tata Motors.")
        elif session_status == "rejected":
            st.error("This session has been **rejected** by Tata Motors.")

    # ═══════════════════════════════════════════════════════════════
    #  TATA MOTORS REVIEW PORTAL
    # ═══════════════════════════════════════════════════════════════
    elif st.session_state.portal == "Tata Motors":

        st.markdown("### Tata Motors Review Dashboard")
        st.caption("Review supplier sessions, benchmark comparisons, and approve/reject final inputs.")

        if st.button("Load Review Dashboard", type="primary", width="stretch"):
            with st.spinner("Loading review dashboard..."):
                try:
                    response = requests.get(
                        f"{api_base_url}/supplier/session/review",
                        params={
                            "employee_id": employee_id,
                            "part_number": part_number,
                        },
                        timeout=45,
                    )
                    response.raise_for_status()
                    st.session_state.review_dashboard = response.json()
                    st.rerun()
                except requests.exceptions.RequestException as exc:
                    st.error(f"Review lookup failed: {exc}")

        if (
            "review_dashboard" in st.session_state
            and st.session_state.review_dashboard
        ):
            dashboard = st.session_state.review_dashboard
            if not isinstance(dashboard, dict):
                st.error(f"Expected dict, got {type(dashboard)}")
                st.stop()

            session = dashboard.get("session", {})

            # ── Session overview ──
            _render_session_status(session)

            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            # ── Cost summary + chart ──
            extracted = session.get("extracted_data", {})
            if extracted.get("total_cost"):
                chart_col, summary_col = st.columns([1, 1])
                with chart_col:
                    render_cost_chart(session)
                with summary_col:
                    render_cost_summary(session)

            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            # ── Benchmark comparison ──
            benchmark = dashboard.get("benchmark_comparison", {})
            st.markdown("### Benchmark Comparison")

            bm_col1, bm_col2, bm_col3 = st.columns(3)
            with bm_col1:
                st.markdown(
                    _metric_card("Supplier Rate", f"₹ {benchmark.get('supplier_material_rate', 0)}"),
                    unsafe_allow_html=True
                )
            with bm_col2:
                st.markdown(
                    _metric_card("Benchmark Rate", f"₹ {benchmark.get('internal_benchmark_rate', 0)}", "accent"),
                    unsafe_allow_html=True
                )
            with bm_col3:
                variance = benchmark.get("variance", 0)
                card_type = "success" if variance <= 0 else "danger"
                st.markdown(
                    _metric_card("Variance", f"₹ {variance}", card_type),
                    unsafe_allow_html=True
                )

            recommendation = benchmark.get("recommendation", "review")
            if recommendation == "accept":
                st.markdown('<div class="rec-accept">RECOMMENDATION: ACCEPT</div>', unsafe_allow_html=True)
            elif recommendation == "review":
                st.markdown('<div class="rec-review">RECOMMENDATION: REVIEW</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="rec-negotiate">RECOMMENDATION: NEGOTIATE FURTHER</div>', unsafe_allow_html=True)

            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            # ── Negotiation analysis ──
            negotiation = session.get("negotiation", {})
            st.markdown("### Negotiation Analysis")

            n_col1, n_col2, n_col3 = st.columns(3)
            with n_col1:
                st.markdown(
                    _metric_card("Supplier Quote", f"₹ {negotiation.get('supplier_quote', 0)}"),
                    unsafe_allow_html=True
                )
            with n_col2:
                st.markdown(
                    _metric_card("Expected Cost", f"₹ {negotiation.get('predicted_cost', 0)}", "accent"),
                    unsafe_allow_html=True
                )
            with n_col3:
                var_pct = negotiation.get("variance", 0)
                card_type = "success" if var_pct <= 5 else "danger"
                st.markdown(
                    _metric_card("Variance %", f"{var_pct}%", card_type),
                    unsafe_allow_html=True
                )

            ai_rec = negotiation.get("ai_recommendation", "—")
            counter = negotiation.get("counter_offer", "—")
            st.info(f"**AI Recommendation:** {ai_rec.upper() if isinstance(ai_rec, str) else ai_rec}")
            st.success(f"**Suggested Counter Offer:** ₹{counter}")

            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            # ── Chat history ──
            st.markdown("### Negotiation History")
            _render_chat_history(session.get("history", []))

            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            # ── Buyer actions (approve/reject) ──
            if session.get("status") == "submitted_for_review":
                st.markdown("### Buyer Actions")

                action_col1, action_col2 = st.columns(2)

                with action_col1:
                    st.markdown("#### Approve Quotation")
                    st.caption("Approving will finalize the cost inputs for procurement.")
                    if st.button("Approve Quotation", type="primary", width="stretch", key="approve_btn"):
                        with st.spinner("Approving..."):
                            try:
                                response = requests.post(
                                    f"{api_base_url}/supplier/session/approve",
                                    params={
                                        "employee_id": employee_id,
                                        "part_number": part_number
                                    },
                                    timeout=45,
                                )
                                response.raise_for_status()
                                st.success("Offer Approved Successfully!")
                                # Reload dashboard
                                dash_resp = requests.get(
                                    f"{api_base_url}/supplier/session/review",
                                    params={"employee_id": employee_id, "part_number": part_number},
                                    timeout=45,
                                )
                                dash_resp.raise_for_status()
                                st.session_state.review_dashboard = dash_resp.json()
                                st.rerun()
                            except requests.exceptions.RequestException as exc:
                                st.error(f"Approval failed: {exc}")

                with action_col2:
                    st.markdown("#### Reject Quotation")
                    reject_reason = st.selectbox(
                        "Rejection Reason",
                        [
                            "Cost Above Benchmark",
                            "Material Rate Too High",
                            "Conversion Cost Too High",
                            "Commercial Terms Not Acceptable",
                            "Incomplete Cost Sheet",
                            "Other"
                        ],
                        key="reject_reason"
                    )
                    if st.button("Reject Quotation", width="stretch", key="reject_btn"):
                        with st.spinner("Rejecting..."):
                            try:
                                response = requests.post(
                                    f"{api_base_url}/supplier/session/reject",
                                    params={
                                        "employee_id": employee_id,
                                        "part_number": part_number,
                                        "reason": reject_reason
                                    },
                                    timeout=45,
                                )
                                response.raise_for_status()
                                st.success("Offer Rejected")
                                # Reload dashboard
                                dash_resp = requests.get(
                                    f"{api_base_url}/supplier/session/review",
                                    params={"employee_id": employee_id, "part_number": part_number},
                                    timeout=45,
                                )
                                dash_resp.raise_for_status()
                                st.session_state.review_dashboard = dash_resp.json()
                                st.rerun()
                            except requests.exceptions.RequestException as exc:
                                st.error(f"Rejection failed: {exc}")

            elif session.get("status") == "approved":
                st.success("This quotation has been **approved**. No further actions needed.")
            elif session.get("status") == "rejected":
                st.error("This quotation has been **rejected**.")


if __name__ == "__main__":
    main()
