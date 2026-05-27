import streamlit as st
from .home import inject_css
import plotly.graph_objects as go
import json
import io
import numpy as np
from datetime import datetime
from utils.emotion_tree import EMOTION_TREE
from utils.vision import sessions_from_json, load_sessions_from_state

CORE_COLORS = {
    "Happy":     "#e8875a",
    "Surprised": "#f0c93a",
    "Bad":       "#6abf8a",
    "Fearful":   "#5bbcd6",
    "Angry":     "#9b6bb5",
    "Disgusted": "#8b7bc8",
    "Sad":       "#b87ab5",
}

POSITIVE = {"Happy", "Surprised"}
NEGATIVE = {"Bad", "Fearful", "Angry", "Disgusted", "Sad"}


#  Granularity helpers 

def get_label(e):
    return e.get("sub_sub") or e.get("sub") or e.get("core")

def get_emotions_at_level(session, level):
    """Aggregate session emotions at the chosen granularity level.
    Returns dict {label: count}"""
    agg = {}
    for e in session.get("emotions", []):
        if level == "Core":
            key = e.get("core")
        elif level == "Sub":
            key = e.get("sub") or e.get("core")
        else:  # Sub-sub
            key = get_label(e)
        if key:
            agg[key] = agg.get(key, 0) + e.get("count", 0)
    return agg

def get_color_for_label(label, level):
    if level == "Core":
        return CORE_COLORS.get(label, "#888")
    for core, data in EMOTION_TREE.items():
        if label == core:
            return CORE_COLORS[core]
        for sub, leaves in data["subs"].items():
            if label == sub or label in leaves:
                return CORE_COLORS[core]
    return "#888"

def get_core_totals(session):
    totals = {c: 0 for c in CORE_COLORS}
    for e in session.get("emotions", []):
        c = e.get("core")
        if c in totals:
            totals[c] += e.get("count", 0)
    return totals


#  Chart 1: Polar wheel 

CORE_ANGLES = {
    "Happy": 180, "Surprised": 270, "Bad": 315,
    "Fearful": 350, "Angry": 45, "Disgusted": 110, "Sad": 145,
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
            for j, leaf in enumerate(leaves):
                leaf_angle = sub_angle - 5 + (j+0.5) * 10 / max(len(leaves), 1)
                points[(core, sub, leaf)] = {"angle": leaf_angle, "radius": 1.0, "color": color}
    return points

ANGLE_MAP = build_angle_map()

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
            r=d["radii"], theta=d["angles"], mode="markers+text",
            marker=dict(size=d["sizes"], color=d["color"], opacity=0.85,
                       line=dict(color="#2d2420", width=1.5)),
            text=d["texts"], textposition="top center",
            textfont=dict(size=9, color="#2d2420"),
            name=core, hovertemplate="<b>%{text}</b><extra></extra>",
        ))
    fig.update_layout(
        polar=dict(
            bgcolor="#fdf6f0",
            radialaxis=dict(visible=False, range=[0, 2.0]),
            angularaxis=dict(
                tickmode="array", tickvals=list(CORE_ANGLES.values()),
                ticktext=list(CORE_ANGLES.keys()),
                tickfont=dict(size=13, color="#7a5c4a"),
                direction="clockwise", rotation=90,
                gridcolor="#e8d5c4", linecolor="#e8d5c4",
            ),
        ),
        paper_bgcolor="#fdf6f0", font=dict(color="#2d2420"),
        title=dict(text=title, font=dict(size=15, color="#2d2420"), x=0.5),
        showlegend=True,
        legend=dict(bgcolor="#fdf6f0", font=dict(color="#7a5c4a"), bordercolor="#e8d5c4", borderwidth=1),
        margin=dict(t=60, b=40, l=60, r=60), height=560,
    )
    return fig


#  Chart 2: Stacked bar 

