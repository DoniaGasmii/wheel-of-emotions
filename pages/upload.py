import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from utils.vision import extract_emotions, save_session, load_all_sessions


def parse_date_from_filename(filename: str) -> tuple:
    """
    Try to parse date from filename stem.
    Supports: dd.mm.yyyy → returns (YYYY-MM-DD, human label)
    Falls back to YYYY-MM-DD format too.
    Returns (None, error_msg) if unparseable.
    """
    try:
        dt = datetime.strptime(filename, "%d.%m.%Y")
        return dt.strftime("%Y-%m-%d"), dt.strftime("%d %B %Y")
    except ValueError:
        pass
    try:
        dt = datetime.strptime(filename, "%Y-%m-%d")
        return filename, dt.strftime("%d %B %Y")
    except ValueError:
        pass
    return None, f"Could not parse date from `{filename}` — expected format: dd.mm.yyyy"


def show():
    st.title("📤 Upload & Process")
    st.caption("Upload a photo of the emotion wheel — AI will detect the dots for you.")

    if "api_key" not in st.session_state or not st.session_state["api_key"]:
        st.warning("Please enter your HF API key in the sidebar to get started.")
        return

    st.divider()

    uploaded_files = st.file_uploader(
        "Upload wheel image(s)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Name your files as dd.mm.yyyy.png — the date is detected automatically."
    )

    if not uploaded_files:
        st.info("Upload one or more emotion wheel photos. Name them `dd.mm.yyyy.png` and the date will be detected automatically.")
        _show_existing_sessions()
        return

    for uploaded_file in uploaded_files:
        filename = Path(uploaded_file.name).stem
        date_str, display = parse_date_from_filename(filename)

        if date_str:
            verified = st.text_input(
                f"📅 Detected date for `{uploaded_file.name}`",
                value=date_str,
                help="Auto-detected from filename. Edit if incorrect (format: YYYY-MM-DD).",
                key=f"date_{uploaded_file.name}"
            )
            date_str = verified.strip() if verified.strip() else date_str
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                st.caption(f"✅ {dt.strftime('%d %B %Y')}")
            except ValueError:
                st.error("Invalid date format — please use YYYY-MM-DD")
                continue
        else:
            st.warning(display)
            date_str = st.text_input(
                f"Enter date manually for `{uploaded_file.name}`",
                placeholder="2025-03-04",
                help="Format: YYYY-MM-DD",
                key=f"date_manual_{uploaded_file.name}"
            )
            if not date_str:
                continue

        session_path = Path("sessions") / f"{date_str}.json"

        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(uploaded_file, caption=f"Session: {date_str}", use_container_width=True)

        with col2:
            if session_path.exists():
                st.success(f"Already processed — {date_str}")
                with open(session_path) as f:
                    existing = json.load(f)
                st.json(existing, expanded=False)
                if st.button(f"Re-process {date_str}", key=f"reprocess_{date_str}"):
                    _process(uploaded_file, date_str)
            else:
                if st.button(f"Extract emotions — {date_str}", key=f"process_{date_str}", type="primary"):
                    _process(uploaded_file, date_str)

    st.divider()
    _show_existing_sessions()


def _process(uploaded_file, date_str):
    with st.spinner(f"Reading the wheel for {date_str}... 🔍"):
        try:
            image_bytes = uploaded_file.read()
            result = extract_emotions(image_bytes, st.session_state["api_key"], date_str)

            st.success(f"Found {result['total_dots']} dots across {len(result['emotions'])} emotion entries!")

            edited = st.data_editor(
                result["emotions"],
                num_rows="dynamic",
                use_container_width=True,
                key=f"editor_{date_str}"
            )

            if st.button(f"Save session — {date_str}", key=f"save_{date_str}", type="primary"):
                result["emotions"] = edited
                result["total_dots"] = sum(e.get("count", 0) for e in edited)
                path = save_session(result)
                st.success(f"Saved to `{path}` ✅")
                st.rerun()

        except Exception as e:
            st.error(f"Something went wrong: {e}")


def _show_existing_sessions():
    sessions = load_all_sessions()
    if not sessions:
        return

    st.subheader(f"Saved sessions ({len(sessions)})")
    for s in sessions:
        with st.expander(f"📅 {s['date']} — {s.get('total_dots', '?')} dots"):
            st.json(s, expanded=False)
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("Delete", key=f"del_{s['date']}"):
                    Path(f"sessions/{s['date']}.json").unlink(missing_ok=True)
                    st.rerun()
