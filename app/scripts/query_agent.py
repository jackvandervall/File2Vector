import streamlit as st
import requests

# Replace with your actual webhook URL from n8n
N8N_WEBHOOK_URL = "https://app.n8n.cloud/webhook/dashboard"

def trigger_n8n_workflow(payload):
    """Send data to n8n workflow"""
    response = requests.post(N8N_WEBHOOK_URL, json=payload)
    return response.json()

def show():
    st.title("Run n8n Workflow")

    # Example form input
    user_input = st.text_input("Provide input")

    if st.button("Run Workflow"):
        if user_input:
            payload = {"input_data": user_input}  # Send data to n8n
            result = trigger_n8n_workflow(payload)
            st.success(f"✅ Workflow Triggered! Response: {result}")
        else:
            st.error("⚠️ Please enter some data before running the workflow.")
