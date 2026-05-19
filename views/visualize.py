import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import json
import io
import zipfile
from PIL import Image
from utils.emotion_tree import EMOTION_TREE
from utils.vision import sessions_from_json, load_sessions_from_state

# ── Color palette matching the wheel ────────────────────────────────────────
CORE_COLORS = {
    "Happy":     "#e8875a",
    "Surprised": "#f0c93a",
    "Bad":       "#6abf8a",
    "Fearful":   "#5bbcd6",
    "Angry":     "#9b6bb5",
    "Disgusted": "#8b7bc8",
    "Sad":       "#b87ab5",
}

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
        color = CORE_COLORS[core]
        subs = list(EMOTION_TREE[core]["subs"].items())
        n = len(subs)
        points[(core, None, None)] = {"angle": base_angle, "radius": 0.2, "color": color}
        for i, (sub, leaves) in enumerate(subs):
            sub_angle = base_angle - sector_width/2 + (i+0.5) * sector_width / n
            points[(core, sub, None)] = {"angle": sub_angle, "radius": 0.55, "color": color}
            nl = len(leaves)
            for j, leaf in enumerate(leaves):
                leaf_angle = sub_angle - 5 + (j+0.5) * 10 / max(nl, 1)
                points[(core, sub, leaf)] = {"angle": leaf_angle, "radius": 1.0, "color": color}
    return points

ANGLE_MAP = build_angle_map()


def get_core_totals(session):
    totals = {c: 0 for c in CORE_COLORS}
    for e in session.get("emotions", []):
        c = e.get("core")
        if c in totals:
            totals[c] += e.get("count", 0)
    return totals


# ── Chart 1: Polar wheel ─────────────────────────────────────────────────────
def make_polar(session, title=""):
    fig = go.Figure()
    core_groups = {}
    for e in session.get("emotions", []):
        key = (e.get("core"), e.get("sub"), e.get("sub_sub"))
        pt = ANGLE_MAP.get(key) or ANGLE_MAP.get((e.get("core"), e.get("sub"), None)) or ANGLE_MAP.get((e.get("core"), None, None))
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
        core_groups[core]["sizes"].append(min(r * 22 + 8, 60))

    for core, d in core_groups.items():
        fig.add_trace(go.Scatterpolar(
            r=d["radii"], theta=d["angles"],
            mode="markers+text",
            marker=dict(size=d["sizes"], color=d["color"], opacity=0.85,
                       line=dict(color="white", width=1.5)),
            text=d["texts"], textposition="top center",
            textfont=dict(size=9, color="white"),
            name=core,
            hovertemplate="<b>%{text}</b><extra></extra>",
        ))

    fig.update_layout(
        polar=dict(
            bgcolor="#0d1117",
            radialaxis=dict(visible=False, range=[0, 2.0]),
            angularaxis=dict(
                tickmode="array",
                tickvals=list(CORE_ANGLES.values()),
                ticktext=list(CORE_ANGLES.keys()),
                tickfont=dict(size=13, color="#aaa"),
                direction="clockwise", rotation=90,
                gridcolor="#1e1e2e", linecolor="#2a2a3e",
            ),
        ),
        paper_bgcolor="#0d1117", font=dict(color="white"),
        title=dict(text=title, font=dict(size=15, color="#e0e0e0"), x=0.5),
        showlegend=True,
        legend=dict(bgcolor="#0d1117", font=dict(color="#ccc"),
                   bordercolor="#333", borderwidth=1),
        margin=dict(t=60, b=40, l=60, r=60), height=560,
    )
    return fig


# ── Chart 2: Stacked bar — core emotion evolution ────────────────────────────
def make_stacked_bar(sessions):
    dates = [s["date"] for s in sessions]
    fig = go.Figure()
    for core in CORE_COLORS:
        counts = [get_core_totals(s).get(core, 0) for s in sessions]
        fig.add_trace(go.Bar(
            name=core, x=dates, y=counts,
            marker_color=CORE_COLORS[core],
            hovertemplate=f"<b>{core}</b>: %{{y}}<extra></extra>"
        ))
    fig.update_layout(
        barmode="stack",
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(color="white"),
        xaxis=dict(gridcolor="#1e1e2e", color="#aaa", title="Session"),
        yaxis=dict(gridcolor="#1e1e2e", color="#aaa", title="Dot count"),
        legend=dict(bgcolor="#0d1117", bordercolor="#333", borderwidth=1),
        height=400, margin=dict(t=30, b=40),
        title=dict(text="Emotion distribution over time", font=dict(size=14, color="#e0e0e0"), x=0.5)
    )
    return fig