def make_stacked_bar(sessions, level):
    dates = [s["date"] for s in sessions]
    all_labels = []
    for s in sessions:
        for lbl in get_emotions_at_level(s, level):
            if lbl not in all_labels:
                all_labels.append(lbl)
    fig = go.Figure()
    for lbl in all_labels:
        counts = [get_emotions_at_level(s, level).get(lbl, 0) for s in sessions]
        fig.add_trace(go.Bar(
            name=lbl, x=dates, y=counts,
            marker_color=get_color_for_label(lbl, level),
            hovertemplate=f"<b>{lbl}</b>: %{{y}}<extra></extra>"
        ))
    fig.update_layout(
        barmode="stack", paper_bgcolor="#fdf6f0", plot_bgcolor="#fdf6f0",
        font=dict(color="#2d2420"),
        xaxis=dict(gridcolor="#e8d5c4", color="#7a5c4a"),
        yaxis=dict(gridcolor="#e8d5c4", color="#7a5c4a", title="Dot count"),
        legend=dict(bgcolor="#fdf6f0", bordercolor="#e8d5c4", borderwidth=1),
        height=450, margin=dict(t=30, b=40),
        title=dict(text=f"Emotion distribution ({level})", font=dict(size=14, color="#2d2420"), x=0.5)
    )
    return fig


#  Chart 3: Line trends 

def make_lines(sessions, level):
    dates = [s["date"] for s in sessions]
    all_labels = []
    for s in sessions:
        for lbl in get_emotions_at_level(s, level):
            if lbl not in all_labels:
                all_labels.append(lbl)
    fig = go.Figure()
    for lbl in all_labels:
        counts = [get_emotions_at_level(s, level).get(lbl, 0) for s in sessions]
        fig.add_trace(go.Scatter(
            x=dates, y=counts, name=lbl, mode="lines+markers",
            line=dict(color=get_color_for_label(lbl, level), width=2.5),
            marker=dict(size=8, color=get_color_for_label(lbl, level)),
            hovertemplate=f"<b>{lbl}</b>: %{{y}}<extra></extra>"
        ))
    fig.update_layout(
        paper_bgcolor="#fdf6f0", plot_bgcolor="#fdf6f0", font=dict(color="#2d2420"),
        xaxis=dict(gridcolor="#e8d5c4", color="#7a5c4a"),
        yaxis=dict(gridcolor="#e8d5c4", color="#7a5c4a", title="Dot count"),
        legend=dict(bgcolor="#fdf6f0", bordercolor="#e8d5c4", borderwidth=1),
        height=430, margin=dict(t=30, b=40),
        title=dict(text=f"Emotion trends ({level})", font=dict(size=14, color="#2d2420"), x=0.5)
    )
    return fig


#  Chart 4: Heatmap 

def make_heatmap(sessions, level):
    dates = [s["date"] for s in sessions]
    all_labels = []
    for s in sessions:
        for lbl in get_emotions_at_level(s, level):
            if lbl not in all_labels:
                all_labels.append(lbl)
    matrix = [[get_emotions_at_level(s, level).get(lbl, 0) for s in sessions] for lbl in all_labels]
    fig = go.Figure(go.Heatmap(
        z=matrix, x=dates, y=all_labels,
        colorscale=[[0, "#0d1117"], [0.2, "#1e3a5f"], [0.5, "#e8875a"], [1, "#f0c93a"]],
        hovertemplate="<b>%{y}</b> on %{x}: %{z} dots<extra></extra>",
        showscale=True,
    ))
    fig.update_layout(
        paper_bgcolor="#fdf6f0", plot_bgcolor="#fdf6f0",
        font=dict(color="#2d2420", size=11),
        xaxis=dict(color="#7a5c4a"),
        yaxis=dict(color="#7a5c4a", autorange="reversed"),
        height=max(350, len(all_labels) * 28),
        margin=dict(t=30, b=40, l=160, r=40),
        title=dict(text=f"Emotion heatmap ({level})", font=dict(size=14, color="#2d2420"), x=0.5)
    )
    return fig


#  Chart 5: Radar overlay 

