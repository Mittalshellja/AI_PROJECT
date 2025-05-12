import streamlit as st
import requests
from PIL import Image
import io

st.title("Knowledge Graph Generator")
st.write("Upload a PDF or type/paste text to generate a knowledge graph.")

input_mode = st.radio("Select input mode:", ("Text", "PDF"))

if input_mode == "PDF":
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file:
        files = {"file": uploaded_file.getvalue()}
        response = requests.post("http://localhost:8000/upload/", files={"file": uploaded_file})
        if "image_url" in response.json():
            img_url = response.json()["image_url"]
            image = Image.open(requests.get(f"http://localhost:8000{img_url}", stream=True).raw)
            st.image(image, caption="Generated Knowledge Graph")
else:
    input_text = st.text_area("Enter your text here")
    if st.button("Generate Graph") and input_text:
        response = requests.post("http://localhost:8000/upload/", data={"text": input_text})
        if "image_url" in response.json():
            img_url = response.json()["image_url"]
            image = Image.open(requests.get(f"http://localhost:8000{img_url}", stream=True).raw)
            st.image(image, caption="Generated Knowledge Graph")
