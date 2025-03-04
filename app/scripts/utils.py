import os
import json
import pandas as pd
import numpy as np
import pdfplumber
import pymupdf  # PyMuPDF for PDFs
import docx
import cohere
import openai
from nltk.tokenize import sent_tokenize
import streamlit as st
from supabase import create_client

# ✅ Load custom settings
def load_custom_settings(): 
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "custom_settings.json")
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("⚠️ Custom settings file not found.")
        return {}
    except json.JSONDecodeError:
        st.error("⚠️ Error reading custom settings file.")
        return {}

# ✅ Supabase Client Initialization
def create_supabase_client(url, key):
    return create_client(url, key)

# ✅ Function to check for new files in a folder
def check_new_files(folder_path, known_files):
    current_files = set(os.listdir(folder_path))
    new_files = current_files - known_files
    return new_files, current_files

# ✅ Function to split text into chunks
def split_text(text, chunk_size=300):
    sentences = sent_tokenize(text)
    chunks, temp_chunk = [], ""
    for sentence in sentences:
        if len(temp_chunk) + len(sentence) <= chunk_size:
            temp_chunk += " " + sentence
        else:
            chunks.append(temp_chunk.strip())
            temp_chunk = sentence
    if temp_chunk:
        chunks.append(temp_chunk.strip())
    return chunks

# ✅ Function to extract text from PDFs
def extract_text_from_pdf(uploaded_file):
    text = ""
    doc = pymupdf.open(stream=uploaded_file.read(), filetype="pdf")
    for page in doc:
        text += page.get_text("text") + "\n"
    return text.strip()

# ✅ Function to extract tables from PDFs
def extract_tables_from_pdf(uploaded_file):
    tables = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            extracted_table = page.extract_table()
            if extracted_table:
                df = pd.DataFrame(extracted_table[1:], columns=extracted_table[0])
                tables.append(df)
    return tables

# ✅ Function to extract text from DOCX files
def extract_text_from_docx(uploaded_file):
    doc = docx.Document(uploaded_file)
    return "\n".join([para.text for para in doc.paragraphs]).strip()

# ✅ Function to generate embeddings
def generate_embedding(text, model, cohere_key, openai_key):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("❌ Error: Input text for embedding is empty or not a valid string.")

    if model == "Cohere":
        co = cohere.Client(cohere_key)
        response = co.embed(texts=[text], model="embed-english-v3.0", input_type="search_document")
        return response.embeddings[0]
    
    else:  # OpenAI
        openai_client = openai.OpenAI(api_key=openai_key)
        
        # Ensure text is within OpenAI's token limit
        max_token_limit = 8192  # Adjust based on OpenAI model constraints
        truncated_text = text[:max_token_limit]

        response = openai_client.embeddings.create(input=truncated_text, model="text-embedding-3-small")
        return response.data[0].embedding

# ✅ Function to clean metadata before storing in Supabase
def clean_metadata(metadata):
    if not isinstance(metadata, dict):
        return {}

    cleaned_metadata = {}
    for key, value in metadata.items():
        if isinstance(value, pd.Timestamp):
            cleaned_metadata[key] = value.isoformat()  # Convert to ISO string
        elif isinstance(value, dict):
            cleaned_metadata[key] = clean_metadata(value)  # Recursively clean
        elif isinstance(value, list):
            cleaned_metadata[key] = [clean_metadata(item) if isinstance(item, dict) else str(item) for item in value]
        else:
            cleaned_metadata[key] = str(value)  # Convert everything else to string

    return cleaned_metadata


# ✅ Function to upload extracted text to Supabase
def upload_to_supabase(supabase, table_name, content, metadata, expected_dim, model, cohere_key, openai_key, chunk_size):
    text_chunks = split_text(content, chunk_size=chunk_size)

    if not text_chunks:
        st.error("⚠️ No valid text extracted for embedding. Skipping upload.")
        return

    metadata = clean_metadata(metadata)  # Ensure metadata is JSON serializable
    progress_bar = st.progress(0)

    for i, chunk in enumerate(text_chunks):
        if not chunk.strip():  # Skip empty chunks
            continue

        try:
            vector = generate_embedding(chunk, model, cohere_key, openai_key)

            # Ensure vector matches expected dimension
            if len(vector) > expected_dim:
                vector = vector[:expected_dim]
            elif len(vector) < expected_dim:
                vector = np.pad(vector, (0, expected_dim - len(vector)), 'constant').tolist()

            # Upload to Supabase
            supabase.table(table_name).insert({
                "content": chunk,
                "embedding": vector,
                "metadata": metadata  # Ensure cleaned metadata is used
            }).execute()
        except ValueError as e:
            st.error(f"⚠️ Skipping invalid text chunk: {e}")
            continue

        progress_bar.progress((i + 1) / len(text_chunks))

    st.success(f"✅ Uploaded {len(text_chunks)} chunks successfully!")