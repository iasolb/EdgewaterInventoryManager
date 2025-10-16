import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import base64

# Add parent directory to path to import from root level modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db_session
from models import Item  # Change to whatever table you want to display

# Page configuration
st.set_page_config(
    page_title="Edgewater Inventory Manager",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Function to load and encode image for background
def get_base64_image(image_path):
    """Convert image to base64 for CSS background"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"Image not found: {image_path}")
        return None


# Add custom CSS with background image
def set_background(image_path):
    """Set background image using CSS"""
    base64_image = get_base64_image(image_path)
    if base64_image:
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{base64_image}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            /* Add semi-transparent overlay for better readability */
            .stApp::before {{
                content: "";
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(255, 255, 255, 0.85);
                z-index: -1;
            }}
            /* Style the dataframe container */
            .dataframe-container {{
                background-color: rgba(255, 255, 255, 0.95);
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )


# Set paths - using absolute paths from the script location
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
LOGO_PATH = (
    PROJECT_ROOT / "database" / "datasource" / "image_assets" / "edgewater_logo.png"
)
BACKGROUND_PATH = (
    PROJECT_ROOT
    / "database"
    / "datasource"
    / "image_assets"
    / "farmstand_background.png"
)

# Set background
set_background(BACKGROUND_PATH)

# Display logo in header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image(LOGO_PATH, use_container_width=True)
    except:
        st.title("🌿 Edgewater Inventory Manager")
        st.caption("(Logo image not found - add your logo to image_assets/)")

# Main content
btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
with btn_col1:
    st.button("Plants", disabled=False)
with btn_col2:
    st.button("Plantings", disabled=False)
with btn_col3:
    st.button("Label Generator (Coming Soon!)", disabled=False)
with btn_col4:
    st.button("Sales and Analytics (Coming Soon!)", disabled=False)

# Title for the table section
st.header("Inventory Items")

# Fetch data from database
try:
    with get_db_session() as session:
        # Query all items - change this to any table you want
        items = session.query(Item).all()

        # Convert to DataFrame
        if items:
            # Extract attributes from SQLAlchemy objects
            data = []
            for item in items:
                # Get all columns from the model
                item_dict = {
                    column.name: getattr(item, column.name)
                    for column in Item.__table__.columns
                }
                data.append(item_dict)

            df = pd.DataFrame(data)

            # Display the dataframe
            st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True, height=500)
            st.markdown("</div>", unsafe_allow_html=True)

            # Show row count
            st.success(f"Total records: {len(df)}")
        else:
            st.info("No items found in the database.")

except Exception as e:
    st.error(f"Error connecting to database: {str(e)}")
    st.info("Make sure your database is running and properly configured in .env")

    # Show example of what would be displayed
    st.subheader("Example Data (Database not connected)")
    example_df = pd.DataFrame(
        {
            "ID": [1, 2, 3],
            "Name": ["Tomato", "Lettuce", "Cucumber"],
            "Type": ["Vegetable", "Vegetable", "Vegetable"],
            "Price": [2.99, 1.99, 1.49],
        }
    )
    st.dataframe(example_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Edgewater Inventory Management System</p>
    </div>
    """,
    unsafe_allow_html=True,
)
