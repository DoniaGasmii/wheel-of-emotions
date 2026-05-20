"""
Export utilities using matplotlib — no Chrome/Kaleido needed.
Two GIF modes:
  - make_gif_timelapse: week-by-week full polar frames (no text labels)
  - make_gif_sticker:   sticker-by-sticker animation with spotlight effect
"""
import io
import zipfile
import numpy as np
from utils.emotion_tree import EMOTION_TREE


def _lazy_imports():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from PIL import Image
    return plt, mpatches, Image

CORE_COLORS = {
    "Happy":     "#e8875a",
    "Surprised": "#f0c93a",
    "Bad":       "#6abf8a",
    "Fearful":   "#5bbcd6",
    "Angry":     "#9b6bb5",
    "Disgusted": "#8b7bc8",
    "Sad":       "#b87ab5",
}

CORE_ANGLES_DEG = {
    "Happy":     180,
    "Surprised": 270,
    "Bad":       315,
    "Fearful":   350,
    "Angry":     45,
    "Disgusted": 110,
    "Sad":       145,
}

BG = "#0d1117"
GRID = "#1e1e2e"


def deg_to_rad(deg):
    return np.radians(90 - deg)


def get_core_totals(session):
    totals = {c: 0 for c in CORE_COLORS}
    for e in session.get("emotions", []):
        c = e.get("core")
        if c in totals:
            totals[c] += e.get("count", 0)
    return totals


def emotion_position(e):
    """Return (angle_rad, radius, color, label) for an emotion entry."""
    core = e.get("core")
    sub = e.get("sub")
    sub_sub = e.get("sub_sub")
    color = CORE_COLORS.get(core, "#888")
    label = sub_sub or sub or core
    base = deg_to_rad(CORE_ANGLES_DEG.get(core, 0))
    sector = np.radians(50)
    subs = list(EMOTION_TREE.get(core, {}).get("subs", {}).items())
    n = len(subs)

    if sub is None:
        return base, 0.4, color, label
    try:
        i = [s for s, _ in subs].index(sub)
    except ValueError:
        return base, 0.4, color, label
    angle = base - sector/2 + (i + 0.5) * sector / n
    if sub_sub is None:
        return angle, 0.9, color, label
    leaves = subs[i][1]
    try:
        j = leaves.index(sub_sub)
        angle += np.radians(-4 + (j + 0.5) * 8 / max(len(leaves), 1))
    except ValueError:
        pass
    return angle, 1.5, color, label


def _base_ax(fig):
    plt, mpatches, Image = _lazy_imports()
    ax = fig.add_subplot(111, polar=True, facecolor=BG)
    for core, deg in CORE_ANGLES_DEG.items():
        ax.text(deg_to_rad(deg), 2.3, core, ha="center", va="center",
                color=CORE_COLORS[core], fontsize=11, fontweight="bold")
    ax.set_ylim(0, 2.6)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.grid(color=GRID, linewidth=0.5)
    ax.spines["polar"].set_color(GRID)
    return ax


def _fig_to_pil(fig):
    plt, mpatches, Image = _lazy_imports()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).copy()


# ── GIF 2: week-by-week timelapse (no text labels) ───────────────────────────

def render_polar_frame(session, figsize=(8, 8)) -> "Image.Image":
    fig = plt.figure(figsize=figsize, facecolor=BG)
    ax = _base_ax(fig)

    for e in session.get("emotions", []):
        count = e.get("count", 0)
        angle, radius, color, _ = emotion_position(e)
        size = min(count * 120 + 60, 600)
        ax.scatter(angle, radius, s=size, color=color, alpha=0.85,
                  zorder=5, edgecolors="white", linewidths=0.8)
        # NO text label — size speaks for itself

    handles = [mpatches.Patch(color=c, label=k) for k, c in CORE_COLORS.items()
               if get_core_totals(session).get(k, 0) > 0]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.08),
             ncol=4, framealpha=0, labelcolor="white", fontsize=9)
    fig.suptitle(f"Session — {session['date']}",
                color="#e0e0e0", fontsize=13, y=0.97)
    return _fig_to_pil(fig)


