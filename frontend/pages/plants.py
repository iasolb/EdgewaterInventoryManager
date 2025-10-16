import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Plants",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)   

st.title("Plants")
st.write("This feature is coming soon!")   
btn_col1 = st.columns(1)[0]
with btn_col1:
    if st.button("Back", disabled=False):
        st.switch_page("edgewater.py")