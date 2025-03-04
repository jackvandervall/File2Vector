import streamlit as st
import pandas as pd
import numpy as np
import pdfplumber
import pymupdf  # PyMuPDF for PDFs
import docx
import cohere
import openai
from nltk.tokenize import sent_tokenize
from supabase import create_client
from scripts.utils import (
    load_custom_settings, create_supabase_client, check_new_files,
    split_text, extract_text_from_pdf, extract_tables_from_pdf, extract_text_from_docx,
    generate_embedding, clean_metadata, upload_to_supabase
)

# Streamlit UI Setup
def show():
    st.title("Upload File")
    st.write("This tool allows users to upload and store various file types into their own Supabase vector database. It extracts text from DOCX, PDFs, and structured data from spreadsheets, generating embeddings while storing them efficiently.")

    # Load custom settings if button is pressed
    custom_settings = load_custom_settings() if st.sidebar.checkbox("Custom Settings") else {}
    
    # User input for API credentials
    SUPABASE_URL = st.sidebar.text_input("Supabase URL", custom_settings.get("SUPABASE_URL", "https://your-supabase-url.supabase.co"))
    SUPABASE_KEY = st.sidebar.text_input("Supabase Key", custom_settings.get("SUPABASE_KEY", "your-service-role-key"), type="password")
    TABLE_NAME = st.sidebar.text_input("Table Name", custom_settings.get("TABLE_NAME", "your_vector_table"))
    EXPECTED_DIM = st.select_slider("Expected Dimensions", options=[384, 786, 1024, 4096], value=int(custom_settings.get("EXPECTED_DIM", 1024)))
    
    # ✅ Embedding Model Selection
    embedding_model = st.radio("Embedding Model", ["OpenAI", "Cohere"])
    
    OPENAI_API_KEY = st.sidebar.text_input("OpenAI API Key", custom_settings.get("OPENAI_API_KEY", "your-openai-api-key"), type="password")
    COHERE_API_KEY = st.sidebar.text_input("Cohere API Key", custom_settings.get("COHERE_API_KEY", "your-cohere-api-key"), type="password")

    # Ensure Supabase API Key is provided
    if SUPABASE_KEY == "your-service-role-key":
        st.write("⚠️ Please provide your dataset and API credentials to start your upload!")
        st.stop()
    
    # Initialize Supabase Client
    supabase = create_supabase_client(SUPABASE_URL, SUPABASE_KEY)
    
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "pdf", "docx", "xlsx"])

    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1]
        metadata = {"filename": uploaded_file.name}
        
        if file_type == "pdf":
            text = extract_text_from_pdf(uploaded_file)
            st.write("Extracted text from PDF:", text[:500])
            if st.button("Upload to Supabase"):
                upload_to_supabase(supabase, TABLE_NAME, text, metadata, EXPECTED_DIM, embedding_model, COHERE_API_KEY, OPENAI_API_KEY)
            
            tables = extract_tables_from_pdf(uploaded_file)
            if tables:
                st.write("Extracted tables from PDF:")
                for table in tables:
                    st.dataframe(table)
        
        elif file_type == "docx":
            text = extract_text_from_docx(uploaded_file)
            st.write("Extracted text from Word document:", text[:500])
            if st.button("Upload to Supabase"):
                upload_to_supabase(supabase, TABLE_NAME, text, metadata, EXPECTED_DIM, embedding_model, COHERE_API_KEY, OPENAI_API_KEY)
        
        elif file_type == "csv":
            df = pd.read_csv(uploaded_file)
            st.write("Preview of uploaded CSV:")
            st.dataframe(df.head())
            if st.button("Upload to Supabase"):
                for _, row in df.iterrows():
                    upload_to_supabase(supabase, TABLE_NAME, str(row.to_dict()), row.to_dict(), EXPECTED_DIM, embedding_model, COHERE_API_KEY, OPENAI_API_KEY)
                st.success("CSV uploaded successfully!")
        
        elif file_type == "xlsx":
            df = pd.read_excel(uploaded_file)
            st.write("Preview of uploaded Excel file:")
            st.dataframe(df.head())
            if st.button("Upload to Supabase"):
                for _, row in df.iterrows():
                    upload_to_supabase(supabase, TABLE_NAME, str(row.to_dict()), row.to_dict(), EXPECTED_DIM, embedding_model, COHERE_API_KEY, OPENAI_API_KEY)
                st.success("Excel uploaded successfully!")
