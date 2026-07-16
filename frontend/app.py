import os
import requests
import streamlit as st


def main() -> None:
    st.set_page_config(page_title="Manufacturing Cost Copilot", page_icon="🤖", layout="wide")

    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.title("Manufacturing Cost Copilot")
    st.caption("Describe the part in plain English and let the app extract the details, train a lightweight XGBoost-style model, and estimate the cost.")

    with st.sidebar:
        st.header("Example prompts")
        st.write("Try: \"I need 100 mounting brackets, 200 by 100 by 50 mm, made from CRCA steel, laser cut and bent 3 times.\"")
        st.write("Try: \"Produce 50 parts, 120 by 80 by 10 mm, aluminum, drilling 4 holes and painting.\"")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Describe the part, quantity, dimensions, material, and processes")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        try:
            response = requests.post(f"{API_BASE_URL}/chat-cost", json={"message": prompt}, timeout=45)
            response.raise_for_status()
            data = response.json()

            extracted = data["extracted_data"]
            prediction = data["prediction"]
            with st.chat_message("assistant"):
                st.success("Request parsed successfully.")
                st.subheader("Extracted details")
                st.json(extracted)
                st.subheader("Estimated cost")
                st.metric("Predicted Cost", f"₹{prediction['predicted_cost']:.2f}")
                st.caption(f"Model: {prediction['model']} | Deterministic reference: ₹{prediction['deterministic_reference']:.2f}")
                with st.expander("Raw response"):
                    st.json(data)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"Estimated cost: ₹{prediction['predicted_cost']:.2f} based on the extracted details.",
                }
            )
        except requests.exceptions.RequestException as exc:
            with st.chat_message("assistant"):
                st.error(f"Backend request failed: {exc}")
            st.session_state.messages.append({"role": "assistant", "content": "The request could not be processed."})


if __name__ == "__main__":
    main()
