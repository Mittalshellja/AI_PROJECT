import streamlit as st
import requests
from PIL import Image
import io

# ✅ Replace this with your actual backend Render URL
BACKEND_URL = "https://ai-project-osay.onrender.com"

st.title("Knowledge Graph Generator")
st.write("Upload a PDF or type/paste text to generate a knowledge graph.")

input_mode = st.radio("Select input mode:", ("Text", "PDF"))

if input_mode == "PDF":
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file:
        # Upload PDF to FastAPI
        response = requests.post(
            f"{BACKEND_URL}/upload/",
            files={"file": uploaded_file}
        )
        if response.status_code == 200 and "image_url" in response.json():
            image_url = response.json()["image_url"]
            st.image(image_url, caption="Knowledge Graph", use_column_width=True)
        else:
            st.error("Failed to generate graph.")
else:
    input_text = st.text_area("Enter your text here")
    if st.button("Generate Graph") and input_text:
        response = requests.post(
            f"{BACKEND_URL}/upload/",
            data={"text": input_text}
        )
        if response.status_code == 200 and "image_url" in response.json():
            image_url = response.json()["image_url"]
            st.image(image_url, caption="Knowledge Graph", use_column_width=True)
        else:
            st.error("Failed to generate graph.")
