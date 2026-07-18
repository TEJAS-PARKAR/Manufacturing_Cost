import os
from pathlib import Path

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import requests
# pyrefly: ignore [missing-import]
import streamlit as st


def _api_base_url() -> str:
    return os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def _render_session_status(session: dict) -> None:
    st.subheader("Negotiation Session")
    st.json(session)
    if session.get("missing_fields"):
        st.warning(f"Missing required details: {', '.join(session['missing_fields'])}")
    else:
        st.success("Mandatory fields are present. The session can now move to review.")


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

        st.subheader("Continue the negotiation")
        supplier_message = st.text_area("Supplier message", height=120)
        if st.button("Send Message") and supplier_message:
            try:
                response = requests.post(
                    f"{api_base_url}/supplier/session/message",
                    json={
                        "employee_id": employee_id,
                        "part_number": part_number,
                        "message": supplier_message,
                    },
                    timeout=45,
                )
                response.raise_for_status()
                st.session_state.session = response.json()
                st.success("Supplier context updated and the memory summary refreshed.")
            except requests.exceptions.RequestException as exc:
                st.error(f"Message processing failed: {exc}")

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
        st.write("Review supplier sessions, benchmark comparisons, and approve the final inputs.")
        if st.button("Load Review Dashboard"):
            try:
                response = requests.get(
                    f"{api_base_url}/supplier/session/review",
                    params={"employee_id": employee_id, "part_number": part_number},
                    timeout=45,
                )
                response.raise_for_status()
                st.session_state.review_dashboard = response.json()
                st.success("Review dashboard loaded.")
            except requests.exceptions.RequestException as exc:
                st.error(f"Review lookup failed: {exc}")

        if "review_dashboard" in st.session_state:
            st.json(st.session_state.review_dashboard)

        if st.button("Approve Current Inputs"):
            try:
                response = requests.post(
                    f"{api_base_url}/supplier/session/approve",
                    params={"employee_id": employee_id, "part_number": part_number},
                    timeout=45,
                )
                response.raise_for_status()
                st.success("Approved cost inputs updated for the session.")
            except requests.exceptions.RequestException as exc:
                st.error(f"Approval failed: {exc}")


if __name__ == "__main__":
    main()
