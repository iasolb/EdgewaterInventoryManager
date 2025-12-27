import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rest"))
from rest.api import EdgewaterAPI

api = EdgewaterAPI()
api.reset_cache("unit_category_cache", api.get_unit_category_full)


st.set_page_config(
    page_title="Unit Category Administration View",
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
st.divider()
st.title("Unit Category Administration Table")
st.divider()
st.write("Coming soon...")
st.write(
    "This page will allow administrators to manage unit category table in the database directly."
)
content_row = st.columns(3)
with content_row[0]:
    pass
with content_row[1]:
    st.data_editor(api.unit_category_cache, use_container_width=False)
with content_row[2]:
    pass
