import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.vision import load_all_sessions


EMOTION_ANGLES = {
    "Happy": {
        "angle": 180,
        "color": "#f9c74f",
        "subs": {
            "Playful":    {"angle": 210, "subs": {"Aroused": 225, "Cheeky": 220}},
            "Content":    {"angle": 195, "subs": {"Joyful": 202, "Free": 208}},
            "Interested": {"angle": 185, "subs": {"Curious": 188, "Inquisitive": 182}},
            "Proud":      {"angle": 175, "subs": {"Successful": 172, "Confident": 178}},
            "Accepted":   {"angle": 165, "subs": {"Respected": 162, "Valued": 168}},
            "Powerful":   {"angle": 158, "subs": {"Courageous": 155, "Creative": 161}},
            "Peaceful":   {"angle": 150, "subs": {"Loving": 147, "Thankful": 153}},
            "Trusting":   {"angle": 143, "subs": {"Sensitive": 140, "Intimate": 146}},
            "Optimistic": {"angle": 135, "subs": {"Hopeful": 132, "Inspired": 138}},
        }
    },
    "Surprised": {
        "angle": 270,
        "color": "#90e0ef",
        "subs": {
            "Startled":   {"angle": 280, "subs": {"Confused": 285, "Amazed": 275}},
            "Confused":   {"angle": 265, "subs": {"Perplexed": 268, "Disillusioned": 262}},
            "Shocked":    {"angle": 255, "subs": {"Dismayed": 258, "Speechless": 252}},
            "Excited":    {"angle": 290, "subs": {"Energetic": 295, "Eager": 288}},
        }
    },
    "Bad": {
        "angle": 315,
        "color": "#9b5de5",
        "subs": {
            "Tired":      {"angle": 330, "subs": {"Sleepy": 335, "Unfocused": 328}},
            "Stressed":   {"angle": 320, "subs": {"Overwhelmed": 325, "Out of control": 318}},
            "Busy":       {"angle": 312, "subs": {"Pressured": 315, "Rushed": 308}},
            "Bored":      {"angle": 303, "subs": {"Indifferent": 306, "Apathetic": 300}},
        }
    },
    "Fearful": {
        "angle": 350,
        "color": "#c77dff",
        "subs": {
            "Scared":     {"angle": 360, "subs": {"Helpless": 365, "Frightened": 358}},
            "Anxious":    {"angle": 350, "subs": {"Overwhelmed": 353, "Worried": 347}},
            "Insecure":   {"angle": 342, "subs": {"Inadequate": 345, "Inferior": 339}},
            "Weak":       {"angle": 335, "subs": {"Worthless": 338, "Insignificant": 332}},
        }
    },
    "Angry": {
        "angle": 30,
        "color": "#f94144",
        "subs": {
            "Let down":   {"angle": 20, "subs": {"Betrayed": 17, "Resentful": 22}},
            "Humiliated": {"angle": 30, "subs": {"Disrespected": 27, "Ridiculed": 33}},
            "Bitter":     {"angle": 40, "subs": {"Indignant": 37, "Violated": 43}},
            "Mad":        {"angle": 50, "subs": {"Furious": 47, "Jealous": 53}},
            "Aggressive": {"angle": 60, "subs": {"Provoked": 57, "Hostile": 63}},
            "Frustrated": {"angle": 70, "subs": {"Infuriated": 67, "Annoyed": 73}},
            "Distant":    {"angle": 80, "subs": {"Withdrawn": 77, "Numb": 83}},
            "Critical":   {"angle": 88, "subs": {"Skeptical": 85, "Dismissive": 91}},
        }
    },
    "Disgusted": {
        "angle": 110,
        "color": "#43aa8b",
        "subs": {
            "Disapproving": {"angle": 100, "subs": {"Judgmental": 97, "Embarrassed": 103}},
            "Disappointed": {"angle": 110, "subs": {"Appalled": 107, "Revolted": 113}},
            "Awful":        {"angle": 120, "subs": {"Nauseated": 117, "Detestable": 123}},
            "Repelled":     {"angle": 130, "subs": {"Horrified": 127, "Hesitant": 133}},
        }
    },
    "Sad": {
        "angle": 90,
        "color": "#4361ee",
        "subs": {
            "Hurt":        {"angle": 82, "subs": {"Embarrassed": 79, "Disappointed": 85}},
            "Depressed":   {"angle": 90, "subs": {"Inferior": 87, "Empty": 93}},
            "Guilty":      {"angle": 98, "subs": {"Remorseful": 95, "Ashamed": 101}},
            "Despair":     {"angle": 106, "subs": {"Powerless": 103, "Grief": 109}},
            "Vulnerable":  {"angle": 75, "subs": {"Fragile": 72, "Victimised": 78}},
            "Lonely":      {"angle": 67, "subs": {"Isolated": 64, "Abandoned": 70}},
        }
    },
}


