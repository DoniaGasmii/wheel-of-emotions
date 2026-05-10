import json
import re
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def get_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not found")
    return key


def save_session_to_state(session: dict):
    """Save a session into Streamlit session_state."""
    import streamlit as st
    if "sessions" not in st.session_state:
        st.session_state["sessions"] = {}
    st.session_state["sessions"][session["date"]] = session


def load_sessions_from_state() -> list:
    """Load all sessions from Streamlit session_state, sorted by date."""
    import streamlit as st
    if "sessions" not in st.session_state:
        return []
    return sorted(st.session_state["sessions"].values(), key=lambda x: x["date"])


def delete_session_from_state(date: str):
    import streamlit as st
    if "sessions" in st.session_state:
        st.session_state["sessions"].pop(date, None)


def sessions_to_json(sessions: list) -> str:
    return json.dumps({"sessions": sessions}, indent=2)


def sessions_from_json(data: dict) -> list:
    if "sessions" in data:
        return sorted(data["sessions"], key=lambda x: x["date"])
    if isinstance(data, list):
        return sorted(data, key=lambda x: x["date"])
    return []