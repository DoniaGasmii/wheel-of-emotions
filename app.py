import streamlit as st

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

st.sidebar.divider()
api_key = st.sidebar.text_input(
    "Anthropic API key",
    type="password",
    placeholder="sk-ant-...",
    help="Your key is never stored — it lives only in this session."
)

if api_key:
    st.session_state["api_key"] = api_key

if page == "📤 Upload & Process":
    from pages.upload import show
    show()
elif page == "📊 Visualize":
    from pages.visualize import show
    show()
