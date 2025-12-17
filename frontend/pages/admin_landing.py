import streamlit as st

st.set_page_config(
    page_title="Admin Landing Page",
    page_icon="",  # TODO get or create a real favicon
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Top navigation row
top_row = st.columns([1, 2, 1])
with top_row[0]:  # left column - back button
    if st.button("← Back"):
        st.switch_page("edgewater.py")
with top_row[1]:  # middle column - title
    pass
with top_row[2]:  # right column - empty for now
    st.markdown("## Admin View")

st.divider()

# Header
st.write("### Select Table to View/Edit")

# Button grid - 4 columns, 4 rows
row1 = st.columns(4)
with row1[0]:
    if st.button("Items", use_container_width=True):
        st.switch_page("pages/item.py")
with row1[1]:
    if st.button("Items Types", use_container_width=True):
        st.switch_page("pages/item_type.py")
with row1[2]:
    if st.button("Inventory", use_container_width=True):
        st.switch_page("pages/inventory.py")
with row1[3]:
    if st.button("Orders", use_container_width=True):
        st.switch_page("pages/order.py")

row2 = st.columns(4)
with row2[0]:
    if st.button("Order Items", use_container_width=True):
        st.switch_page("pages/order_item.py")
with row2[1]:
    if st.button("Order Item Type", use_container_width=True):
        st.switch_page("pages/order_item_type.py")
with row2[2]:
    if st.button("Order Notes", use_container_width=True):
        st.switch_page("pages/order_note.py")
with row2[3]:
    if st.button("Shippers", use_container_width=True):
        st.switch_page("pages/shipper.py")

row3 = st.columns(4)
with row3[0]:
    if st.button("Suppliers", use_container_width=True):
        st.switch_page("pages/supplier.py")
with row3[1]:
    if st.button("Growing Seasons", use_container_width=True):
        st.switch_page("pages/growing_season.py")
with row3[2]:
    if st.button("Pitch", use_container_width=True):
        st.switch_page("pages/pitch.py")
with row3[3]:
    if st.button("Plantings", use_container_width=True):
        st.switch_page("pages/planting.py")

row4 = st.columns(4)
with row4[0]:
    if st.button("Prices", use_container_width=True):
        st.switch_page("pages/price.py")
with row4[1]:
    if st.button("Units", use_container_width=True):
        st.switch_page("pages/unit.py")
with row4[2]:
    if st.button("Unit Categories", use_container_width=True):
        st.switch_page("pages/unit_categories.py")
with row4[3]:
    if st.button("Brokers", use_container_width=True):
        st.switch_page("pages/broker.py")
