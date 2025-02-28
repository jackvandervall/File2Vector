import streamlit as st
import pandas as pd
import nltk
import textwrap
import pymupdf  # PyMuPDF for PDFs
import docx  # For Word documents
import numpy as np
import pdfplumber  # For extracting tables from PDFs
from nltk.tokenize import sent_tokenize
from supabase import create_client
import cohere
import openai
import json

nltk.download('punkt')

# Function to load custom settings from a file
def load_custom_settings():
    try:
        with open("custom_settings.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("⚠️ Custom settings file not found.")
        return {}
    except json.JSONDecodeError:
        st.error("⚠️ Error reading custom settings file.")
        return {}
    
# Streamlit Sidebar for API and Table Configuration
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Upload", "Supabase", "Contact"])

if page == "Home":
    st.title("File2Vector")
    st.write("Hi, welcome to the file upload hub for Vector data storage.")
    st.write("---")
    st.write("1. Go to https://supabase.com/: Project Settings > Data API and paste your Project URL + service_role into the Upload tab.")
    st.write("2. Upload the files you want to convert to embeddings.")
    st.write("3. Provide feedback via the contact page.")

if page == "Upload":
    
    # UI Format
    st.title("Upload File")
    st.write("This Supabase Vector Uploader allows users to upload and store various file types into their own Supabase vector database. It extracts text from documents, tables from PDFs, and structured data from spreadsheets, generating embeddings using Cohere and storing them efficiently.")
    st.write("***")
    st.write("**Embedding Model Settings**")
    st.sidebar.write("***")
    st.sidebar.write("**Credentials**")

    # Load custom settings if button is pressed
    if st.sidebar.checkbox("Custom Settings"):
        custom_settings = load_custom_settings()
    else:
        custom_settings = {}    
    
    # User input for API credential
    SUPABASE_URL = st.sidebar.text_input("Supabase URL", custom_settings.get("SUPABASE_URL", "https://your-supabase-url.supabase.co"))
    SUPABASE_KEY = st.sidebar.text_input("Supabase Key", custom_settings.get("SUPABASE_KEY", "your-service-role-key"), type="password")
    TABLE_NAME = st.sidebar.text_input("Table Name", custom_settings.get("TABLE_NAME", "your_vector_table"))
    
    # Select slider with dynamic default value
    default_expected_dim = custom_settings.get("EXPECTED_DIM", 1024)
    EXPECTED_DIM = st.select_slider("Expected Dimensions", options=[384, 786, 1024, 4096], value=int(default_expected_dim))
    
    # Embedding Model Selection
    embedding_model = st.radio("Choose Embedding Model:", ["Cohere", "OpenAI"])

    if embedding_model == "OpenAI":
        OPENAI_API_KEY = st.sidebar.text_input("Cohere API Key", custom_settings.get("OPENAI_API_KEY", "your-openai-api-key"), type="password")
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    else:
        COHERE_API_KEY = st.sidebar.text_input("OpenAI API Key", custom_settings.get("COHERE_API_KEY", "your-cohere-api-key"), type="password")
        co = cohere.Client(COHERE_API_KEY)

    # Ensure Supabase API Key is provided
    if SUPABASE_KEY == "your-service-role-key":
        st.write("⚠️ Please provide your dataset and API credentials to start your upload!")
        st.stop()

    # Initialize Supabase and API Clients
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    def split_text(text, chunk_size=300):
        """Splits text into smaller chunks while preserving sentence structure."""
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

    def extract_text_from_pdf(uploaded_file):
        """Extracts text from a PDF file using PyMuPDF."""
        text = ""
        doc = pymupdf.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            text += page.get_text("text") + "\n"
        return text.strip()

    def extract_tables_from_pdf(uploaded_file):
        """Extracts tables from a PDF using pdfplumber."""
        tables = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                extracted_table = page.extract_table()
                if extracted_table:
                    df = pd.DataFrame(extracted_table[1:], columns=extracted_table[0])
                    tables.append(df)
        return tables

    def extract_text_from_docx(uploaded_file):
        """Extracts text from a Word document."""
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs]).strip()

    def generate_embedding(text):
        """Generate an embedding vector from text using the selected model."""
        if embedding_model == "Cohere":
            response = co.embed(texts=[text], model="embed-english-v3.0", input_type="search_document")
            vector = response.embeddings[0]
        else:  # OpenAI
            response = openai_client.embeddings.create(input=[text], model="text-embedding-3-small")
            vector = response.data[0].embedding
        
        expected_dim = EXPECTED_DIM
        if len(vector) > expected_dim:
            vector = vector[:expected_dim]
        elif len(vector) < expected_dim:
            vector = np.pad(vector, (0, expected_dim - len(vector)), 'constant').tolist()
        return vector
    
    def clean_metadata(metadata):
        """Convert non-serializable objects like Timestamps to JSON serializable format"""
        for key, value in metadata.items():
            if isinstance(value, pd.Timestamp):
                metadata[key] = value.isoformat()  # Convert timestamp to string
            elif isinstance(value, dict):
                metadata[key] = clean_metadata(value)  # Recursively clean nested dictionaries
        return metadata
    
    def upload_to_supabase(content, metadata):
        """Uploads text chunks to Supabase and shows progress."""
        text_chunks = split_text(content, chunk_size=300)
        progress_bar = st.progress(0)
        for i, chunk in enumerate(text_chunks):
            vector = generate_embedding(chunk)
            supabase.table(TABLE_NAME).insert({
                "content": chunk,
                "embedding": vector,
                "metadata": metadata
            }).execute()
            progress_bar.progress((i + 1) / len(text_chunks))
        st.success(f"✅ Uploaded {len(text_chunks)} chunks successfully!")

    uploaded_file = st.file_uploader("Choose a file", type=["csv", "pdf", "docx", "xlsx"])

    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1]
        metadata = {"filename": uploaded_file.name}

        if file_type == "pdf":
            text = extract_text_from_pdf(uploaded_file)
            st.write("Extracted text from PDF:", text[:500])
            if st.button("Upload to Supabase"):
                upload_to_supabase(text, metadata)

            tables = extract_tables_from_pdf(uploaded_file)
            if tables:
                st.write("Extracted tables from PDF:")
                for table in tables:
                    st.dataframe(table)

        elif file_type == "docx":
            text = extract_text_from_docx(uploaded_file)
            st.write("Extracted text from Word document:", text[:500])
            if st.button("Upload to Supabase"):
                upload_to_supabase(text, metadata)

        elif file_type == "csv":
            df = pd.read_csv(uploaded_file)
            st.write("Preview of uploaded CSV:")
            st.dataframe(df.head())
            if st.button("Upload to Supabase"):
                for _, row in df.iterrows():
                    upload_to_supabase(str(row.to_dict()), row.to_dict())
                st.success("CSV uploaded successfully!")

        elif file_type == "xlsx":
            df = pd.read_excel(uploaded_file)
            st.write("Preview of uploaded Excel file:")
            st.dataframe(df.head())
            if st.button("Upload to Supabase"):
                for _, row in df.iterrows():
                    upload_to_supabase(str(row.to_dict()), row.to_dict())
                st.success("Excel uploaded successfully!")

