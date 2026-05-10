import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from utils.emotion_tree import EMOTION_TREE
from utils.vision import save_session, load_all_sessions


def parse_date_from_filename(filename: str):
    for fmt in ("%d_%m_%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(filename, fmt)
            return dt.strftime("%Y-%m-%d"), dt.strftime("%d %B %Y")
        except ValueError:
            continue
    return None, f"Could not parse date from `{filename}`"


def show():
    st.markdown('<h2 style="margin-bottom:4px">📍 Annotate</h2>', unsafe_allow_html=True)
    st.caption("Upload a wheel photo, mark the dots, save the session.")

    uploaded_file = st.file_uploader(
        "Upload wheel image",
        type=["png", "jpg", "jpeg"],
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

        with col_form:
            st.markdown("#### Mark the dots")
            st.caption("Enter the count for each emotion that has a sticker. Leave at 0 if none.")

            counts = {}

            for core, core_data in EMOTION_TREE.items():
                with st.expander(f"● {core}", expanded=False):
                    for sub, leaves in core_data["subs"].items():
                        st.markdown(f"**{sub}**")

                        c = st.number_input(
                            f"{sub} (direct hit)",
                            min_value=0, max_value=10, value=0, step=1,
                            key=f"n_{core}_{sub}_direct",
                            label_visibility="collapsed"
                        )
                        if c > 0:
                            counts[(core, sub, None)] = c

                        if leaves:
                            leaf_cols = st.columns(len(leaves))
                            for i, leaf in enumerate(leaves):
                                with leaf_cols[i]:
                                    lc = st.number_input(
                                        leaf, min_value=0, max_value=10,
                                        value=0, step=1,
                                        key=f"n_{core}_{sub}_{leaf}"
                                    )
                                    if lc > 0:
                                        counts[(core, sub, leaf)] = lc
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
                    save_session(session)
                    st.success(f"✅ Saved — {total} dots for {date_str}")
                    st.balloons()

    # --- Saved sessions + export ---
    st.divider()
    sessions = load_all_sessions()

    if not sessions:
        st.info("No sessions saved yet.")
        return

    # Export button at the top, next to the header
    col_hdr, col_export = st.columns([2, 1])
    with col_hdr:
        st.markdown(f"#### Saved sessions ({len(sessions)})")
    with col_export:
        export_data = json.dumps({"sessions": sessions}, indent=2)
        st.download_button(
            label=f"⬇️ Export all ({len(sessions)} weeks)",
            data=export_data,
            file_name="feelmap_sessions.json",
            mime="application/json",
            use_container_width=True,
            type="primary"
        )

    for s in sessions:
        with st.expander(f"📅 {s['date']} — {s.get('total_dots', '?')} dots"):
            st.json(s, expanded=False)
            if st.button("🗑 Delete", key=f"del_{s['date']}"):
                Path(f"sessions/{s['date']}.json").unlink(missing_ok=True)
                st.rerun()