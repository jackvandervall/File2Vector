import streamlit as st
from scripts.utils import load_custom_settings, create_supabase_client

def show():
    # Load custom settings if button is pressed
    custom_settings = load_custom_settings() if st.sidebar.checkbox("Custom Settings") else {}

    # User input for API credential
    SUPABASE_URL = st.sidebar.text_input("Supabase URL", custom_settings.get("SUPABASE_URL", "https://your-supabase-url.supabase.co"))
    SUPABASE_KEY = st.sidebar.text_input("Supabase Key", custom_settings.get("SUPABASE_KEY", "your-service-role-key"), type="password")
    TABLE_NAME = st.sidebar.text_input("Table Name", custom_settings.get("TABLE_NAME", "your_vector_table"))
  
    st.title("Database Management")
    st.write("This will permanently delete all rows from the vector store in Supabase.")
    
    if st.button("Delete Vectors"):
        if SUPABASE_KEY == "your-service-role-key" or not TABLE_NAME:
            st.error("⚠️ Please provide valid Supabase credentials and table name!")
        else:
            try:
                supabase = create_supabase_client(SUPABASE_URL, SUPABASE_KEY)
                response = supabase.table(TABLE_NAME).delete().neq("id", 0).execute()
                st.success("✅ All rows have been deleted successfully!")
            except Exception as e:
                st.error(f"❌ Failed to delete data: {e}")