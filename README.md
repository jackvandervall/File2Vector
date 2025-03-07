# 🥳 File2Vector - **NEW RELEASE**  

A tool that allows users to upload and store various file types in their own **Supabase vector database**.  
Extract text from **DOCX, PDFs, and spreadsheets**, generating **embeddings** while storing them efficiently.


## ✨ Features  
✔️ **Supports multiple file types**: DOCX, PDFs, CSVs, and more  
✔️ **Automatic text extraction** from documents  
✔️ **Embeddings generation** for vector storage  
✔️ **Seamless integration** with Supabase  
✔️ **User-friendly interface** for easy file uploads  


## 📌 How to Install
Follow these steps to install and run **File2Vector** on your local machine.

## **🔹 Step 1: Install Dependencies**
Before running the app, install the required Python packages.
```sh
pip install -r requirements.txt
```

If there is no `requirements.txt`, you can install the dependencies manually:
```sh
pip install streamlit
```
(Add any additional dependencies if necessary.)

## **🔹 Step 2: Navigate to the App Directory**
Move into the `app/` directory:
```sh
cd app
```

## **🔹 Step 3: Run the Streamlit App**
Start the application by running:
```sh
streamlit run main.py
```
This will launch the **File2Vector** web app in your default browser.


## 📌 How to Use  

1. **Set up Supabase**  
   - Go to [Supabase](https://supabase.com/)  
   - Navigate to **Project Settings** > **Data API**  
   - Copy your **Project URL** and **service_role key**  
   - Paste them into the **Upload tab** of File2Vector  

2. **Upload Files**  
   - Select the documents you want to convert into embeddings  
   - The tool will automatically process and store them in your vector database  

3. **Provide Feedback**  
   - Use the **contact page** to share your experience or report issues  


## 🚀 Roadmap 2025
- [ ] API support for any Embedding provider
- [ ] Upload to any Vector Database
- [ ] Instant RAG functionality using your own LLM API
- [ ] More to be announced...


## 🔗 Connect with Me  
💼 **LinkedIn:** [Jack van der Vall](https://www.linkedin.com/in/jackvandervall)  
📂 **GitHub:** [jackvandervall](https://github.com/jackvandervall)  
