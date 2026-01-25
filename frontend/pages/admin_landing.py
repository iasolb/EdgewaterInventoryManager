import streamlit as st

st.set_page_config(
    page_title="Admin Landing Page",
    page_icon="",  # TODO get or create a real favicon
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Top navigation row
top_row = st.columns([1, 2, 1])
with top_row[0]:
    if st.button("← Back"):
        st.switch_page("edgewater.py")
with top_row[1]:
    pass
with top_row[2]:
    st.markdown("## Admin View")

st.divider()

st.write("### Select Table to View/Edit")

row1 = st.columns(5)
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
with row1[4]:
    if st.button("Order Item Destinations", use_container_width=True):
        st.switch_page("pages/order_item_destination.py")

row2 = st.columns(5)
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
with row2[4]:
    if st.button("Seasonal Notes", use_container_width=True):
        st.switch_page("pages/seasonal_notes.py")
row3 = st.columns(5)
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
with row3[4]:
    if st.button("Locations", use_container_width=True):
        st.switch_page("pages/locations.py")
row4 = st.columns(5)
with row4[0]:
    if st.button("Prices", use_container_width=True):
        st.switch_page("pages/price.py")
with row4[1]:
    if st.button("Units", use_container_width=True):
        st.switch_page("pages/unit.py")
with row4[2]:
    if st.button("Unit Categories", use_container_width=True):
        st.switch_page("pages/unit_category.py")
with row4[3]:
    if st.button("Brokers", use_container_width=True):
        st.switch_page("pages/broker.py")
with row4[4]:
    if st.button("Users", use_container_width=True):
        st.switch_page("pages/users.py")
