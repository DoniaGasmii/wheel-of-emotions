import streamlit as st

st.set_page_config(
    page_title="feelmap",
    page_icon="🌈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: #0f0f0f;
}
[data-testid="stSidebar"] * {
    color: #e0e0e0 !important;
}
.sidebar-title {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: #fff !important;
    margin-bottom: 4px;
}
.sidebar-sub {
    font-size: 11px;
    color: #666 !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 24px;
}
.nav-label {
    font-size: 11px;
    color: #555 !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown('<div class="sidebar-title">🌈 feelmap</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-sub">emotion wheel tracker</div>', unsafe_allow_html=True)

st.sidebar.markdown('<div class="nav-label">Navigation</div>', unsafe_allow_html=True)
page = st.sidebar.radio(
    "nav",
    ["1 · Annotate", "2 · Analyse"],
    label_visibility="collapsed"
)

st.sidebar.divider()

from utils.vision import get_api_key
try:
    get_api_key()
    st.sidebar.success("API key loaded ✅")
except ValueError:
    st.sidebar.caption("⚠ GEMINI_API_KEY missing in .env")

st.sidebar.divider()
st.sidebar.caption("Built with ❤️ for the facilitators")

if page == "1 · Annotate":
    from pages.annotate import show
    show()
elif page == "2 · Analyse":
    from pages.visualize import show
    show()