if page == "Supabase":
    st.sidebar.write("***")
    st.sidebar.write("**Credentials**")
    
    # Load custom settings if button is pressed
    if st.sidebar.checkbox("Custom Settings"):
        custom_settings = load_custom_settings()
    else:
        custom_settings = {}
    
    # User input for API credential
    SUPABASE_URL = st.sidebar.text_input("Supabase URL", custom_settings.get("SUPABASE_URL", "https://your-supabase-url.supabase.co"))
    SUPABASE_KEY = st.sidebar.text_input("Supabase Key", custom_settings.get("SUPABASE_KEY", "your-service-role-key"), type="password")
    TABLE_NAME = st.sidebar.text_input("Table Name", custom_settings.get("TABLE_NAME", "your_vector_table"))
  
    st.title("Delete All Data from Supabase Vector Store")
    st.write("This will permanently delete all rows from the vector store in Supabase.")
    
    if st.button("Delete All Data"):
        if SUPABASE_KEY == "your-service-role-key" or not TABLE_NAME:
            st.error("⚠️ Please provide valid Supabase credentials and table name!")
        else:
            try:
                supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                response = supabase.table(TABLE_NAME).delete().neq("id", 0).execute()
                st.success("✅ All rows have been deleted successfully!")
            except Exception as e:
                st.error(f"❌ Failed to delete data: {e}")


# Contact Page with a Button
elif page == "Contact":
    st.title("📬 Contact Me")
    st.write("Feel free to reach out for collaborations, suggestions, or feedback!")

    email_address = "jackvdv3@gmail.com"
    subject = "Feedback on Your App"
    body = "Hello Jack,%0D%0A%0D%0AI wanted to share some feedback on your app..."
    mailto_link = f"mailto:{email_address}?subject={subject}&body={body}"

    st.markdown(f'<a href="{mailto_link}" target="_blank" style="text-decoration:none; font-size:18px; padding:10px; background-color:#0078D4; color:white; border-radius:5px; display:inline-block;">📧 Click here to send an email</a>', unsafe_allow_html=True)

    st.write("---")
    st.write("### 📧 Connect with Me")
    st.write("📧 [Email](mailto:jackvdv3@gmail.com)")
    st.write("💼 [LinkedIn](https://www.linkedin.com/in/jackvandervall)")
    st.write("📂 [GitHub](https://github.com/jackvandervall)")