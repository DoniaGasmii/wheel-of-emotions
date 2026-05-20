import streamlit as st
import json
from utils.tree_state import set_custom_tree, get_active_tree


def show():
    st.markdown('<h2 style="margin-bottom:4px">✏️ Build your emotion wheel</h2>',
                unsafe_allow_html=True)
    st.caption("Define your own emotion tree. You can have as many core emotions, sub-emotions, and sub-sub-emotions as you like.")

    st.divider()

    # ── Init builder state ───────────────────────────────────────────────────
    if "builder_tree" not in st.session_state:
        st.session_state["builder_tree"] = {}

    tree = st.session_state["builder_tree"]

    # ── Add core emotion ─────────────────────────────────────────────────────
    st.markdown("#### Core emotions")
    st.caption("These are the main categories in the centre of your wheel.")

    new_core = st.text_input("Add a core emotion", placeholder="e.g. Happy",
                             key="new_core_input")
    if st.button("+ Add core emotion", key="add_core"):
        name = new_core.strip().title()
        if name and name not in tree:
            tree[name] = {}
            st.session_state["builder_tree"] = tree
            st.rerun()
        elif name in tree:
            st.warning(f"'{name}' already exists.")

    if not tree:
        st.info("Add your first core emotion above to get started.")
        return

    st.divider()

    # ── Build sub-levels per core ────────────────────────────────────────────
    for core in list(tree.keys()):
        with st.expander(f"● {core}", expanded=True):
            col_del, _ = st.columns([1, 5])
            with col_del:
                if st.button(f"Remove '{core}'", key=f"del_core_{core}"):
                    del tree[core]
                    st.session_state["builder_tree"] = tree
                    st.rerun()

            st.markdown(f"**Sub-emotions under {core}:**")
            new_sub = st.text_input(f"Add sub-emotion", placeholder="e.g. Joyful",
                                    key=f"new_sub_{core}")
            if st.button(f"+ Add", key=f"add_sub_{core}"):
                name = new_sub.strip().title()
                if name and name not in tree[core]:
                    tree[core][name] = []
                    st.session_state["builder_tree"] = tree
                    st.rerun()

            for sub in list(tree[core].keys()):
                st.markdown(f"&nbsp;&nbsp;&nbsp;**{sub}**", unsafe_allow_html=True)
                leaves = tree[core][sub]

                # leaf inputs
                leaf_cols = st.columns([3, 1])
                with leaf_cols[0]:
                    new_leaf = st.text_input(f"Add sub-sub under {sub}",
                                            placeholder="e.g. Proud",
                                            key=f"new_leaf_{core}_{sub}",
                                            label_visibility="collapsed")
                with leaf_cols[1]:
                    if st.button("+ Add", key=f"add_leaf_{core}_{sub}"):
                        name = new_leaf.strip().title()
                        if name and name not in leaves:
                            leaves.append(name)
                            st.session_state["builder_tree"] = tree
                            st.rerun()

                if leaves:
                    for leaf in list(leaves):
                        lc1, lc2 = st.columns([4, 1])
                        with lc1:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;· {leaf}",
                                       unsafe_allow_html=True)
                        with lc2:
                            if st.button("✕", key=f"del_leaf_{core}_{sub}_{leaf}"):
                                leaves.remove(leaf)
                                st.session_state["builder_tree"] = tree
                                st.rerun()

                c1, c2 = st.columns([4, 1])
                with c2:
                    if st.button("Remove sub", key=f"del_sub_{core}_{sub}"):
                        del tree[core][sub]
                        st.session_state["builder_tree"] = tree
                        st.rerun()
                st.markdown("---")

    st.divider()

    # ── Import / Export ──────────────────────────────────────────────────────
    col_imp, col_exp = st.columns(2)
    with col_imp:
        st.markdown("**Import tree from JSON**")
        uploaded = st.file_uploader("Upload tree JSON", type=["json"], key="tree_upload",
                                   label_visibility="collapsed")
        if uploaded:
            try:
                imported = json.load(uploaded)
                st.session_state["builder_tree"] = imported
                st.success("Tree imported!")
                st.rerun()
            except Exception as e:
                st.error(f"Could not read file: {e}")

    with col_exp:
        st.markdown("**Export tree as JSON**")
        st.download_button(
            "⬇️ Download tree",
            data=json.dumps(tree, indent=2),
            file_name="custom_wheel.json",
            mime="application/json",
            use_container_width=True
        )

    st.divider()

    # ── Confirm & use ────────────────────────────────────────────────────────
    total_cores = len(tree)
    total_subs = sum(len(v) for v in tree.values())
    total_leaves = sum(len(l) for v in tree.values() for l in v.values())
    st.markdown(f"**Tree summary:** {total_cores} core emotions · {total_subs} sub-emotions · {total_leaves} sub-sub-emotions")

    if total_cores == 0:
        st.warning("Add at least one core emotion before saving.")
    else:
        # convert builder format to app format: {core: {color: ..., subs: {sub: [leaves]}}}
        from utils.tree_state import get_core_colors
        colors = get_core_colors(tree)
        app_tree = {
            core: {"color": colors[core], "subs": subs}
            for core, subs in tree.items()
        }
        if st.button("✅ Use this wheel", type="primary", use_container_width=True):
            set_custom_tree(app_tree)
            st.session_state["wheel_chosen"] = "custom"
            st.session_state["page"] = "home"
            st.success("Custom wheel saved! Returning to home...")
            st.rerun()