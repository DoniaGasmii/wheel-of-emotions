import streamlit as st
from utils.vision import get_api_key

st.set_page_config(
    page_title="feelmap",
    page_icon="🌈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("🌈 feelmap")
st.sidebar.caption("Emotion wheel tracker")

page = st.sidebar.radio(
    "Navigate",
    ["📤 Upload & Process", "📊 Visualize"],
    label_visibility="collapsed"
)

# Validate key on startup
try:
    get_api_key()
    st.sidebar.success("API key loaded ✅", icon="🔑")
except ValueError:
    st.sidebar.error("GEMINI_API_KEY missing — add it to your .env file")

st.sidebar.divider()
st.sidebar.caption("Powered by Gemini Flash · Built with ❤️")

if page == "📤 Upload & Process":
    from pages.upload import show
    show()
elif page == "📊 Visualize":
    from pages.visualize import show
    show()