def make_radar(sessions):
    cores = list(CORE_COLORS.keys())
    fig = go.Figure()
    for s in sessions:
        totals = get_core_totals(s)
        values = [totals.get(c, 0) for c in cores] + [totals.get(cores[0], 0)]
        fig.add_trace(go.Scatterpolar(
            r=values, theta=cores + [cores[0]],
            fill="toself", name=s["date"],
            opacity=0.5,
            line=dict(width=2),
        ))
    fig.update_layout(
        polar=dict(
            bgcolor="#fdf6f0",
            radialaxis=dict(visible=True, color="#555", gridcolor="#e8d5c4"),
            angularaxis=dict(color="#7a5c4a", gridcolor="#e8d5c4"),
        ),
        paper_bgcolor="#fdf6f0", font=dict(color="#2d2420"),
        showlegend=True,
        legend=dict(bgcolor="#fdf6f0", font=dict(color="#7a5c4a"), bordercolor="#e8d5c4", borderwidth=1),
        height=520, margin=dict(t=40, b=40),
        title=dict(text="Emotion radar — all sessions overlaid", font=dict(size=14, color="#2d2420"), x=0.5)
    )
    return fig


#  Chart 6: Positive vs Negative ratio 

def make_posneg(sessions):
    dates = [s["date"] for s in sessions]
    pos_pct, neg_pct, attendance = [], [], []
    for s in sessions:
        totals = get_core_totals(s)
        total = s.get("total_dots", 1) or 1
        pos = sum(totals.get(c, 0) for c in POSITIVE)
        neg = sum(totals.get(c, 0) for c in NEGATIVE)
        pos_pct.append(round(pos / total * 100, 1))
        neg_pct.append(round(neg / total * 100, 1))
        attendance.append(total)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=pos_pct, name="Positive %", mode="lines+markers",
        line=dict(color="#e8875a", width=3), marker=dict(size=10),
        hovertemplate="%{y}%<extra>Positive</extra>"))
    fig.add_trace(go.Scatter(x=dates, y=neg_pct, name="Challenging %", mode="lines+markers",
        line=dict(color="#9b6bb5", width=3), marker=dict(size=10),
        hovertemplate="%{y}%<extra>Challenging</extra>"))
    fig.add_trace(go.Bar(x=dates, y=attendance, name="Total dots (attendance)",
        marker_color="rgba(180,160,140,0.25)", yaxis="y2",
        hovertemplate="%{y} dots<extra>Attendance</extra>"))
    fig.update_layout(
        paper_bgcolor="#fdf6f0", plot_bgcolor="#fdf6f0", font=dict(color="#2d2420"),
        xaxis=dict(gridcolor="#e8d5c4", color="#7a5c4a"),
        yaxis=dict(gridcolor="#e8d5c4", color="#7a5c4a", title="% of dots", range=[0, 100]),
        yaxis2=dict(overlaying="y", side="right", color="#b0a090",
                   title="Total dots", showgrid=False),
        legend=dict(bgcolor="#fdf6f0", bordercolor="#e8d5c4", borderwidth=1),
        height=420, margin=dict(t=30, b=40),
        title=dict(text="Positive vs challenging (% of session dots)", font=dict(size=14, color="#2d2420"), x=0.5)
    )
    return fig


#  Chart 7: Bubble timeline 

def make_bubble(sessions, level):
    rows = []
    for s in sessions:
        agg = get_emotions_at_level(s, level)
        for lbl, cnt in agg.items():
            if cnt > 0:
                rows.append({"date": s["date"], "emotion": lbl, "count": cnt,
                            "color": get_color_for_label(lbl, level)})
    if not rows:
        return go.Figure()
    # normalize bubble sizes relative to global max so they never overlap
    max_count = max(r["count"] for r in rows) if rows else 1
    MIN_SIZE, MAX_SIZE = 8, 60

    fig = go.Figure()
    emotions = list({r["emotion"] for r in rows})
    for lbl in emotions:
        pts = [r for r in rows if r["emotion"] == lbl]
        counts = [p["count"] for p in pts]
        sizes = [MIN_SIZE + (c / max_count) * (MAX_SIZE - MIN_SIZE) for c in counts]
        fig.add_trace(go.Scatter(
            x=[p["date"] for p in pts],
            y=[p["emotion"] for p in pts],
            mode="markers",
            marker=dict(
                size=sizes,
                color=pts[0]["color"], opacity=0.8,
                line=dict(color="#2d2420", width=1)
            ),
            customdata=counts,
            name=lbl,
            hovertemplate="<b>%{y}</b> on %{x}<br>%{customdata} dots<extra></extra>",
            showlegend=False
        ))
    fig.update_layout(
        paper_bgcolor="#fdf6f0", plot_bgcolor="#fdf6f0", font=dict(color="#2d2420"),
        xaxis=dict(gridcolor="#e8d5c4", color="#7a5c4a", title="Session"),
        yaxis=dict(gridcolor="#e8d5c4", color="#7a5c4a", autorange="reversed"),
        height=max(400, len(emotions) * 28),
        margin=dict(t=30, b=40, l=160, r=40),
        title=dict(text=f"Bubble timeline ({level})", font=dict(size=14, color="#2d2420"), x=0.5)
    )
    return fig