def get_all_emotion_points():
    points = []
    for core, core_data in EMOTION_ANGLES.items():
        points.append({
            "label": core, "core": core, "sub": None, "sub_sub": None,
            "angle": core_data["angle"], "radius": 0.33, "color": core_data["color"]
        })
        for sub, sub_data in core_data["subs"].items():
            points.append({
                "label": sub, "core": core, "sub": sub, "sub_sub": None,
                "angle": sub_data["angle"], "radius": 0.66, "color": core_data["color"]
            })
            for sub_sub, angle in sub_data["subs"].items():
                points.append({
                    "label": sub_sub, "core": core, "sub": sub, "sub_sub": sub_sub,
                    "angle": angle, "radius": 1.0, "color": core_data["color"]
                })
    return points


def find_emotion_point(core, sub, sub_sub, all_points):
    for p in all_points:
        if p["core"] == core and p["sub"] == sub and p["sub_sub"] == sub_sub:
            return p
        if sub_sub and p["core"] == core and p["sub"] == sub and p["label"] == sub_sub:
            return p
    for p in all_points:
        if sub and p["core"] == core and p["label"] == sub:
            return p
    for p in all_points:
        if p["core"] == core and p["sub"] is None:
            return p
    return None


def session_to_polar(session, all_points):
    rows = []
    for e in session["emotions"]:
        pt = find_emotion_point(e.get("core"), e.get("sub"), e.get("sub_sub"), all_points)
        if pt:
            rows.append({
                "angle": pt["angle"],
                "radius": pt["radius"] * e.get("count", 1),
                "count": e.get("count", 1),
                "label": pt["label"],
                "core": pt["core"],
                "color": pt["color"],
            })
    return rows


def make_polar_figure(rows, date_str, all_points):
    fig = go.Figure()

    core_groups = {}
    for row in rows:
        core = row["core"]
        if core not in core_groups:
            core_groups[core] = {"angles": [], "radii": [], "colors": [], "labels": []}
        core_groups[core]["angles"].append(row["angle"])
        core_groups[core]["radii"].append(row["radius"])
        core_groups[core]["colors"].append(row["color"])
        core_groups[core]["labels"].append(f"{row['label']} ({row['count']})")

    for core, data in core_groups.items():
        fig.add_trace(go.Scatterpolar(
            r=data["radii"],
            theta=data["angles"],
            mode="markers+text",
            marker=dict(size=[r * 18 + 6 for r in data["radii"]], color=data["colors"], opacity=0.85),
            text=data["labels"],
            textposition="top center",
            textfont=dict(size=9, color="white"),
            name=core,
            hovertemplate="<b>%{text}</b><extra></extra>",
        ))

    fig.update_layout(
        polar=dict(
            bgcolor="#0d1117",
            radialaxis=dict(visible=False, range=[0, 1.5]),
            angularaxis=dict(
                tickmode="array",
                tickvals=[d["angle"] for d in EMOTION_ANGLES.values()],
                ticktext=list(EMOTION_ANGLES.keys()),
                tickfont=dict(size=12, color="#aaaaaa"),
                direction="clockwise",
                rotation=90,
                gridcolor="#222",
                linecolor="#333",
            ),
        ),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="white"),
        title=dict(text=f"Session — {date_str}", font=dict(size=16, color="#e0e0e0"), x=0.5),
        showlegend=True,
        legend=dict(bgcolor="#0d1117", font=dict(color="#ccc"), bordercolor="#333", borderwidth=1),
        margin=dict(t=60, b=40, l=40, r=40),
        height=580,
    )
    return fig


