import os
import requests
import streamlit as st


def main() -> None:
    st.set_page_config(page_title="Manufacturing Cost Estimator", page_icon="🏭", layout="wide")

    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

    st.markdown(
        """
        <style>
        .main {padding-top: 1rem;}
        .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > select {
            border-radius: 8px;
        }
        div[data-testid="stExpander"] {border: 1px solid #d0d7de; border-radius: 8px;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Manufacturing Cost Estimation")
    st.caption("Structured, deterministic costing for industrial parts.")

    with st.sidebar:
        st.header("Input Guide")
        st.write("Enter part dimensions, material data, and selected manufacturing processes.")

    with st.form("cost_form"):
        st.subheader("Part Information")
        col1, col2 = st.columns(2)
        with col1:
            part_name = st.text_input("Part Name", value="", placeholder="e.g. Mounting Bracket (optional)")
        with col2:
            quantity = st.number_input("Quantity", min_value=1, value=100, step=1)

        st.subheader("Dimensions")
        col3, col4, col5, col6 = st.columns(4)
        with col3:
            length = st.number_input("Length (mm)", min_value=1.0, value=200.0, step=1.0)
        with col4:
            width = st.number_input("Width (mm)", min_value=1.0, value=100.0, step=1.0)
        with col5:
            height = st.number_input("Height (mm)", min_value=1.0, value=50.0, step=1.0)
        with col6:
            thickness = st.number_input("Thickness (mm)", min_value=0.1, value=2.0, step=0.1)

        st.subheader("Material Information")
        material_type = st.text_input("Material Type", value="", placeholder="Optional")
        material_density = st.number_input("Material Density (kg/m³)", min_value=1.0, value=7850.0, step=10.0)
        material_rate = st.number_input("Material Rate (₹/kg)", min_value=1.0, value=65.0, step=1.0)

        st.subheader("Process Information")
        available_processes = [
            "laser_cutting",
            "bending",
            "welding",
            "drilling",
            "machining",
            "powder_coating",
            "painting",
            "assembly",
        ]
        selected_processes = st.multiselect("Select Processes", available_processes, default=["laser_cutting", "bending"])

        process_fields = []
        for process_name in selected_processes:
            st.markdown(f"### {process_name.replace('_', ' ').title()}")
            quantity_value = st.number_input(f"{process_name} quantity", min_value=1, value=1, key=f"qty_{process_name}")
            payload = {"name": process_name, "quantity": int(quantity_value)}
            if process_name == "bending":
                payload["bends"] = st.number_input("Number of bends", min_value=0, value=2, key=f"bends_{process_name}")
            if process_name == "drilling":
                payload["holes"] = st.number_input("Number of holes", min_value=0, value=4, key=f"holes_{process_name}")
            if process_name == "machining":
                payload["machining_hours"] = st.number_input("Machining hours", min_value=0.0, value=1.0, step=0.1, key=f"mach_hours_{process_name}")
            if process_name in {"powder_coating", "painting"}:
                payload["coating_thickness_um"] = st.number_input("Coating thickness (µm)", min_value=0.0, value=40.0, step=1.0, key=f"coating_{process_name}")
            process_fields.append(payload)

        submitted = st.form_submit_button("Estimate Cost", use_container_width=True, type="primary")

    if submitted:
        payload = {
            "part_name": part_name.strip() or "Unnamed Part",
            "quantity": int(quantity),
            "length": float(length),
            "width": float(width),
            "height": float(height),
            "thickness": float(thickness),
            "material": {
                "type": material_type.strip() or "UNKNOWN",
                "density": float(material_density),
                "rate_per_kg": float(material_rate),
            },
            "processes": process_fields,
        }
        try:
            response = requests.post(f"{API_BASE_URL}/estimate-cost", json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            st.success("Cost estimate generated successfully.")
            st.subheader("Estimated Cost")
            breakdown = data["cost_breakdown"]
            st.metric("Raw Material Cost", f"₹{breakdown['raw_material_cost']:.2f}")
            st.metric("Process Cost", f"₹{breakdown['process_cost']:.2f}")
            st.metric("Overhead Cost", f"₹{breakdown['overhead_cost']:.2f}")
            st.metric("Total Manufacturing Cost", f"₹{breakdown['total_manufacturing_cost']:.2f}")
            st.metric("Cost per Piece", f"₹{breakdown['cost_per_piece']:.2f}")
            with st.expander("Detailed Breakdown"):
                st.json(data)
        except requests.exceptions.RequestException as exc:
            st.error(f"Backend request failed: {exc}")


if __name__ == "__main__":
    main()