def make_gif_timelapse(sessions, duration_ms=1200) -> bytes:
    """Week-by-week: one full polar frame per session, no labels."""
    frames = [render_polar_frame(s) for s in sessions]
    # hold last frame longer
    durations = [duration_ms] * len(frames)
    durations[-1] = duration_ms * 3
    buf = io.BytesIO()
    frames[0].save(buf, format="GIF", save_all=True,
                  append_images=frames[1:], duration=durations, loop=0)
    buf.seek(0)
    return buf.read()


# keep old name as alias
def make_gif(sessions, duration_ms=1200) -> bytes:
    return make_gif_timelapse(sessions, duration_ms)


# ── GIF 1: sticker-by-sticker with spotlight ─────────────────────────────────

def _render_sticker_frame(placed, active_idx, date, figsize=(8, 8)) -> "Image.Image":
    """
    placed: list of (angle, radius, color, label, count) — all emotions placed so far
    active_idx: index of the currently active (spotlight) emotion
    """
    fig = plt.figure(figsize=figsize, facecolor=BG)
    ax = _base_ax(fig)

    for i, (angle, radius, color, label, count) in enumerate(placed):
        is_active = (i == active_idx)
        size = min(count * 120 + 60, 600)

        if is_active:
            # spotlight: full opacity, white edge, big label
            ax.scatter(angle, radius, s=size, color=color, alpha=1.0,
                      zorder=10, edgecolors="white", linewidths=2.0)
            ax.text(angle, radius + 0.22, label,
                   ha="center", va="bottom", color="white",
                   fontsize=13, fontweight="bold", zorder=11,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor=BG,
                            edgecolor=color, alpha=0.85))
        else:
            # faded: lower opacity, no label
            ax.scatter(angle, radius, s=size, color=color, alpha=0.35,
                      zorder=5, edgecolors="white", linewidths=0.5)

    fig.suptitle(date, color="#e0e0e0", fontsize=15, fontweight="bold", y=0.97)
    return _fig_to_pil(fig)


def _render_week_final(placed, date, figsize=(8, 8)) -> "Image.Image":
    """Final frame for a week: all bubbles visible, no spotlight, no labels."""
    fig = plt.figure(figsize=figsize, facecolor=BG)
    ax = _base_ax(fig)
    for angle, radius, color, label, count in placed:
        size = min(count * 120 + 60, 600)
        ax.scatter(angle, radius, s=size, color=color, alpha=0.85,
                  zorder=5, edgecolors="white", linewidths=0.8)
    handles = [mpatches.Patch(color=c, label=k) for k, c in CORE_COLORS.items()
               if any(pc == c for _, _, pc, _, _ in placed)]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.08),
             ncol=4, framealpha=0, labelcolor="white", fontsize=9)
    fig.suptitle(date, color="#e0e0e0", fontsize=15, fontweight="bold", y=0.97)
    return _fig_to_pil(fig)


def make_gif_sticker(sessions, frame_ms=400, pause_ms=1800) -> bytes:
    """
    Sticker-by-sticker animation:
    - Each emotion appears one by one with spotlight
    - If count > 1, bubble grows step by step
    - Previous emotions fade
    - After all emotions for a week: hold the complete frame, then next week
    """
    frames = []
    durations = []

    for session in sessions:
        emotions = session.get("emotions", [])
        date = session.get("date", "")
        placed = []  # (angle, radius, color, label, current_count)

        for ei, e in enumerate(emotions):
            angle, radius, color, label = emotion_position(e)
            total_count = e.get("count", 0)

            # grow bubble count by count
            for step in range(1, total_count + 1):
                # update or add this emotion's bubble
                entry = (angle, radius, color, label, step)
                if ei < len(placed):
                    placed[ei] = entry
                else:
                    placed.append(entry)

                frame = _render_sticker_frame(placed, ei, date)
                frames.append(frame)
                durations.append(frame_ms)

        # hold final complete frame for this week
        final = _render_week_final(placed, date)
        frames.append(final)
        durations.append(pause_ms)

    buf = io.BytesIO()
    frames[0].save(buf, format="GIF", save_all=True,
                  append_images=frames[1:], duration=durations, loop=0)
    buf.seek(0)
    return buf.read()


# ── ZIP export ────────────────────────────────────────────────────────────────

def make_zip(sessions) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for s in sessions:
            img = render_polar_frame(s)
            img_buf = io.BytesIO()
            img.save(img_buf, format="PNG")
            zf.writestr(f"polar_{s['date']}.png", img_buf.getvalue())
    buf.seek(0)
    return buf.read()