# ── Chart 3: Line chart — core emotion trends ────────────────────────────────
def make_lines(sessions):
    dates = [s["date"] for s in sessions]
    fig = go.Figure()
    for core in CORE_COLORS:
        counts = [get_core_totals(s).get(core, 0) for s in sessions]
        fig.add_trace(go.Scatter(
            x=dates, y=counts, name=core,
            mode="lines+markers",
            line=dict(color=CORE_COLORS[core], width=2.5),
            marker=dict(size=8, color=CORE_COLORS[core]),
            hovertemplate=f"<b>{core}</b>: %{{y}}<extra></extra>"
        ))
    fig.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(color="white"),
        xaxis=dict(gridcolor="#1e1e2e", color="#aaa"),
        yaxis=dict(gridcolor="#1e1e2e", color="#aaa", title="Dot count"),
        legend=dict(bgcolor="#0d1117", bordercolor="#333", borderwidth=1),
        height=400, margin=dict(t=30, b=40),
        title=dict(text="Emotion trends across sessions", font=dict(size=14, color="#e0e0e0"), x=0.5)
    )
    return fig


# ── Chart 4: Heatmap — emotion × session ────────────────────────────────────
def make_heatmap(sessions):
    # collect all sub-emotions that appear
    all_subs = []
    for s in sessions:
        for e in s.get("emotions", []):
            label = e.get("sub_sub") or e.get("sub") or e.get("core")
            if label and label not in all_subs:
                all_subs.append(label)

    dates = [s["date"] for s in sessions]
    matrix = []
    for sub in all_subs:
        row = []
        for s in sessions:
            count = sum(e.get("count", 0) for e in s.get("emotions", [])
                       if (e.get("sub_sub") or e.get("sub") or e.get("core")) == sub)
            row.append(count)
        matrix.append(row)

    fig = go.Figure(go.Heatmap(
        z=matrix, x=dates, y=all_subs,
        colorscale=[[0, "#0d1117"], [0.2, "#1e3a5f"], [0.5, "#e8875a"], [1, "#f0c93a"]],
        hovertemplate="<b>%{y}</b> on %{x}: %{z} dots<extra></extra>",
        showscale=True,
    ))
    fig.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(color="white", size=11),
        xaxis=dict(color="#aaa"),
        yaxis=dict(color="#aaa", autorange="reversed"),
        height=max(400, len(all_subs) * 22),
        margin=dict(t=30, b=40, l=160, r=40),
        title=dict(text="Emotion heatmap", font=dict(size=14, color="#e0e0e0"), x=0.5)
    )
    return fig


# ── Chart 5: Donut — single session breakdown ────────────────────────────────
def make_donut(session):
    totals = get_core_totals(session)
    labels = [k for k, v in totals.items() if v > 0]
    values = [totals[k] for k in labels]
    colors = [CORE_COLORS[k] for k in labels]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.5,
        marker=dict(colors=colors, line=dict(color="#0d1117", width=2)),
        textfont=dict(size=13, color="white"),
        hovertemplate="<b>%{label}</b>: %{value} dots (%{percent})<extra></extra>"
    ))
    fig.update_layout(
        paper_bgcolor="#0d1117", font=dict(color="white"),
        showlegend=True,
        legend=dict(bgcolor="#0d1117", font=dict(color="#ccc"), bordercolor="#333", borderwidth=1),
        height=400, margin=dict(t=30, b=20),
        title=dict(text=f"Session breakdown — {session['date']}", font=dict(size=14, color="#e0e0e0"), x=0.5)
    )
    return fig


# ── GIF export ───────────────────────────────────────────────────────────────
def make_gif(sessions) -> bytes:
    frames = []
    for s in sessions:
        fig = make_polar(s, f"Session — {s['date']}")
        img_bytes = fig.to_image(format="png", width=800, height=700, scale=1.5)
        frame = Image.open(io.BytesIO(img_bytes))
        frames.append(frame)

    buf = io.BytesIO()
    frames[0].save(
        buf, format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=1200,
        loop=0,
    )
    buf.seek(0)
    return buf.read()


