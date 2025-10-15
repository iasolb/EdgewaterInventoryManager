import streamlit as st
from api import EdgewaterAPI
from database import Database

db = Database()
api = EdgewaterAPI()

import streamlit as st

page_bg_img = """
    <style>
    .stApp {
        background-image: url("YOUR_IMAGE_URL_HERE");
        background-size: cover;
        background-attachment: fixed; /* Optional: keeps image fixed while scrolling */
    }
    </style>
    """
st.markdown(page_bg_img, unsafe_allow_html=True)

# Your Streamlit app content goes here
st.title("My Streamlit App with Background Image")
st.write("This is some content on top of the background.")