def show():
    st.title("📊 Visualize")
    st.caption("Explore the emotional journey of your cohort across the semester.")

    sessions = load_all_sessions()

    if not sessions:
        st.info("No sessions yet — upload and process some wheel photos first!")
        return

    all_points = get_all_emotion_points()

    st.divider()
    mode = st.radio("Mode", ["Single session", "Timelapse"], horizontal=True)

    if mode == "Single session":
        dates = [s["date"] for s in sessions]
        selected = st.select_slider("Select session", options=dates)
        session = next(s for s in sessions if s["date"] == selected)
        rows = session_to_polar(session, all_points)
        if rows:
            fig = make_polar_figure(rows, selected, all_points)
            st.plotly_chart(fig, use_container_width=True)
            _show_summary(session)
        else:
            st.warning("No matchable emotions found for this session.")

    elif mode == "Timelapse":
        st.info("Use the slider to animate through the weeks.")

        frames = []
        for s in sessions:
            rows = session_to_polar(s, all_points)
            if rows:
                frames.append((s["date"], rows))

        if not frames:
            st.warning("No sessions with matchable emotions found.")
            return

        idx = st.slider("Week", 0, len(frames) - 1, 0, format=f"%d")
        date_str, rows = frames[idx]
        fig = make_polar_figure(rows, date_str, all_points)
        st.plotly_chart(fig, use_container_width=True)

        st.caption(f"Session {idx + 1} of {len(frames)} — {date_str}")
        _show_summary(next(s for s in sessions if s["date"] == date_str))

    st.divider()
    _show_core_evolution(sessions, all_points)


def _show_summary(session):
    total = session.get("total_dots", 0)
    emotions = session.get("emotions", [])
    core_counts = {}
    for e in emotions:
        c = e.get("core", "Unknown")
        core_counts[c] = core_counts.get(c, 0) + e.get("count", 0)

    cols = st.columns(len(core_counts) + 1)
    cols[0].metric("Total dots", total)
    for i, (core, count) in enumerate(sorted(core_counts.items(), key=lambda x: -x[1])):
        cols[i + 1].metric(core, count)


def _show_core_evolution(sessions, all_points):
    st.subheader("Core emotion evolution")
    st.caption("How the balance of core emotions shifted across the semester.")

    core_names = list(EMOTION_ANGLES.keys())
    dates = [s["date"] for s in sessions]
    data = {c: [] for c in core_names}

    for s in sessions:
        counts = {c: 0 for c in core_names}
        for e in s.get("emotions", []):
            c = e.get("core")
            if c in counts:
                counts[c] += e.get("count", 0)
        for c in core_names:
            data[c].append(counts[c])

    fig = go.Figure()
    for core in core_names:
        color = EMOTION_ANGLES[core]["color"]
        fig.add_trace(go.Scatter(
            x=dates, y=data[core],
            name=core,
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=7, color=color),
        ))

    fig.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="white"),
        xaxis=dict(gridcolor="#222", color="#aaa"),
        yaxis=dict(gridcolor="#222", color="#aaa", title="Dot count"),
        legend=dict(bgcolor="#0d1117", bordercolor="#333", borderwidth=1),
        height=350,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
