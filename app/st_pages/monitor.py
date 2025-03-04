import streamlit as st
import os
import pandas as pd
from scripts.utils import (
    load_custom_settings, create_supabase_client, check_new_files,
    extract_text_from_pdf, extract_tables_from_pdf, extract_text_from_docx,
    upload_to_supabase
)

# ✅ Set base directory to `./data_storage`
BASE_DIR = os.path.join(os.getcwd(), "..","data", "data_storage")

# ✅ Ensure the directory exists
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

def show():
    st.title("Check `data_storage` for New Files")
    st.write("This tool allows users to upload and store various file types into their own Supabase vector database in bulk from a given folder.")

    # ✅ Check for new files in `data_storage/`
    if st.button("Refresh"):
        known_files = set()
        new_files, known_files = check_new_files(BASE_DIR, known_files)

        if new_files:
            st.write("📂 **New files detected:**")
            for file in new_files:
                st.write(f"- {file}")
        else:
            st.write("✅ No new files detected.")

    # ✅ Sidebar for API Credentials
    custom_settings = load_custom_settings() if st.sidebar.checkbox("Custom Settings") else {}

    SUPABASE_URL = st.sidebar.text_input("Supabase URL", custom_settings.get("SUPABASE_URL", "https://your-supabase-url.supabase.co"))
    SUPABASE_KEY = st.sidebar.text_input("Supabase Key", custom_settings.get("SUPABASE_KEY", "your-service-role-key"), type="password")
    TABLE_NAME = st.sidebar.text_input("Table Name", custom_settings.get("TABLE_NAME", "your_vector_table"))
    EXPECTED_DIM = st.select_slider("Expected Dimensions", options=[384, 786, 1024, 4096], value=int(custom_settings.get("EXPECTED_DIM", 1024)))

    # ✅ Embedding Model Selection
    embedding_model = st.radio("Embedding Model", ["OpenAI", "Cohere"])
    
    OPENAI_API_KEY = st.sidebar.text_input("OpenAI API Key", custom_settings.get("OPENAI_API_KEY", "your-openai-api-key"), type="password")
    COHERE_API_KEY = st.sidebar.text_input("Cohere API Key", custom_settings.get("COHERE_API_KEY", "your-cohere-api-key"), type="password")

    if SUPABASE_KEY == "your-service-role-key":
        st.error("⚠️ Please provide your dataset and API credentials to start your upload!")
        st.stop()

    # ✅ Initialize Supabase Client
    supabase = create_supabase_client(SUPABASE_URL, SUPABASE_KEY)

    # ✅ Buttons to upload files individually or all at once
    uploaded_files = []
    
    if new_files:
        st.write("### **Upload Individual Files**")
        for file in new_files:
            file_path = os.path.join(BASE_DIR, file)
            if st.button(f"Upload {file}"):
                upload_file(file_path, supabase, TABLE_NAME, EXPECTED_DIM, embedding_model, COHERE_API_KEY, OPENAI_API_KEY)
                st.success(f"✅ {file} uploaded successfully!")

            uploaded_files.append(file_path)

        # ✅ Button to upload all new files at once
        if st.button("Upload All New Files"):
            for file_path in uploaded_files:
                upload_file(file_path, supabase, TABLE_NAME, EXPECTED_DIM, embedding_model, COHERE_API_KEY, OPENAI_API_KEY)
            st.success(f"✅ All {len(uploaded_files)} files uploaded successfully!")

# ✅ Function to process and upload a file
def upload_file(file_path, supabase, table_name, expected_dim, model, cohere_key, openai_key):
    file_name = os.path.basename(file_path)
    metadata = {"filename": file_name}
    file_extension = file_name.split(".")[-1]

    with open(file_path, "rb") as uploaded_file:
        if file_extension == "pdf":
            text = extract_text_from_pdf(uploaded_file)
            tables = extract_tables_from_pdf(uploaded_file)

            if text:
                upload_to_supabase(supabase, table_name, text, metadata, expected_dim, model, cohere_key, openai_key)

            if tables:
                for table in tables:
                    upload_to_supabase(supabase, table_name, str(table.to_dict()), metadata, expected_dim, model, cohere_key, openai_key)

        elif file_extension == "docx":
            text = extract_text_from_docx(uploaded_file)
            if text:
                upload_to_supabase(supabase, table_name, text, metadata, expected_dim, model, cohere_key, openai_key)

        elif file_extension == "csv":
            df = pd.read_csv(uploaded_file)
            for _, row in df.iterrows():
                upload_to_supabase(supabase, table_name, str(row.to_dict()), row.to_dict(), expected_dim, model, cohere_key, openai_key)

        elif file_extension == "xlsx":
            df = pd.read_excel(uploaded_file)
            for _, row in df.iterrows():
                upload_to_supabase(supabase, table_name, str(row.to_dict()), row.to_dict(), expected_dim, model, cohere_key, openai_key)