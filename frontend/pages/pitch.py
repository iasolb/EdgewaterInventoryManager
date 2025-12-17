import streamlit as st

st.set_page_config(
    page_title="Pitch Table Administration View",
    page_icon="",  # TODO get or create a real favicon
    layout="wide",
    initial_sidebar_state="collapsed",
)
top_row = st.columns([1, 2, 1])

# back button
with top_row[0]:
    if st.button("← Back"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    pass

with top_row[2]:
    pass
st.title("Pitch Administration Table")
st.write("Coming soon...")
st.write(
    "This page will allow administrators to manage pitch table in the database directly."
)
