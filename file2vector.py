import streamlit as st
import pandas as pd
import nltk
import textwrap
import pymupdf  # Correct import for PyMuPDF
import docx  # For Word documents
import numpy as np
import pdfplumber  # For extracting tables from PDFs
from nltk.tokenize import sent_tokenize
from supabase import create_client
import cohere

nltk.download('punkt')
nltk.download('punkt_tab')

# Streamlit Sidebar for API and Table Configuration
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Upload", "Contact"])

if page == "Home":
    st.title("File2Vector")
    st.write("Hi, welcome to the file upload hub for Vector data storage.")
    st.write("---")
    st.write("1. Go to https://supabase.com/: Project Settings > Data API and paste your Project URL + service_role into the Upload tab.")
    st.write("2. Upload the files you want to convert to embeddings.")
    st.write("3. Provide feedback via the contact page.")


# Upload File Page
if page == "Upload":
    st.title("Upload File")
    st.write("This Supabase Vector Uploader is an app that allows users to upload and store various file types into their own Supabase vector database. It extracts text from documents, tables from PDFs, and structured data from spreadsheets, generating embeddings using Cohere and storing them efficiently.")

    SUPABASE_URL = st.sidebar.text_input("Supabase URL", "https://your-supabase-url.supabase.co")
    SUPABASE_KEY = st.sidebar.text_input("Supabase Key", "your-service-role-key", type="password")
    COHERE_API_KEY = st.sidebar.text_input("Cohere API Key", "your-cohere-api-key", type="password")
    TABLE_NAME = st.sidebar.text_input("Table Name", "your_vector_table")

    # Ensure Supabase API Key is provided
    if SUPABASE_KEY == "your-service-role-key":
        st.write("⚠️ Please provide your dataset and API credentials in order to start your upload!.")
        st.stop()

    # Initialize Supabase Client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    co = cohere.Client(COHERE_API_KEY)

    def split_text(text, chunk_size=300):
        """Splits text into smaller chunks while preserving sentence structure"""
        sentences = sent_tokenize(text)
        chunks = []
        temp_chunk = ""

        for sentence in sentences:
            if len(temp_chunk) + len(sentence) <= chunk_size:
                temp_chunk += " " + sentence
            else:
                chunks.append(temp_chunk.strip())
                temp_chunk = sentence

        if temp_chunk:
            chunks.append(temp_chunk.strip())

        return chunks

    # Extract from PDF
    def extract_text_from_pdf(uploaded_file):
        """Extracts text from a PDF file using PyMuPDF"""
        text = ""
        doc = pymupdf.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            text += page.get_text("text") + "\n"
        return text.strip()

    def extract_tables_from_pdf(uploaded_file):
        """Extracts tables from a PDF using pdfplumber"""
        tables = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                extracted_table = page.extract_table()
                if extracted_table:
                    df = pd.DataFrame(extracted_table[1:], columns=extracted_table[0])
                    tables.append(df)
        return tables

    # Extract from DOCX
    def extract_text_from_docx(uploaded_file):
        """Extracts text from a Word document"""
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs]).strip()

    def generate_embedding(text):
        """Generate an embedding vector from text using Cohere API"""
        response = co.embed(
            texts=[text],
            model="embed-english-v3.0",  
            input_type="search_document"
        )
        vector = response.embeddings[0]

        expected_dim = 1024
        if len(vector) > expected_dim:
            vector = vector[:expected_dim]
        elif len(vector) < expected_dim:
            vector = np.pad(vector, (0, expected_dim - len(vector)), 'constant').tolist()

        return vector

    def upload_to_supabase(content, metadata):
        """Uploads text chunks to Supabase"""
        text_chunks = split_text(content, chunk_size=300)
        for chunk in text_chunks:
            vector = generate_embedding(chunk)
            supabase.table(TABLE_NAME).insert({
                "content": chunk,
                "embedding": vector,
                "metadata": metadata
            }).execute()
        st.write(f"Inserted {len(text_chunks)} chunks")

    # Streamlit UI
    st.title("Upload Files to Supabase Vector DB")

    uploaded_file = st.file_uploader("Choose a file", type=["csv", "pdf", "docx", "xlsx"])

    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1]
        metadata = {"filename": uploaded_file.name}

        if file_type == "pdf":
            extract_option = st.radio(
                "Select what to extract from PDF:",
                ["Text Only", "Tables Only", "Both"]
            )
            
            text = extract_text_from_pdf(uploaded_file)
            tables = extract_tables_from_pdf(uploaded_file)

            if extract_option == "Text Only":
                st.write("Extracted text:")
                st.text_area("PDF Text", text, height=300)
            
            elif extract_option == "Tables Only" and tables:
                st.write("Extracted tables:")
                for df in tables:
                    st.dataframe(df)
            
            elif extract_option == "Both":
                st.write("Extracted text:")
                st.text_area("PDF Text", text, height=300)
                if tables:
                    st.write("Extracted tables:")
                    for df in tables:
                        st.dataframe(df)

            if st.button("Upload to Supabase"):
                if extract_option in ["Text Only", "Both"]:
                    upload_to_supabase(text, metadata)
                if extract_option in ["Tables Only", "Both"] and tables:
                    for df in tables:
                        supabase.table(TABLE_NAME).insert({"content": None, "embedding": None, "metadata": df.to_dict(orient="records")}).execute()
                st.success("PDF uploaded successfully!")

# Contact Page with Button
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
    st.write("📧 **Email:** [jackvdv3@gmail.com](mailto:jackvdv3@gmail.com)")
    st.write("💼 **LinkedIn:** [Jack van der Vall](https://www.linkedin.com/in/yourjackvandervall)")
    st.write("📂 **GitHub:** [jackvandervall](https://github.com/jackvandervall)")