#  Chart 8: Word cloud 

def make_wordcloud(session, level):
    try:
        from wordcloud import WordCloud
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        agg = get_emotions_at_level(session, level)
        if not agg:
            return None
        wc = WordCloud(
            width=800, height=400, background_color="#fdf6f0",
            colormap="YlOrRd", prefer_horizontal=0.8,
            max_words=60
        ).generate_from_frequencies(agg)
        fig, ax = plt.subplots(figsize=(10, 5), facecolor="#fdf6f0")
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#fdf6f0")
        plt.close(fig)
        buf.seek(0)
        return buf
    except ImportError:
        return None


#  Photo timelapse GIF 

def parse_date_from_name(name):
    for fmt in ("%d_%m_%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(name, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return name

def make_photo_gif(uploaded_files, duration_ms=1200) -> bytes:
    frames = []
    file_list = sorted(uploaded_files, key=lambda f: parse_date_from_name(f.name.rsplit(".", 1)[0]))
    for f in file_list:
        img = Image.open(f).convert("RGB")
        img = img.resize((800, 800), Image.LANCZOS)
        # add date label
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        date_label = parse_date_from_name(f.name.rsplit(".", 1)[0])
        draw.rectangle([0, 0, 800, 40], fill=(13, 17, 23))
        draw.text((10, 8), date_label, fill=(220, 220, 220))
        frames.append(img)
    buf = io.BytesIO()
    frames[0].save(buf, format="GIF", save_all=True,
                  append_images=frames[1:], duration=duration_ms, loop=0)
    buf.seek(0)
    return buf.read()


#  Main page 

def show():
    inject_css()
    st.markdown('<h2 style="margin-bottom:4px">Analyse</h2>', unsafe_allow_html=True)
    st.caption("Upload your save file to explore the emotional journey of your cohort.")

    uploaded = st.file_uploader("Upload feelmap_sessions.json", type=["json"],
                                label_visibility="collapsed")
    sessions = []
    if uploaded:
        try:
            data = json.load(uploaded)
            sessions = sessions_from_json(data)
            st.success(f" {len(sessions)} sessions loaded")
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

    #  Granularity toggle 
    level = st.radio(
        "Granularity",
        ["Core", "Sub", "Sub-sub"],
        horizontal=True,
        help="Choose which level of the emotion tree to display. Applies to all charts except the polar wheel and radar."
    )

    st.divider()

    #  Viz tabs 
    tabs = st.tabs(["Polar wheel", "Radar", "Positive vs negative",
                    "Stacked bar", "Lines", "Heatmap",
                    "Bubbles", "Word cloud"])

    with tabs[0]:
        dates = [s["date"] for s in sessions]
        idx = st.select_slider("Session", options=list(range(len(dates))),
                               format_func=lambda i: dates[i], key="polar_slider")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(make_polar(sessions[idx], sessions[idx]["date"]),
                           use_container_width=True)
        with col2:
            st.markdown("##### Breakdown")
            totals = get_core_totals(sessions[idx])
            total_dots = sessions[idx].get("total_dots", 1)
            for core, cnt in sorted(totals.items(), key=lambda x: -x[1]):
                if cnt > 0:
                    pct = int(cnt / total_dots * 100)
                    st.markdown(f"<span style='color:{CORE_COLORS[core]}'></span> **{core}** — {cnt} ({pct}%)",
                               unsafe_allow_html=True)

    with tabs[1]:
        st.plotly_chart(make_radar(sessions), use_container_width=True)

    with tabs[2]:
        st.plotly_chart(make_posneg(sessions), use_container_width=True)

    with tabs[3]:
        st.plotly_chart(make_stacked_bar(sessions, level), use_container_width=True)

    with tabs[4]:
        st.plotly_chart(make_lines(sessions, level), use_container_width=True)

    with tabs[5]:
        st.plotly_chart(make_heatmap(sessions, level), use_container_width=True)

    with tabs[6]:
        st.plotly_chart(make_bubble(sessions, level), use_container_width=True)

    with tabs[7]:
        dates = [s["date"] for s in sessions]
        idx = st.select_slider("Session", options=list(range(len(dates))),
                               format_func=lambda i: dates[i], key="wc_slider")
        buf = make_wordcloud(sessions[idx], level)
        if buf:
            st.image(buf, use_container_width=True)
        else:
            st.warning("wordcloud package not installed — run `pip install wordcloud`")

    st.divider()

    #  Export 
    st.markdown("#### Export")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Sticker by sticker**")
        st.caption("Emotions appear one by one, spotlight on the active one.")
        frame_ms = st.slider("Frame speed (ms)", 200, 800, 400, 100, key="sticker_speed")
        pause_ms = st.slider("Pause between weeks (ms)", 800, 3000, 1800, 200, key="sticker_pause")
        if st.button("Generate sticker GIF", use_container_width=True):
            with st.spinner("Rendering frames — this takes a moment..."):
                try:
                    from utils.export import make_gif_sticker
                    gif = make_gif_sticker(sessions, frame_ms=frame_ms, pause_ms=pause_ms)
                    st.download_button(" Download sticker GIF", data=gif,
                        file_name="feelmap_sticker.gif", mime="image/gif",
                        use_container_width=True, type="primary")
                except Exception as e:
                    st.error(f"Failed: {e}")

    with col2:
        st.markdown("**Week timelapse**")
        st.caption("One frame per session — best for comparing weeks side by side.")
        speed = st.slider("Frame duration (ms)", 600, 3000, 1200, 200, key="gif_speed")
        if st.button("Generate timelapse GIF", use_container_width=True):
            with st.spinner("Rendering..."):
                try:
                    from utils.export import make_gif_timelapse
                    gif = make_gif_timelapse(sessions, duration_ms=speed)
                    st.download_button(" Download timelapse GIF", data=gif,
                        file_name="feelmap_timelapse.gif", mime="image/gif",
                        use_container_width=True, type="primary")
                except Exception as e:
                    st.error(f"Failed: {e}")

    with col3:
        st.markdown("**Photo GIF** — original wheel photos")
        photos = st.file_uploader("Upload wheel photos (dd_mm_yyyy.png)",
            type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="photo_upload")
        photo_speed = st.slider("Frame duration (ms)", 600, 3000, 1500, 200, key="photo_speed")
        if photos and st.button("Generate photo GIF", use_container_width=True):
            with st.spinner("Assembling..."):
                try:
                    gif = make_photo_gif(photos, duration_ms=photo_speed)
                    st.download_button(" Download photo GIF", data=gif,
                        file_name="feelmap_photos.gif", mime="image/gif",
                        use_container_width=True, type="primary")
                except Exception as e:
                    st.error(f"Failed: {e}")

    with col3:
        st.markdown("**ZIP** — all polar charts as PNG")
        if st.button("Generate ZIP", use_container_width=True):
            with st.spinner("Rendering..."):
                try:
                    from utils.export import make_zip
                    z = make_zip(sessions)
                    st.download_button(" Download ZIP", data=z,
                        file_name="feelmap_export.zip", mime="application/zip",
                        use_container_width=True, type="primary")
                except Exception as e:
                    st.error(f"Failed: {e}")