import streamlit as st
from st_pages import database, contact, home, monitor, upload
import nltk
# from scripts import query_agent


# ✅ Cache NLTK download so it wruns only once per session
@st.cache_resource
def load_nltk_dependencies():
    nltk.download('punkt')
    
# Call the cachd function
load_nltk_dependencies()
 
# Streamlit Sidebar for API and Table Configuration@
st.sidebar.title("Navigation")

page = st.sidebar.radio("Go to", ["Home", "Upload", "Monitor", "Database", "Contact"])
st.sidebar.write("***")

if page == "Home":
    home.show()

elif page == "Upload":
    upload.show()  

elif page == "Monitor":
    monitor.show()
    
# elif page == "Agents":
#     query_agent.show()
    
elif page == "Database":
    database.show()
    
elif page == "Contact":
    contact.show()
