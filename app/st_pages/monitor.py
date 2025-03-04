import streamlit as st
import os
import pandas as pd
from scripts.utils import (
    load_custom_settings, create_supabase_client, check_new_files,
    extract_text_from_pdf, extract_tables_from_pdf, extract_text_from_docx,
    upload_to_supabase
)
from streamlit_extras.let_it_rain import rain

rain_length = 0

rain(
    emoji="🎉",
    font_size=20,
    falling_speed=3,
    animation_length=rain_length
)

# ✅ Set base directory to ./data
BASE_DIR = os.path.join(os.getcwd(), "..", "data")

# ✅ Ensure the directory exists
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# ✅ Store known files in session state
if "known_files" not in st.session_state:
    st.session_state.known_files = set()

# ✅ Function to process and upload a file
def upload_file(file_path, supabase, table_name, expected_dim, model, cohere_key, openai_key, CHUNK_SIZE):
    file_name = os.path.basename(file_path)
    metadata = {"filename": file_name}
    file_extension = file_name.split(".")[-1]

    # ✅ Streamlit progress bar
    progress_text = st.empty()
    progress_bar = st.progress(0)

    with open(file_path, "rb") as uploaded_file:
        if file_extension == "pdf":
            text = extract_text_from_pdf(uploaded_file)
            tables = extract_tables_from_pdf(uploaded_file)

            if text:
                upload_to_supabase(supabase, table_name, text, metadata, expected_dim, model, cohere_key, openai_key, CHUNK_SIZE)
                progress_text.text("Uploading extracted text from PDF...")
                progress_bar.progress(50)

            if tables:
                total_tables = len(tables)
                for i, table in enumerate(tables):
                    upload_to_supabase(supabase, table_name, str(table.to_dict()), metadata, expected_dim, model, cohere_key, openai_key, CHUNK_SIZE)
                    progress_text.text(f"Uploading table {i+1}/{total_tables}...")
                    progress_bar.progress(50 + int(50 * (i + 1) / total_tables))

        elif file_extension == "docx":
            text = extract_text_from_docx(uploaded_file)
            if text:
                upload_to_supabase(supabase, table_name, text, metadata, expected_dim, model, cohere_key, openai_key, CHUNK_SIZE)
                progress_text.text("Uploading extracted text from Word document...")
                progress_bar.progress(100)

        elif file_extension in ["csv", "xlsx"]:
            df = pd.read_csv(uploaded_file) if file_extension == "csv" else pd.read_excel(uploaded_file)
            total_rows = len(df)

            for i, (_, row) in enumerate(df.iterrows()):
                upload_to_supabase(supabase, table_name, str(row.to_dict()), row.to_dict(), expected_dim, model, cohere_key, openai_key, CHUNK_SIZE)
                progress_text.text(f"Uploading row {i+1}/{total_rows}...")
                progress_bar.progress(int((i + 1) / total_rows * 100))

    progress_text.text("Upload complete!")
    progress_bar.progress(100)
    st.success(f"✅ {file_name} uploaded successfully!")


# ✅ Main function with proper button handling
def show():
    st.title("Check `/data` for New Files")
    st.write("Press the refresh button to detect new files and store them individually or in bulk.")

    # ✅ Credentials Input
    custom_settings = load_custom_settings() if st.sidebar.checkbox("Custom Settings") else {}

    SUPABASE_URL = st.sidebar.text_input("Supabase URL", custom_settings.get("SUPABASE_URL", "https://your-supabase-url.supabase.co"))
    SUPABASE_KEY = st.sidebar.text_input("Supabase Key", custom_settings.get("SUPABASE_KEY", "your-service-role-key"), type="password")
    TABLE_NAME = st.sidebar.text_input("Table Name", custom_settings.get("TABLE_NAME", "your_vector_table"))
    EXPECTED_DIM = st.select_slider("Expected Dimensions", options=[384, 786, 1024, 4096], value=int(custom_settings.get("EXPECTED_DIM", 1024)))
    CHUNK_SIZE = st.number_input("Chunk Size", min_value=100, max_value=1000, value=int(custom_settings.get("CHUNK_SIZE", 300)), step=50)

    embedding_model = st.radio("Embedding Model", ["OpenAI", "Cohere"])
    if embedding_model == "OpenAI":
        OPENAI_API_KEY = st.sidebar.text_input("OpenAI API Key", custom_settings.get("OPENAI_API_KEY", "your-openai-api-key"), type="password")
        COHERE_API_KEY = None
    else:
        COHERE_API_KEY = st.sidebar.text_input("Cohere API Key", custom_settings.get("COHERE_API_KEY", "your-cohere-api-key"), type="password")
        OPENAI_API_KEY = None

    if SUPABASE_KEY == "your-service-role-key":
        st.error("⚠️ Please provide your dataset and API credentials to start your upload!")
        return

    # ✅ Initialize Supabase Client
    supabase = create_supabase_client(SUPABASE_URL, SUPABASE_KEY)

    # ✅ Refresh button to check for new files
    if st.button("Refresh"):
        new_files, st.session_state.known_files = check_new_files(BASE_DIR, st.session_state.known_files)

        if new_files:
            st.session_state.new_files = new_files  # Store detected new files
            st.success("📂 New files detected!")
        else:
            st.session_state.new_files = []
            st.info("✅ No new files detected.")

    # ✅ Load new files from session state
    new_files = st.session_state.get("new_files", [])

    if new_files:
        st.write("### **Upload Individual Files**")

        for file in new_files:
            file_path = os.path.join(BASE_DIR, file)

            # ✅ Track button states to prevent rerun issues
            if st.button(f"Upload {file}", key=f"upload_{file}"):
                upload_file(file_path, supabase, TABLE_NAME, EXPECTED_DIM, embedding_model, COHERE_API_KEY, OPENAI_API_KEY, CHUNK_SIZE)
                st.session_state.new_files.remove(file)  # Remove uploaded file from list
                st.experimental_rerun()  # Refresh UI

        # ✅ Upload all new files in bulk
        if st.button("Upload All New Files"):
            for file in new_files:
                file_path = os.path.join(BASE_DIR, file)
                upload_file(file_path, supabase, TABLE_NAME, EXPECTED_DIM, embedding_model, COHERE_API_KEY, OPENAI_API_KEY, CHUNK_SIZE)

            st.session_state.new_files = []  # Clear new files after upload
            st.success(f"✅ All {len(new_files)} files uploaded successfully!")
            st.experimental_rerun()  # Refresh UI
