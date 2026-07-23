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


def _api_base_url() -> str:
    return os.getenv("API_BASE_URL", "http://127.0.0.1:8000")



def _render_session_status(session: dict) -> None:
    extracted = session.get("extracted_data", {})
    st.subheader("Session Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Part Number",
        session.get("part_number", "-")
    )
    col2.metric(
        "Material",
        extracted.get("material", "-")
    )
    col3.metric(
        "Material Rate",
        extracted.get("material_rate", "-")
    )
    col4.metric(
        "Total Cost",
        f"₹ {round(extracted.get('total_cost', 0), 2)}"
    )
    # st.write("DEBUG MISSING FIELDS:")
    # st.write(session.get("missing_fields"))

    if session.get("missing_fields"):
        st.warning(
            f"Missing Fields: {', '.join(session['missing_fields'])}"
        )
    else:
        st.success("All mandatory fields available.")

def render_cost_summary(session):
    extracted = session.get("extracted_data", {})
    st.subheader("Costing Summary")
    data = {
        "Parameter": [
            "Material",
            "Material Rate",
            "Thickness",
            "Width",
            "Length",
            "Finished Weight",
            "Scrap Weight",
            "RM Cost",
            "Conversion Cost",
            "Coating Cost",
            "Total Cost",
        ],
        "Value": [
            extracted.get("material"),
            extracted.get("material_rate"),
            extracted.get("thickness"),
            extracted.get("width"),
            extracted.get("length"),
            extracted.get("finished_weight"),
            extracted.get("scrap_weight"),
            extracted.get("raw_material_cost"),
            extracted.get("conversion_cost"),
            extracted.get("coating_cost"),
            extracted.get("total_cost"),
        ],
    }
    st.dataframe(
        pd.DataFrame(data),
        use_container_width=True
    )

# def get_session_context(
#     self,
#     employee_id,
#     part_number
# ):
#     session = self._ensure_session(
#         employee_id,
#         part_number
#     )

#     return self._serialize_session(session)

def render_cost_chart(session):
    extracted = session.get("extracted_data", {})
    rm = extracted.get("raw_material_cost", 0)
    conversion = extracted.get("conversion_cost", 0)
    coating = extracted.get("coating_cost", 0)
    df = pd.DataFrame(
        {
            "Cost Type": [
                "Raw Material",
                "Conversion",
                "Coating",
            ],
            "Cost": [
                rm,
                conversion,
                coating,
            ],
        }
    )
    fig = px.pie(
        df,
        names="Cost Type",
        values="Cost",
        title="Cost Breakdown"
    )
    st.plotly_chart(
        fig,
        use_container_width=True
    )

