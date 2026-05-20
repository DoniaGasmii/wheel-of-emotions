"""
Active emotion tree resolver.
Returns either the default hardcoded tree or the user's custom tree from session_state.
"""
import streamlit as st
from .emotion_tree import EMOTION_TREE as DEFAULT_TREE


def get_active_tree() -> dict:
    """Return custom tree if set, otherwise default."""
    return st.session_state.get("custom_tree") or DEFAULT_TREE


def set_custom_tree(tree: dict):
    st.session_state["custom_tree"] = tree


def clear_custom_tree():
    st.session_state.pop("custom_tree", None)


def is_custom() -> bool:
    return "custom_tree" in st.session_state and bool(st.session_state["custom_tree"])


def get_core_colors(tree: dict) -> dict:
    """
    Return a color map for the given tree's core emotions.
    Uses preset palette cycling if more/fewer cores than default.
    """
    PALETTE = [
        "#e8875a", "#f0c93a", "#6abf8a", "#5bbcd6",
        "#9b6bb5", "#8b7bc8", "#b87ab5", "#e05c5c",
        "#4db8a4", "#f5a623", "#7bc8f5"
    ]
    default_colors = {
        "Happy": "#e8875a", "Surprised": "#f0c93a", "Bad": "#6abf8a",
        "Fearful": "#5bbcd6", "Angry": "#9b6bb5", "Disgusted": "#8b7bc8",
        "Sad": "#b87ab5",
    }
    result = {}
    palette_idx = 0
    for core in tree:
        if core in default_colors:
            result[core] = default_colors[core]
        else:
            result[core] = PALETTE[palette_idx % len(PALETTE)]
            palette_idx += 1
    return result