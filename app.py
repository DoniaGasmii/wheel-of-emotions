import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="feelmap",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0f0f0f; }
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
.stRadio label { font-size: 14px; }
</style>
""", unsafe_allow_html=True)

#  Init page state 
if "page" not in st.session_state:
    st.session_state["page"] = "home"

#  Sidebar nav 
st.sidebar.markdown("###  feelmap")
st.sidebar.caption("emotion wheel tracker")
st.sidebar.divider()

from utils.tree_state import is_custom

pages = {
    "home":          "Home",
    "wheel_builder": "Custom wheel",
    "annotate":      "1 · Annotate",
    "visualize":     "2 · Visualise",
    "analyse":       "3 · Analyse",
}

selected = st.sidebar.radio(
    "nav", list(pages.values()),
    index=list(pages.keys()).index(st.session_state["page"]),
    label_visibility="collapsed"
)

# sync radio → page state
for key, label in pages.items():
    if selected == label:
        st.session_state["page"] = key
        break

if is_custom():
    st.sidebar.success("Custom wheel active")
else:
    st.sidebar.info("Using default wheel")

st.sidebar.divider()
st.sidebar.caption("Built with care for people who care about how their students feel.")

#  Route to page 
page = st.session_state["page"]

if page == "home":
    from views.home import show
    show()
elif page == "wheel_builder":
    from views.wheel_builder import show
    show()
elif page == "annotate":
    from views.annotate import show
    show()
elif page == "visualize":
    from views.visualize import show
    show()
elif page == "analyse":
    from views.analyse import show
    show()