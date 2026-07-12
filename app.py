"""
Manufacturing Cost Estimation Assistant
A Streamlit application that extracts structured manufacturing data
from natural language part descriptions using OpenAI GPT-4o.
"""

import json
import streamlit as st
import requests
from dotenv import load_dotenv
import os

from prompt import SYSTEM_PROMPT
from utils import call_openai, parse_response, get_default_extracted_data

# Load environment variables
load_dotenv()

# ─────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Manufacturing Cost Estimator",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom Styling
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 165, 0, 0.15);
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #f0a500;
        font-size: 0.9rem;
        margin: 0.3rem 0 0 0;
        font-weight: 400;
    }

    /* Data card styling */
    .data-card {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid rgba(255, 165, 0, 0.12);
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
    }
    .data-card-title {
        color: #f0a500;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 0.4rem;
    }
    .data-card-value {
        color: #e8e8e8;
        font-size: 1.15rem;
        font-weight: 500;
    }

    /* Operations table styling */
    .ops-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 8px;
        overflow: hidden;
    }
    .ops-table th {
        background: rgba(240, 165, 0, 0.15);
        color: #f0a500;
        padding: 0.6rem 1rem;
        text-align: left;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .ops-table td {
        padding: 0.5rem 1rem;
        color: #e0e0e0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 0.9rem;
    }
    .ops-table tr:last-child td {
        border-bottom: none;
    }
    .ops-active {
        color: #4ade80 !important;
        font-weight: 600;
    }
    .ops-zero {
        color: #555 !important;
    }

    /* Status badges */
    .badge-complete {
        background: rgba(74, 222, 128, 0.15);
        color: #4ade80;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-missing {
        background: rgba(251, 191, 36, 0.15);
        color: #fbbf24;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }

    /* Missing info alert */
    .missing-alert {
        background: rgba(251, 191, 36, 0.08);
        border: 1px solid rgba(251, 191, 36, 0.25);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-top: 0.5rem;
    }
    .missing-alert-title {
        color: #fbbf24;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .missing-alert-item {
        color: #e0c36a;
        font-size: 0.85rem;
        padding: 0.15rem 0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #f0a500;
    }

    /* Chat message customization */
    .stChatMessage {
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Session State Initialization
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []  # Chat history for display

if "api_messages" not in st.session_state:
    st.session_state.api_messages = []  # Messages sent to OpenAI (includes system prompt)

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

if "cost_breakdown" not in st.session_state:
    st.session_state.cost_breakdown = None

if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("OPENAI_API_KEY", "")
    if not st.session_state.api_key or st.session_state.api_key == "your-api-key-here":
        st.error("OPENAI_API_KEY not found in .env file. Please add your key to the .env file and restart.")
        st.stop()

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Manufacturing Cost Assistant")
    st.markdown("---")

    # New Chat Button
    if st.button("New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.api_messages = []
        st.session_state.extracted_data = None
        st.session_state.cost_breakdown = None
        st.rerun()

    st.markdown("---")

    # Instructions
    st.markdown("### How to Use")
    st.markdown("""
    1. Describe your manufacturing part
    2. The AI will extract structured data
    3. Answer follow-up questions if needed
    4. Export the final JSON
    """)

    st.markdown("---")
    st.markdown("### Example Input")
    st.code(
        'Need cost for a clamp made from\n'
        'E46 plate. Size 280 x 75 mm.\n'
        'Thickness 10 mm. Operations:\n'
        'Blanking, Piercing, 2 Forming\n'
        'Operations. Powder Coating.',
        language=None,
    )

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>Manufacturing Cost Estimation Assistant</h1>
    <p>Describe your part in natural language — AI extracts structured costing data</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Main Layout: Chat (left) + Data Panel (right)
# ─────────────────────────────────────────────
chat_col, data_col = st.columns([1.2, 1], gap="large")

# ─────────────────────────────────────────────
# RIGHT COLUMN: Extracted Data Panel
# ─────────────────────────────────────────────
with data_col:
    st.markdown("### Extracted Data")

    if st.session_state.extracted_data:
        data = st.session_state.extracted_data
        missing = data.get("missing_information", [])

        # Status badge
        if not missing:
            st.markdown('<span class="badge-complete">All fields complete</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="badge-missing">{len(missing)} field(s) missing</span>', unsafe_allow_html=True)

        st.markdown("")

        # Part Name & Material
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="data-card">
                <div class="data-card-title">Part Name</div>
                <div class="data-card-value">{data.get('part_name', '—') or '—'}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            material_val = data.get('material', '') or '—'
            material_class = "data-card-value" if material_val != '—' else "data-card-value ops-zero"
            st.markdown(f"""
            <div class="data-card">
                <div class="data-card-title">Material</div>
                <div class="{material_class}">{material_val}</div>
            </div>
            """, unsafe_allow_html=True)

        # Dimensions
        length_val = data.get('length_mm')
        width_val = data.get('width_mm')
        thickness_val = data.get('thickness_mm')

        c1, c2, c3 = st.columns(3)
        with c1:
            display_l = f"{length_val} mm" if length_val is not None else "—"
            st.markdown(f"""
            <div class="data-card">
                <div class="data-card-title">Length</div>
                <div class="data-card-value">{display_l}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            display_w = f"{width_val} mm" if width_val is not None else "—"
            st.markdown(f"""
            <div class="data-card">
                <div class="data-card-title">Width</div>
                <div class="data-card-value">{display_w}</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            display_t = f"{thickness_val} mm" if thickness_val is not None else "—"
            st.markdown(f"""
            <div class="data-card">
                <div class="data-card-title">Thickness</div>
                <div class="data-card-value">{display_t}</div>
            </div>
            """, unsafe_allow_html=True)

        # Operations Table
        operations = data.get("operations", {})
        ops_html = """
        <div class="data-card">
            <div class="data-card-title">Manufacturing Operations</div>
            <table class="ops-table">
                <tr><th>Operation</th><th>Count</th></tr>
        """
        for op_name, op_count in operations.items():
            css_class = "ops-active" if op_count > 0 else "ops-zero"
            display_name = op_name.replace("_", " ").title()
            ops_html += f'<tr><td>{display_name}</td><td class="{css_class}">{op_count}</td></tr>'
        ops_html += "</table></div>"
        st.markdown(ops_html, unsafe_allow_html=True)

        # Surface Treatment
        surface = data.get("surface_treatment", "") or "—"
        surface_display = surface.replace("_", " ").title() if surface != "—" else "—"
        st.markdown(f"""
        <div class="data-card">
            <div class="data-card-title">Surface Treatment</div>
            <div class="data-card-value">{surface_display}</div>
        </div>
        """, unsafe_allow_html=True)

        # Quantity
        qty = data.get("quantity")
        qty_display = str(qty) if qty is not None else "—"
        st.markdown(f"""
        <div class="data-card">
            <div class="data-card-title">Quantity</div>
            <div class="data-card-value">{qty_display}</div>
        </div>
        """, unsafe_allow_html=True)

        # Missing Information Alert
        if missing:
            missing_items = "".join(
                f'<div class="missing-alert-item">• {field.replace("_", " ").title()}</div>'
                for field in missing
            )
            st.markdown(f"""
            <div class="missing-alert">
                <div class="missing-alert-title">Missing Information</div>
                {missing_items}
            </div>
            """, unsafe_allow_html=True)
        else:
            # All fields complete: Show Calculate Cost button
            st.markdown("---")
            if st.button("Calculate Cost", type="primary", use_container_width=True):
                with st.spinner("Calculating costs..."):
                    try:
                        # Call Cost Engine API
                        response = requests.post(
                            "http://localhost:8000/estimate-cost",
                            json=data,
                            headers={"Content-Type": "application/json"}
                        )
                        if response.status_code == 200:
                            st.session_state.cost_breakdown = response.json()
                            st.toast("Cost estimation successfully completed!")
                        else:
                            err_detail = response.json().get("detail", "Unknown error")
                            st.error(f"Cost Engine Error: {err_detail}")
                    except Exception as err:
                        st.error(f"Failed to connect to Cost Engine: {str(err)}. Make sure it is running on port 8000.")

        # Show Cost Estimation results if calculated
        if st.session_state.cost_breakdown:
            cb = st.session_state.cost_breakdown.get("cost_breakdown", {})
            st.markdown(f"""
            <div class="data-card" style="border: 1px solid rgba(74, 222, 128, 0.3);">
                <div class="data-card-title" style="color: #4ade80;">Cost Estimation Sheet</div>
                <table class="ops-table">
                    <tr><th>Cost Component</th><th>INR</th></tr>
                    <tr><td>Raw Material Cost</td><td>{cb.get('raw_material_cost', 0):,.2f}</td></tr>
                    <tr><td>Conversion Cost</td><td>{cb.get('conversion_cost', 0):,.2f}</td></tr>
                    <tr><td>Coating Cost</td><td>{cb.get('coating_cost', 0):,.2f}</td></tr>
                    <tr><td>Overhead (10% of Conversion)</td><td>{cb.get('overhead', 0):,.2f}</td></tr>
                    <tr><td>ICC (1% of RM)</td><td>{cb.get('icc', 0):,.2f}</td></tr>
                    <tr><td>Rejection (1% of RM+Conv)</td><td>{cb.get('rejection', 0):,.2f}</td></tr>
                    <tr><td>Profit (10% of RM+Conv)</td><td>{cb.get('profit', 0):,.2f}</td></tr>
                    <tr style="font-weight: 700; color: #4ade80; background: rgba(74, 222, 128, 0.1);">
                        <td>Total Calculated Cost</td><td>{cb.get('total_cost', 0):,.2f}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            notes = st.session_state.cost_breakdown.get("notes", [])
            if notes:
                notes_items = "".join(f'<div class="missing-alert-item">• {note}</div>' for note in notes)
                st.markdown(f"""
                <div class="missing-alert" style="border: 1px solid rgba(74, 222, 128, 0.25); background: rgba(74, 222, 128, 0.08);">
                    <div class="missing-alert-title" style="color: #4ade80;">Calculation Notes</div>
                    {notes_items}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("")

        # Export Buttons
        json_str = json.dumps(data, indent=2)

        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"{data.get('part_name', 'part').lower().replace(' ', '_')}_costing.json",
                mime="application/json",
                use_container_width=True,
            )
        with exp_col2:
            if st.button("Copy JSON", use_container_width=True):
                st.code(json_str, language="json")
                st.toast("JSON displayed below — copy it from the code block!")

    else:
        # Empty state
        st.markdown("""
        <div class="data-card" style="text-align: center; padding: 3rem 1.5rem;">
            <div style="font-size: 1.5rem; margin-bottom: 0.8rem; color: #f0a500; font-weight: 600;">No Data Yet</div>
            <div class="data-card-value" style="font-size: 1rem; color: #888;">
                Describe a manufacturing part in the chat<br>to see extracted data here.
            </div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LEFT COLUMN: Chat Interface
# ─────────────────────────────────────────────
with chat_col:
    st.markdown("### Conversation")

    # Display chat history
    chat_container = st.container(height=500)
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #666;">
                <div style="font-size: 1.2rem; margin-bottom: 0.5rem; color: #f0a500; font-weight: 600;">Ready to Analyze</div>
                <p style="font-size: 0.95rem;">
                    Describe your manufacturing part below.<br>
                    Structured data will be extracted for cost estimation.
                </p>
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

# ─────────────────────────────────────────────
# Chat Input
# ─────────────────────────────────────────────
user_input = st.chat_input("Describe your manufacturing part...", key="chat_input")

if user_input:
    # Validate API key
    api_key = st.session_state.api_key
    if not api_key or api_key == "your-api-key-here":
        st.error("OPENAI_API_KEY not found. Please add your key to the .env file and restart.")
        st.stop()

    # Add user message to display history
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.cost_breakdown = None

    # Build API messages
    if not st.session_state.api_messages:
        # First message — include system prompt
        st.session_state.api_messages.append({"role": "system", "content": SYSTEM_PROMPT})

    st.session_state.api_messages.append({"role": "user", "content": user_input})

    # Call OpenAI
    with st.spinner("Analyzing your part description..."):
        try:
            raw_response = call_openai(api_key, st.session_state.api_messages)
            parsed = parse_response(raw_response)

            # Add assistant response to histories
            st.session_state.api_messages.append({"role": "assistant", "content": raw_response})
            st.session_state.messages.append({"role": "assistant", "content": parsed["summary"]})

            # Update extracted data
            if parsed["extracted_data"]:
                st.session_state.extracted_data = parsed["extracted_data"]

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

    # Rerun to display new messages
    st.rerun()
