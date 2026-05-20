import streamlit as st
import plotly.graph_objects as go
import json
from utils.tree_state import get_active_tree, get_core_colors
from utils.vision import sessions_from_json, load_sessions_from_state


def get_all_emotions(tree):
    """Flat list of all (core, sub, sub_sub) combos in the tree."""
    result = []
    for core, data in tree.items():
        result.append((core, None, None))
        for sub, leaves in data["subs"].items():
            result.append((core, sub, None))
            for leaf in leaves:
                result.append((core, sub, leaf))
    return result


def get_label(core, sub, sub_sub):
    return sub_sub or sub or core


def count_emotion_appearances(sessions, core, sub, sub_sub):
    """How many sessions had this emotion with at least 1 dot."""
    count = 0
    for s in sessions:
        for e in s.get("emotions", []):
            if e.get("core") == core and e.get("sub") == sub and e.get("sub_sub") == sub_sub:
                if e.get("count", 0) > 0:
                    count += 1
                    break
    return count


def total_dots_for_emotion(sessions, core, sub, sub_sub):
    total = 0
    for s in sessions:
        for e in s.get("emotions", []):
            if e.get("core") == core and e.get("sub") == sub and e.get("sub_sub") == sub_sub:
                total += e.get("count", 0)
    return total


def week_over_week_shifts(sessions):
    """Return list of (date_pair, emotion, change) for biggest shifts."""
    shifts = []
    for i in range(1, len(sessions)):
        prev, curr = sessions[i-1], sessions[i]
        prev_map = {(e["core"], e.get("sub"), e.get("sub_sub")): e.get("count", 0)
                   for e in prev.get("emotions", [])}
        curr_map = {(e["core"], e.get("sub"), e.get("sub_sub")): e.get("count", 0)
                   for e in curr.get("emotions", [])}
        all_keys = set(prev_map) | set(curr_map)
        for key in all_keys:
            delta = curr_map.get(key, 0) - prev_map.get(key, 0)
            if delta != 0:
                shifts.append({
                    "from": prev["date"], "to": curr["date"],
                    "emotion": get_label(*key),
                    "core": key[0], "delta": delta
                })
    return sorted(shifts, key=lambda x: abs(x["delta"]), reverse=True)


