import streamlit as st
from streamlit_extras.let_it_rain import rain

# Page confi
st.set_page_config(page_title="File2Vector", page_icon="📂", layout="wide")

rain(
    emoji="🎉",
    font_size=20,
    falling_speed=3,
    animation_length="infinite"
)


def show():
    # Introduction
    st.title("🥳 File2Vector - :violet[NEW RELEASE]")
    st.write(
        "A tool that allows users to upload and store various file types in their own **:green[Supabase] vector database**."
    )
    st.write(
        "It extracts text from **:violet[DOCX], :violet[PDFs], and :violet[spreadsheets]**, generating **:violet[embeddings]** while storing them efficiently."
    )
    
    st.write("")

    # Display Image Using Streamlit
    st.image("img/vector_space.webp", use_container_width=True)

    # Features section below the image
    st.markdown("### 🎆 Features")
    st.markdown(
        """
    - ✅ **Supports multiple file types**: DOCX, PDFs, CSVs, and more  
    - ✅ **Automatic text extraction** from documents  
    - ✅ **Embeddings generation** for vector storage  
    - ✅ **Seamless integration with Supabase**  
    - ✅ **User-friendly interface for easy file uploads**  
    """
    )

    # Instructions
    st.markdown("### 📌 How to Use")
    with st.expander("📖 Read Instructions"):
        st.markdown(
        """
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
    """
    )

    st.write("***")
    st.write("*[:violet[04/03/2025 release]](https://github.com/jackvandervall/File2Vector)*")