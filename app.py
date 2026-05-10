import streamlit as st

st.set_page_config(
    page_title="feelmap",
    page_icon="🌈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0f0f0f; }
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 🌈 feelmap")
st.sidebar.caption("emotion wheel tracker")
st.sidebar.divider()

page = st.sidebar.radio(
    "nav",
    ["1 · Annotate", "2 · Analyse"],
    label_visibility="collapsed"
)

st.sidebar.divider()
st.sidebar.caption("Built with ❤️ for the facilitators")

if page == "1 · Annotate":
    from views.annotate import show
    show()
else:
    from views.visualize import show
    show()