def make_zip(sessions) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for s in sessions:
            fig = make_polar(s, f"Session — {s['date']}")
            zf.writestr(f"polar_{s['date']}.png", fig.to_image(format="png", width=800, height=700, scale=2))
        if len(sessions) > 1:
            zf.writestr("stacked_bar.png", make_stacked_bar(sessions).to_image(format="png", width=1000, height=500, scale=2))
            zf.writestr("lines.png", make_lines(sessions).to_image(format="png", width=1000, height=500, scale=2))
            zf.writestr("heatmap.png", make_heatmap(sessions).to_image(format="png", width=1000, height=max(600, len(set(
                e.get("sub_sub") or e.get("sub") or e.get("core")
                for s in sessions for e in s.get("emotions", [])
            )) * 22), scale=2))
    buf.seek(0)
    return buf.read()


# ── Main page ────────────────────────────────────────────────────────────────
def show():
    st.markdown('<h2 style="margin-bottom:4px">📊 Analyse</h2>', unsafe_allow_html=True)
    st.caption("Upload your save file to explore the emotional journey of your cohort.")

    uploaded = st.file_uploader("Upload feelmap_sessions.json", type=["json"], label_visibility="collapsed")

    sessions = []
    if uploaded:
        try:
            data = json.load(uploaded)
            sessions = sessions_from_json(data)
            st.success(f"✅ {len(sessions)} sessions loaded")
        except Exception as e:
            st.error(f"Could not read file: {e}")
            return
    else:
        sessions = load_sessions_from_state()
        if sessions:
            st.info(f"Showing {len(sessions)} sessions from current workspace.")

    if not sessions:
        st.info("Upload a `feelmap_sessions.json` to get started.")
        return

    st.divider()

    # ── Viz selector ─────────────────────────────────────────────────────────
    viz = st.radio(
        "Choose visualisation",
        ["🌀 Polar wheel", "📊 Stacked bar", "📈 Line trends", "🔥 Heatmap"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if viz == "🌀 Polar wheel":
        st.markdown("#### Session polar wheel")
        dates = [s["date"] for s in sessions]
        idx = st.select_slider("Session", options=list(range(len(dates))),
                               format_func=lambda i: dates[i])
        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(make_polar(sessions[idx], sessions[idx]["date"]), use_container_width=True)
        with col2:
            st.markdown("##### Breakdown")
            totals = get_core_totals(sessions[idx])
            for core, cnt in sorted(totals.items(), key=lambda x: -x[1]):
                if cnt > 0:
                    pct = int(cnt / sessions[idx]["total_dots"] * 100)
                    st.markdown(f"<span style='color:{CORE_COLORS[core]}'>●</span> **{core}** — {cnt} dots ({pct}%)", unsafe_allow_html=True)

    elif viz == "📊 Stacked bar":
        st.plotly_chart(make_stacked_bar(sessions), use_container_width=True)

    elif viz == "📈 Line trends":
        st.plotly_chart(make_lines(sessions), use_container_width=True)

    elif viz == "🔥 Heatmap":
        st.plotly_chart(make_heatmap(sessions), use_container_width=True)

    st.divider()

    # ── Export ───────────────────────────────────────────────────────────────
    st.markdown("#### Export")
    col_gif, col_zip = st.columns(2)

    with col_gif:
        st.markdown("**🎞 Animated GIF** — polar wheel timelapse")
        if st.button("Generate GIF", use_container_width=True):
            with st.spinner("Rendering frames..."):
                try:
                    gif = make_gif(sessions)
                    st.download_button(
                        "⬇️ Download GIF",
                        data=gif,
                        file_name="feelmap_timelapse.gif",
                        mime="image/gif",
                        use_container_width=True,
                        type="primary"
                    )
                except Exception as e:
                    st.error(f"GIF export failed: {e}")

    with col_zip:
        st.markdown("**📦 ZIP** — all charts as PNG")
        if st.button("Generate ZIP", use_container_width=True):
            with st.spinner("Rendering charts..."):
                try:
                    zip_bytes = make_zip(sessions)
                    st.download_button(
                        "⬇️ Download ZIP",
                        data=zip_bytes,
                        file_name="feelmap_export.zip",
                        mime="application/zip",
                        use_container_width=True,
                        type="primary"
                    )
                except Exception as e:
                    st.error(f"ZIP export failed: {e}")