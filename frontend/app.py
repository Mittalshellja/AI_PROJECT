import streamlit as st
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Knowledge Graph Generator", layout="wide")

st.title("📘 Knowledge Graph Generator")
st.write("Upload a PDF or enter text to generate a knowledge graph.")

# User input: file or text
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
text_input = st.text_area("Or enter text here", height=300)

if st.button("Generate Graph"):
    if uploaded_file:
        files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
        response = requests.post("http://localhost:8000/upload/", files=files)
    elif text_input.strip():
        data = {"text": text_input}
        response = requests.post("http://localhost:8000/upload/", data=data)
    else:
        st.warning("Please upload a file or enter text.")
        st.stop()

    if response.status_code == 200:
        image_url = response.json().get("image_url")
        if image_url:
            st.success("Knowledge graph generated!")
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                image = Image.open(BytesIO(image_response.content))
                st.image(image, caption="Generated Knowledge Graph", use_column_width=True)
            else:
                st.error("Failed to load image from backend.")
        else:
            st.error("No image URL received.")
    else:
        st.error("Something went wrong. Check your FastAPI server.")
