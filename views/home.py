import streamlit as st
from pathlib import Path
from utils.tree_state import is_custom, clear_custom_tree

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Lora', serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #f0e6da !important;
    border-right: 1px solid #e2d0c0;
}
[data-testid="stSidebar"] * {
    color: #3d2b1f !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 14px;
    font-weight: 500;
    padding: 4px 0;
}

/* Main background */
.main { background: #fdf6f0; }
section[data-testid="stMain"] { background: #fdf6f0; }

/* Cards */
.feel-card {
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    border: 1.5px solid transparent;
    transition: box-shadow 0.2s, border-color 0.2s;
    margin-bottom: 12px;
}
.feel-card:hover {
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
}
.feel-card-default {
    background: linear-gradient(135deg, #fdebd8 0%, #fad4b4 100%);
    border-color: #f0b896;
}
.feel-card-custom {
    background: linear-gradient(135deg, #e8f4f0 0%, #c8e6dc 100%);
    border-color: #9ecfbf;
}
.card-title {
    font-family: 'Lora', serif;
    font-size: 20px;
    font-weight: 600;
    color: #2d2420;
    margin-bottom: 6px;
}
.card-sub {
    font-size: 13px;
    color: #7a5c4a;
    line-height: 1.5;
}

/* Action cards */
.action-card {
    background: #fff8f3;
    border: 1.5px solid #e8d5c4;
    border-radius: 14px;
    padding: 22px 20px;
    text-align: center;
    margin-bottom: 8px;
}
.action-title {
    font-family: 'Lora', serif;
    font-size: 17px;
    font-weight: 600;
    color: #2d2420;
    margin-bottom: 4px;
}
.action-sub {
    font-size: 12px;
    color: #9a7a6a;
}

/* Section label */
.section-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #b08070;
    font-weight: 600;
    margin-bottom: 16px;
}

/* Landing title */
.landing-title {
    font-family: 'Lora', serif;
    font-size: 48px;
    font-weight: 600;
    color: #2d2420;
    letter-spacing: -0.02em;
    margin-bottom: 6px;
    line-height: 1.1;
}
.landing-sub {
    font-size: 16px;
    color: #7a5c4a;
    line-height: 1.7;
    margin-bottom: 40px;
    max-width: 560px;
}

/* Buttons — override Streamlit primary */
.stButton > button {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    border: none !important;
    transition: opacity 0.15s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* Divider */
hr { border-color: #e8d5c4 !important; }

/* Metric */
[data-testid="stMetric"] {
    background: #fff8f3;
    border-radius: 10px;
    padding: 12px;
    border: 1px solid #e8d5c4;
}

/* Expander */
[data-testid="stExpander"] {
    border: 1px solid #e8d5c4 !important;
    border-radius: 10px !important;
    background: #fff8f3 !important;
}

/* Tabs */
[data-testid="stTabs"] button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
}

/* Info/success/warning boxes */
[data-testid="stAlert"] {
    border-radius: 10px !important;
}

/* Plotly charts background to match */
.js-plotly-plot .plotly .bg { fill: #fdf6f0 !important; }
</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def show():
    inject_css()

    st.markdown('<div class="landing-title">🌈 feelmap</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="landing-sub">
        A tool for teaching teams who use emotion wheels to track how their students feel.
        Digitise your sticker annotations, explore the data, and share the story of a semester.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Step 1 — Choose your emotion wheel</div>',
                unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="feel-card feel-card-default">
            <div class="card-title">Default wheel</div>
            <div class="card-sub">The standard 7-core emotion wheel<br>
            Happy, Sad, Angry, Fearful, Bad, Disgusted, Surprised</div>
        </div>
        """, unsafe_allow_html=True)

        wheel_path = Path("assets/wheel.png")
        if wheel_path.exists():
            st.image(str(wheel_path), use_container_width=True, caption="Your emotion wheel")
        else:
            st.caption("Place your wheel image at `assets/wheel.png` to display it here.")

        if st.button("Use default wheel", use_container_width=True, type="primary", key="btn_default"):
            clear_custom_tree()
            st.session_state["wheel_chosen"] = "default"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="feel-card feel-card-custom">
            <div class="card-title">Custom wheel</div>
            <div class="card-sub">Define your own emotion tree —<br>
            any structure, any labels, any depth</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("Build custom wheel", use_container_width=True, key="btn_custom"):
            st.session_state["wheel_chosen"] = "custom"
            st.session_state["page"] = "wheel_builder"
            st.rerun()

    if st.session_state.get("wheel_chosen"):
        st.divider()
        st.markdown('<div class="section-label">Step 2 — What would you like to do?</div>',
                    unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3, gap="large")
        with c1:
            st.markdown("""
            <div class="action-card">
                <div class="action-title">Annotate</div>
                <div class="action-sub">Mark which emotions had stickers each week</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Go to Annotate", use_container_width=True, type="primary", key="go_annotate"):
                st.session_state["page"] = "annotate"
                st.rerun()
        with c2:
            st.markdown("""
            <div class="action-card">
                <div class="action-title">Visualise</div>
                <div class="action-sub">Explore charts and animated timelapses</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Go to Visualise", use_container_width=True, type="primary", key="go_visualise"):
                st.session_state["page"] = "visualize"
                st.rerun()
        with c3:
            st.markdown("""
            <div class="action-card">
                <div class="action-title">Analyse</div>
                <div class="action-sub">Get insights about emotion patterns</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Go to Analyse", use_container_width=True, type="primary", key="go_analyse"):
                st.session_state["page"] = "analyse"
                st.rerun()