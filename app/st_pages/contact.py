import streamlit as st

def show():
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