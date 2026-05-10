import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from utils.emotion_tree import EMOTION_TREE
from utils.vision import (
    save_session_to_state, load_sessions_from_state,
    delete_session_from_state, sessions_to_json, sessions_from_json
)


def parse_date_from_filename(filename: str):
    for fmt in ("%d_%m_%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(filename, fmt)
            return dt.strftime("%Y-%m-%d"), dt.strftime("%d %B %Y")
        except ValueError:
            continue
    return None, f"Could not parse date from `{filename}`"


def session_to_counts(session: dict) -> dict:
    """Convert a saved session's emotions list back into a counts dict keyed by (core, sub, leaf)."""
    counts = {}
    for e in session.get("emotions", []):
        key = (e.get("core"), e.get("sub"), e.get("sub_sub"))
        counts[key] = e.get("count", 0)
    return counts


def show():
    st.markdown('<h2 style="margin-bottom:4px">📍 Annotate</h2>', unsafe_allow_html=True)

    # ── Step 1: Load save file ───────────────────────────────────────────────
    st.markdown("**Step 1 — Load your previous data** *(skip if starting fresh)*")
    uploaded_save = st.file_uploader(
        "Upload feelmap_sessions.json",
        type=["json"],
        key="load_save",
        label_visibility="collapsed"
    )
    if uploaded_save:
        try:
            data = json.load(uploaded_save)
            sessions = sessions_from_json(data)
            st.session_state["sessions"] = {s["date"]: s for s in sessions}
            st.success(f"✅ {len(sessions)} sessions loaded — scroll down to see them.")
        except Exception as e:
            st.error(f"Could not read file: {e}")

    st.divider()

    # ── Step 2: Annotate new session ─────────────────────────────────────────
    st.markdown("**Step 2 — Annotate a new session**")
    uploaded_file = st.file_uploader(
        "Upload wheel image",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed",
        help="Name the file dd_mm_yyyy.png for automatic date detection."
    )

    if uploaded_file:
        filename = Path(uploaded_file.name).stem
        date_str, display = parse_date_from_filename(filename)

        col_img, col_form = st.columns([1.1, 0.9], gap="large")

        with col_img:
            st.image(uploaded_file, use_container_width=True)
            if date_str:
                verified = st.text_input(
                    "📅 Session date",
                    value=date_str,
                    help="Auto-detected from filename. Edit if needed (YYYY-MM-DD)."
                )
                date_str = verified.strip() or date_str
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    st.caption(f"✅ {dt.strftime('%d %B %Y')}")
                except ValueError:
                    st.error("Use format YYYY-MM-DD")
                    return
            else:
                st.warning(display)
                date_str = st.text_input("Enter date manually", placeholder="2026-03-04")
                if not date_str:
                    return

            # check if session already exists and pre-fill
            existing_sessions = st.session_state.get("sessions", {})
            existing_counts = {}
            if date_str in existing_sessions:
                existing_counts = session_to_counts(existing_sessions[date_str])
                st.info(f"📋 Loaded existing annotation for {date_str} — counters pre-filled. Edit and save to update.")

        with col_form:
            st.markdown("#### Mark the dots")
            st.caption("Open each emotion group, enter the count for emotions that have stickers.")

            counts = {}

            for core, core_data in EMOTION_TREE.items():
                with st.expander(f"● {core}", expanded=False):

                    # ── Root level: dot directly on the core emotion ─────────
                    root_key = (core, None, None)
                    root_default = existing_counts.get(root_key, 0)
                    rc = st.number_input(
                        f"On '{core}' directly",
                        min_value=0, max_value=10,
                        value=root_default, step=1,
                        key=f"n_{core}_root"
                    )
                    if rc > 0:
                        counts[root_key] = rc

                    st.divider()

                    # ── Sub emotions ─────────────────────────────────────────
                    for sub, leaves in core_data["subs"].items():
                        st.markdown(f"**{sub}**")

                        sub_key = (core, sub, None)
                        sub_default = existing_counts.get(sub_key, 0)
                        c = st.number_input(
                            f"On '{sub}' directly",
                            min_value=0, max_value=10,
                            value=sub_default, step=1,
                            key=f"n_{core}_{sub}_direct",
                            label_visibility="collapsed"
                        )
                        if c > 0:
                            counts[sub_key] = c

                        if leaves:
                            leaf_cols = st.columns(len(leaves))
                            for i, leaf in enumerate(leaves):
                                with leaf_cols[i]:
                                    leaf_key = (core, sub, leaf)
                                    leaf_default = existing_counts.get(leaf_key, 0)
                                    lc = st.number_input(
                                        leaf,
                                        min_value=0, max_value=10,
                                        value=leaf_default, step=1,
                                        key=f"n_{core}_{sub}_{leaf}"
                                    )
                                    if lc > 0:
                                        counts[leaf_key] = lc

                        st.divider()

            total = sum(counts.values())
            st.markdown(f"**Total dots marked: `{total}`**")

            if st.button("💾 Save session", type="primary", use_container_width=True):
                if total == 0:
                    st.warning("No dots marked yet!")
                else:
                    emotions = [
                        {"core": k[0], "sub": k[1], "sub_sub": k[2], "count": v}
                        for k, v in counts.items()
                    ]
                    session = {"date": date_str, "total_dots": total, "emotions": emotions}
                    save_session_to_state(session)
                    st.success(f"✅ Saved — {total} dots for {date_str}")
                    st.balloons()

    # ── Step 3: Export ───────────────────────────────────────────────────────
    st.divider()
    sessions = load_sessions_from_state()

    if not sessions:
        st.info("No sessions yet — annotate a wheel above to get started.")
        return

    col_hdr, col_export = st.columns([2, 1])
    with col_hdr:
        st.markdown(f"**Step 3 — Export your data** ({len(sessions)} sessions saved)")
    with col_export:
        st.download_button(
            label="⬇️ Export save file",
            data=sessions_to_json(sessions),
            file_name="feelmap_sessions.json",
            mime="application/json",
            use_container_width=True,
            type="primary",
            help="Keep this file on your desktop and upload it next time to continue."
        )

    st.caption("⚠️ Always export before closing the app — your data is not saved automatically.")

    st.divider()
    st.markdown(f"#### Sessions ({len(sessions)})")
    for s in sessions:
        with st.expander(f"📅 {s['date']} — {s.get('total_dots', '?')} dots"):
            st.json(s, expanded=False)
            if st.button("🗑 Delete", key=f"del_{s['date']}"):
                delete_session_from_state(s["date"])
                st.rerun()