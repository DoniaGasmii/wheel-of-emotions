import streamlit as st
from pathlib import Path
from utils.tree_state import is_custom, clear_custom_tree


def show():
    st.markdown("""
    <style>
    .landing-title { font-size: 42px; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 4px; }
    .landing-sub { font-size: 17px; color: #888; margin-bottom: 40px; line-height: 1.6; }
    .section-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.12em;
        color: #555; margin-bottom: 12px; font-weight: 600; }
    .wheel-card { border: 1px solid #2a2a3e; border-radius: 12px; padding: 24px;
        background: #0f0f1a; text-align: center; }
    .card-title { font-size: 18px; font-weight: 700; margin-bottom: 6px; }
    .card-sub { font-size: 13px; color: #777; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="landing-title">🌈 feelmap</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="landing-sub">
        A tool for teaching teams who use emotion wheels to track how their students feel.<br>
        Digitise your sticker annotations, explore the data, and share the story of a semester.
    </div>
    """, unsafe_allow_html=True)

    # ── Wheel selection ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Step 1 — Choose your emotion wheel</div>',
                unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="wheel-card">
            <div class="card-title">Default wheel</div>
            <div class="card-sub">The standard 7-core emotion wheel<br>
            (Happy, Sad, Angry, Fearful, Bad, Disgusted, Surprised)</div>
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
        <div class="wheel-card">
            <div class="card-title">Custom wheel</div>
            <div class="card-sub">Define your own emotion tree —<br>
            any structure, any labels, any depth</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
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
            st.markdown("### Annotate")
            st.caption("Mark which emotions had stickers each week.")
            if st.button("Go to Annotate", use_container_width=True, type="primary", key="go_annotate"):
                st.session_state["page"] = "annotate"
                st.rerun()
        with c2:
            st.markdown("### Visualise")
            st.caption("Explore charts and animated timelapses.")
            if st.button("Go to Visualise", use_container_width=True, type="primary", key="go_visualise"):
                st.session_state["page"] = "visualize"
                st.rerun()
        with c3:
            st.markdown("### Analyse")
            st.caption("Get insights about emotion patterns.")
            if st.button("Go to Analyse", use_container_width=True, type="primary", key="go_analyse"):
                st.session_state["page"] = "analyse"
                st.rerun()