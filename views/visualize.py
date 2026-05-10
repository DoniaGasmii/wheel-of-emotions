import streamlit as st
import plotly.graph_objects as go
import json
import io
import zipfile
from utils.emotion_tree import EMOTION_TREE
from utils.vision import sessions_from_json, load_sessions_from_state


CORE_ANGLES = {
    "Happy":     180,
    "Surprised": 270,
    "Bad":       315,
    "Fearful":   350,
    "Angry":     45,
    "Disgusted": 110,
    "Sad":       145,
}


def build_angle_map():
    points = {}
    sector_width = 50
    for core, base_angle in CORE_ANGLES.items():
        color = EMOTION_TREE[core]["color"]
        subs = list(EMOTION_TREE[core]["subs"].items())
        n = len(subs)
        for i, (sub, leaves) in enumerate(subs):
            sub_angle = base_angle - sector_width/2 + (i+0.5) * sector_width / n
            points[(core, sub, None)] = {"angle": sub_angle, "radius": 0.5, "color": color}
            nl = len(leaves)
            for j, leaf in enumerate(leaves):
                leaf_angle = sub_angle - 4 + (j+0.5) * 8 / max(nl, 1)
                points[(core, sub, leaf)] = {"angle": leaf_angle, "radius": 1.0, "color": color}
        points[(core, None, None)] = {"angle": base_angle, "radius": 0.15, "color": color}
    return points

ANGLE_MAP = build_angle_map()


def make_polar_figure(session: dict, title: str) -> go.Figure:
    fig = go.Figure()
    core_groups = {}

    for e in session.get("emotions", []):
        key = (e.get("core"), e.get("sub"), e.get("sub_sub"))
        pt = ANGLE_MAP.get(key) or ANGLE_MAP.get((e.get("core"), e.get("sub"), None))
        if not pt:
            continue
        core = e.get("core")
        if core not in core_groups:
            core_groups[core] = {"angles": [], "radii": [], "texts": [], "color": pt["color"], "sizes": []}
        label = e.get("sub_sub") or e.get("sub") or core
        r = pt["radius"] * e.get("count", 1)
        core_groups[core]["angles"].append(pt["angle"])
        core_groups[core]["radii"].append(r)
        core_groups[core]["texts"].append(f"{label} ({e.get('count',1)})")
        core_groups[core]["sizes"].append(r * 20 + 8)

    for core, d in core_groups.items():
        fig.add_trace(go.Scatterpolar(
            r=d["radii"], theta=d["angles"],
            mode="markers+text",
            marker=dict(size=d["sizes"], color=d["color"], opacity=0.85,
                       line=dict(color="white", width=1)),
            text=d["texts"], textposition="top center",
            textfont=dict(size=9, color="white"),
            name=core,
            hovertemplate="<b>%{text}</b><extra></extra>",
        ))

    fig.update_layout(
        polar=dict(
            bgcolor="#0d1117",
            radialaxis=dict(visible=False, range=[0, 1.8]),
            angularaxis=dict(
                tickmode="array",
                tickvals=list(CORE_ANGLES.values()),
                ticktext=list(CORE_ANGLES.keys()),
                tickfont=dict(size=13, color="#aaa"),
                direction="clockwise",
                rotation=90,
                gridcolor="#222",
                linecolor="#333",
            ),
        ),
        paper_bgcolor="#0d1117",
        font=dict(color="white"),
        title=dict(text=title, font=dict(size=15, color="#e0e0e0"), x=0.5),
        showlegend=True,
        legend=dict(bgcolor="#0d1117", font=dict(color="#ccc"),
                   bordercolor="#333", borderwidth=1),
        margin=dict(t=60, b=40, l=60, r=60),
        height=560,
    )
    return fig


def make_evolution_figure(sessions: list) -> go.Figure:
    dates = [s["date"] for s in sessions]
    fig = go.Figure()
    for core in EMOTION_TREE:
        color = EMOTION_TREE[core]["color"]
        counts = [
            sum(e.get("count", 0) for e in s.get("emotions", []) if e.get("core") == core)
            for s in sessions
        ]
        fig.add_trace(go.Scatter(
            x=dates, y=counts, name=core,
            mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=8, color=color),
        ))
    fig.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(color="white"),
        xaxis=dict(gridcolor="#222", color="#aaa", title="Session"),
        yaxis=dict(gridcolor="#222", color="#aaa", title="Dot count"),
        legend=dict(bgcolor="#0d1117", bordercolor="#333", borderwidth=1),
        height=380, margin=dict(t=40, b=40),
        title=dict(text="Emotion evolution across sessions",
                  font=dict(size=14, color="#e0e0e0"), x=0.5)
    )
    return fig


def export_zip(sessions: list) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for s in sessions:
            fig = make_polar_figure(s, s["date"])
            img_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
            zf.writestr(f"{s['date']}.png", img_bytes)
        if len(sessions) > 1:
            evo = make_evolution_figure(sessions)
            evo_bytes = evo.to_image(format="png", width=1000, height=500, scale=2)
            zf.writestr("evolution.png", evo_bytes)
    buf.seek(0)
    return buf.read()


def show():
    st.markdown('<h2 style="margin-bottom:4px"> Analyse</h2>', unsafe_allow_html=True)
    st.caption("Upload your save file to explore the emotional journey of your cohort.")

    sessions = []

    uploaded = st.file_uploader(
        "Upload feelmap_sessions.json",
        type=["json"],
        help="Export this from the Annotate tab."
    )

    if uploaded:
        try:
            data = json.load(uploaded)
            sessions = sessions_from_json(data)
            st.success(f"✅ Loaded {len(sessions)} sessions")
        except Exception as e:
            st.error(f"Could not read file: {e}")
            return
    else:
        sessions = load_sessions_from_state()
        if sessions:
            st.info("Showing sessions from current workspace. Upload a save file to load different data.")

    if not sessions:
        st.info("No data yet — upload a `feelmap_sessions.json` file to get started.")
        return

    st.divider()

    # ── Timelapse ────────────────────────────────────────────────────────────
    st.markdown("#### Session timelapse")
    idx = st.slider("Week", 0, len(sessions)-1, 0)
    selected = sessions[idx]
    fig = make_polar_figure(selected, f"Session — {selected['date']}")
    st.plotly_chart(fig, use_container_width=True)

    # dot summary
    core_counts = {}
    for e in selected.get("emotions", []):
        c = e.get("core", "?")
        core_counts[c] = core_counts.get(c, 0) + e.get("count", 0)
    cols = st.columns(len(core_counts) + 1)
    cols[0].metric("Total dots", selected.get("total_dots", "?"))
    for i, (core, cnt) in enumerate(sorted(core_counts.items(), key=lambda x: -x[1])):
        cols[i+1].metric(core, cnt)

    st.divider()

    # ── Evolution ────────────────────────────────────────────────────────────
    if len(sessions) > 1:
        st.markdown("#### Emotion evolution")
        st.plotly_chart(make_evolution_figure(sessions), use_container_width=True)
        st.divider()

    # ── Export ───────────────────────────────────────────────────────────────
    st.markdown("#### Export charts")
    st.caption("Download all session charts as PNGs in a ZIP.")
    if st.button("📦 Generate export ZIP", use_container_width=True):
        with st.spinner("Rendering charts..."):
            try:
                zip_bytes = export_zip(sessions)
                st.download_button(
                    label="⬇️ Download ZIP",
                    data=zip_bytes,
                    file_name="feelmap_export.zip",
                    mime="application/zip",
                    use_container_width=True,
                    type="primary"
                )
            except Exception as e:
                st.error(f"Export failed: {e}")