def show():
    st.markdown('<h2 style="margin-bottom:4px">🔍 Analyse</h2>', unsafe_allow_html=True)
    st.caption("Deeper insights into emotion patterns across the semester.")

    tree = get_active_tree()
    colors = get_core_colors(tree)

    # ── Load data ────────────────────────────────────────────────────────────
    uploaded = st.file_uploader("Upload feelmap_sessions.json", type=["json"],
                                label_visibility="collapsed")
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

    all_emotions = get_all_emotions(tree)
    n_sessions = len(sessions)

    # ── Insight 1: Never chosen emotions ─────────────────────────────────────
    st.markdown("### 🚫 Emotions never chosen")
    st.caption("These emotions appeared zero times across all sessions — candidates for removal from the wheel.")

    never = []
    for core, sub, sub_sub in all_emotions:
        if count_emotion_appearances(sessions, core, sub, sub_sub) == 0:
            never.append({
                "Emotion": get_label(core, sub, sub_sub),
                "Level": "Core" if sub is None else ("Sub" if sub_sub is None else "Sub-sub"),
                "Core category": core
            })

    if never:
        # group by core
        by_core = {}
        for n in never:
            by_core.setdefault(n["Core category"], []).append(n["Emotion"])

        cols = st.columns(min(len(by_core), 4))
        for i, (core, emotions) in enumerate(by_core.items()):
            with cols[i % len(cols)]:
                color = colors.get(core, "#888")
                st.markdown(f"<span style='color:{color}'>●</span> **{core}**",
                           unsafe_allow_html=True)
                for em in emotions:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;· {em}", unsafe_allow_html=True)
    else:
        st.success("Every emotion in the wheel was chosen at least once!")

    st.divider()

    # ── Insight 2: Rarely chosen ─────────────────────────────────────────────
    st.markdown("### 📉 Rarely chosen emotions")
    st.caption(f"Emotions chosen in only 1 out of {n_sessions} sessions.")

    rare_threshold = max(1, n_sessions // 4)
    rare = []
    for core, sub, sub_sub in all_emotions:
        appearances = count_emotion_appearances(sessions, core, sub, sub_sub)
        if 0 < appearances <= rare_threshold:
            rare.append({
                "Emotion": get_label(core, sub, sub_sub),
                "Sessions": f"{appearances}/{n_sessions}",
                "Core": core,
                "appearances": appearances
            })

    if rare:
        rare_sorted = sorted(rare, key=lambda x: x["appearances"])
        for r in rare_sorted[:15]:
            color = colors.get(r["Core"], "#888")
            st.markdown(
                f"<span style='color:{color}'>●</span> **{r['Emotion']}** — chosen {r['Sessions']} sessions",
                unsafe_allow_html=True)
    else:
        st.info("No rarely chosen emotions found.")

    st.divider()

    # ── Insight 3: Most dominant emotions ────────────────────────────────────
    st.markdown("### 🏆 Most dominant emotions")
    st.caption("Emotions with the highest total dot count across the semester.")

    dominance = []
    for core, sub, sub_sub in all_emotions:
        total = total_dots_for_emotion(sessions, core, sub, sub_sub)
        if total > 0:
            dominance.append({
                "label": get_label(core, sub, sub_sub),
                "core": core, "total": total
            })
    dominance = sorted(dominance, key=lambda x: -x["total"])[:15]

    if dominance:
        fig = go.Figure(go.Bar(
            x=[d["label"] for d in dominance],
            y=[d["total"] for d in dominance],
            marker_color=[colors.get(d["core"], "#888") for d in dominance],
            hovertemplate="<b>%{x}</b>: %{y} dots total<extra></extra>"
        ))
        fig.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            font=dict(color="white"),
            xaxis=dict(gridcolor="#1e1e2e", color="#aaa", tickangle=-30),
            yaxis=dict(gridcolor="#1e1e2e", color="#aaa", title="Total dots"),
            height=380, margin=dict(t=20, b=80),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Insight 4: Week-over-week biggest shifts ──────────────────────────────
    st.markdown("### 📈 Biggest week-over-week shifts")
    st.caption("Emotions that changed the most between consecutive sessions.")

    shifts = week_over_week_shifts(sessions)
    if shifts:
        top_shifts = shifts[:12]
        for sh in top_shifts:
            color = colors.get(sh["core"], "#888")
            arrow = "⬆️" if sh["delta"] > 0 else "⬇️"
            st.markdown(
                f"<span style='color:{color}'>●</span> **{sh['emotion']}** {arrow} "
                f"`{'+' if sh['delta']>0 else ''}{sh['delta']}` dots &nbsp; "
                f"<span style='color:#555'>{sh['from']} → {sh['to']}</span>",
                unsafe_allow_html=True)

    st.divider()

    # ── Insight 5: Emotional balance per session ──────────────────────────────
    st.markdown("### ⚖️ Positive vs challenging ratio")
    st.caption("How the emotional balance shifted each week.")

    POSITIVE = {"Happy", "Surprised"}
    dates = [s["date"] for s in sessions]
    pos_pct, neg_pct = [], []
    for s in sessions:
        total = s.get("total_dots", 1) or 1
        pos = sum(e.get("count", 0) for e in s.get("emotions", [])
                 if e.get("core") in POSITIVE)
        pos_pct.append(round(pos / total * 100))
        neg_pct.append(100 - round(pos / total * 100))

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=dates, y=pos_pct, name="Positive",
                         marker_color="#e8875a",
                         hovertemplate="%{y}% positive<extra></extra>"))
    fig2.add_trace(go.Bar(x=dates, y=neg_pct, name="Challenging",
                         marker_color="#9b6bb5",
                         hovertemplate="%{y}% challenging<extra></extra>"))
    fig2.update_layout(
        barmode="stack",
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(color="white"),
        xaxis=dict(gridcolor="#1e1e2e", color="#aaa"),
        yaxis=dict(gridcolor="#1e1e2e", color="#aaa", title="%", range=[0, 100]),
        legend=dict(bgcolor="#0d1117", bordercolor="#333", borderwidth=1),
        height=350, margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Insight 6: Consistency — emotions present every week ─────────────────
    st.markdown("### 🔁 Always present")
    st.caption("Emotions chosen every single session — the constants of the semester.")

    always = []
    for core, sub, sub_sub in all_emotions:
        if count_emotion_appearances(sessions, core, sub, sub_sub) == n_sessions:
            always.append((get_label(core, sub, sub_sub), core))

    if always:
        for label, core in always:
            color = colors.get(core, "#888")
            st.markdown(f"<span style='color:{color}'>●</span> **{label}**",
                       unsafe_allow_html=True)
    else:
        st.info("No emotion was chosen every single session.")