def main() -> None:
    st.set_page_config(page_title="Supplier Negotiation Copilot", page_icon="🤖", layout="wide")
    api_base_url = _api_base_url()

    st.title("AI-Powered Supplier Negotiation & Cost Estimation Copilot")
    st.caption("Supplier-side intake, Excel extraction, negotiated memory, and Tata Motors review handoff.")

    if "portal" not in st.session_state:
        st.session_state.portal = "Supplier"
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "authenticated_portal" not in st.session_state:
        st.session_state.authenticated_portal = None

    with st.sidebar:
        st.header("Portal Access")
        portal = st.radio("Choose portal", ["Supplier", "Tata Motors"], horizontal=False, key="portal_selector")
        if portal != st.session_state.portal:
            st.session_state.authenticated = False
            st.session_state.authenticated_portal = None
        st.session_state.portal = portal
        st.write("Use separate credentials so suppliers and Tata reviewers can access their own workspace.")

    if not st.session_state.authenticated:
        st.subheader(f"{st.session_state.portal} Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
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
                st.success(f"Logged in to {st.session_state.portal} workspace.")
            else:
                st.error("Invalid credentials.")
        return

    employee_id = st.text_input("Employee ID", placeholder="EMP1001", key="employee_id")
    part_number = st.text_input("Part Number", placeholder="123456789012", key="part_number")

    if st.button("Start / Resume Session"):
        if employee_id and part_number:
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

    if "session" not in st.session_state:
        st.session_state.session = None

    if st.session_state.portal == "Supplier" and st.session_state.session is not None:
        _render_session_status(st.session_state.session)

        uploaded_file = st.file_uploader("Upload costing Excel sheet", type=["xlsx", "xls"])
        if uploaded_file is not None and st.button("Process Excel Sheet"):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                response = requests.post(
                    f"{api_base_url}/supplier/session/upload-excel",
                    params={"employee_id": employee_id, "part_number": part_number},
                    files=files,
                    timeout=60,
                )
                response.raise_for_status()
                st.session_state.session = response.json()
                st.success("Excel assumptions extracted and merged into the session.")
            except requests.exceptions.RequestException as exc:
                st.error(f"Excel upload failed: {exc}")

        
        st.subheader("Negotiation Chat")
        for item in st.session_state.session.get("history", []):
            role = item.get("role")
            if role == "supplier":
                with st.chat_message("user"):
                    st.write(item["message"])
            else:
                with st.chat_message("assistant"):
                    st.write(item["message"])
        supplier_message = st.chat_input(
            "Enter supplier demand..."
        )

        if supplier_message:
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
                st.error(
                    f"Message processing failed: {exc}"
                )
        if st.button("Submit for Tata Review"):
            try:
                response = requests.post(
                    f"{api_base_url}/supplier/session/submit-review",
                    params={"employee_id": employee_id, "part_number": part_number},
                    timeout=45,
                )
                response.raise_for_status()
                st.session_state.session = response.json()
                st.info("The negotiation is now visible to the Tata Motors review dashboard.")
            except requests.exceptions.RequestException as exc:
                st.error(f"Submission failed: {exc}")

        with st.expander("Review Dashboard Recommendation"):
            try:
                response = requests.get(
                    f"{api_base_url}/supplier/session/review",
                    params={"employee_id": employee_id, "part_number": part_number},
                    timeout=45,
                )
                response.raise_for_status()
                dashboard = response.json()
                st.json(dashboard)
            except requests.exceptions.RequestException as exc:
                st.error(f"Review lookup failed: {exc}")
    
    elif st.session_state.portal == "Tata Motors":

        st.subheader("Tata Motors Review Dashboard")
        st.write(
            "Review supplier sessions, benchmark comparisons, "
            "and approve the final inputs."
        )

        if st.button("Load Review Dashboard"):
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

                st.success("Review dashboard loaded.")

            except requests.exceptions.RequestException as exc:
                st.error(f"Review lookup failed: {exc}")
      
        if (
            "review_dashboard" in st.session_state
            and st.session_state.review_dashboard
        ):
            
            st.write("REVIEW DASHBOARD RAW:")
            st.write(st.session_state.review_dashboard)
            dashboard = st.session_state.review_dashboard
            if not isinstance(dashboard, dict):
                st.error(f"Expected dict, got {type(dashboard)}")
                st.stop()
            session = dashboard.get("session", {})
            # render_cost_summary(session)
            # render_cost_chart(session)
            _render_session_status(session)
            benchmark = dashboard.get(
                "benchmark_comparison",
                {}
            )
            st.subheader("Benchmark Comparison")
            col1, col2, col3 = st.columns(3)
            col1.metric(
                "Supplier Rate",
                benchmark.get(
                    "supplier_material_rate",
                    0
                )
            )
            col2.metric(
                "Benchmark Rate",
                benchmark.get(
                    "internal_benchmark_rate",
                    0
                )
            )
            col3.metric(
                "Variance",
                benchmark.get(
                    "variance",
                    0
                )
            )
            recommendation = benchmark.get(
                "recommendation",
                "review"
            )
            if recommendation == "accept":
                st.success("ACCEPT")
            elif recommendation == "review":
                st.warning("REVIEW")
            else:
                st.error("NEGOTIATE FURTHER")
            
            negotiation = session.get(
                "negotiation",
                {}
            )

            st.subheader(
                "Negotiation Analysis"
            )

            c1,c2,c3 = st.columns(3)

            c1.metric(
                "Supplier Quote",
                negotiation.get(
                    "supplier_quote",
                    0
                )
            )

            c2.metric(
                "Expected Cost",
                negotiation.get(
                    "predicted_cost",
                    0
                )
            )

            c3.metric(
                "Variance %",
                negotiation.get(
                    "variance",
                    0
                )
            )

            st.info(
                f"AI Recommendation: "
                f"{negotiation.get('ai_recommendation')}"
            )

            st.success(
                f"Suggested Counter Offer: ₹"
                f"{negotiation.get('counter_offer')}"
            )
            
            if session.get("status") == "submitted_for_review":
                st.subheader("Buyer Actions")
                col1, col2 = st.columns(2)
                # APPROVE
                with col1:
                    if st.button("✅ Approve"):
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
                            st.success("Offer Approved")
                            # Reload full review dashboard after approval
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
                # REJECT
                with col2:
                    reject_reason = st.selectbox(
                        "Rejection Reason",
                        [
                            "Cost Above Benchmark",
                            "Material Rate Too High",
                            "Conversion Cost Too High",
                            "Commercial Terms Not Acceptable",
                            "Incomplete Cost Sheet",
                            "Other"
                        ]
                    )
                    if st.button("❌ Reject"):
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
                            # Reload full review dashboard after rejection
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



if __name__ == "__main__":
    main()
