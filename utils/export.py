import io
import zipfile
import numpy as np
from .emotion_tree import EMOTION_TREE

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

BG = "#fdf6f0"
GRID = "#e8d5c4"


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


def _get_mpl():
    """Lazy-load matplotlib and PIL — only when actually needed."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from PIL import Image
    return plt, mpatches, Image


def _base_ax(plt, fig):
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


def _fig_to_pil(plt, Image, fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).copy()


def render_polar_frame(session, figsize=(8, 8)):
    plt, mpatches, Image = _get_mpl()
    fig = plt.figure(figsize=figsize, facecolor=BG)
    ax = _base_ax(plt, fig)
    for e in session.get("emotions", []):
        count = e.get("count", 0)
        angle, radius, color, _ = emotion_position(e)
        size = min(count * 120 + 60, 600)
        ax.scatter(angle, radius, s=size, color=color, alpha=0.85,
                  zorder=5, edgecolors="white", linewidths=0.8)
    handles = [mpatches.Patch(color=c, label=k) for k, c in CORE_COLORS.items()
               if get_core_totals(session).get(k, 0) > 0]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.08),
             ncol=4, framealpha=0, labelcolor="#2d2420", fontsize=9)
    fig.suptitle(f"Session — {session['date']}",
                color="#2d2420", fontsize=13, y=0.97)
    return _fig_to_pil(plt, Image, fig)


def make_gif_timelapse(sessions, duration_ms=1200):
    plt, mpatches, Image = _get_mpl()
    frames = [render_polar_frame(s) for s in sessions]
    durations = [duration_ms] * len(frames)
    durations[-1] = duration_ms * 3
    buf = io.BytesIO()
    frames[0].save(buf, format="GIF", save_all=True,
                  append_images=frames[1:], duration=durations, loop=0)
    buf.seek(0)
    return buf.read()


def make_gif(sessions, duration_ms=1200):
    return make_gif_timelapse(sessions, duration_ms)


def _render_sticker_frame(session_date, placed, active_idx, figsize=(8, 8)):
    plt, mpatches, Image = _get_mpl()
    fig = plt.figure(figsize=figsize, facecolor=BG)
    ax = _base_ax(plt, fig)
    for i, (angle, radius, color, label, count) in enumerate(placed):
        is_active = (i == active_idx)
        size = min(count * 120 + 60, 600)
        if is_active:
            ax.scatter(angle, radius, s=size, color=color, alpha=1.0,
                      zorder=10, edgecolors="white", linewidths=2.0)
            ax.text(angle, radius + 0.22, label,
                   ha="center", va="bottom", color="#2d2420",
                   fontsize=13, fontweight="bold", zorder=11,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor=BG,
                            edgecolor=color, alpha=0.9))
        else:
            ax.scatter(angle, radius, s=size, color=color, alpha=0.3,
                      zorder=5, edgecolors="white", linewidths=0.5)
    fig.suptitle(session_date, color="#2d2420", fontsize=15, fontweight="bold", y=0.97)
    return _fig_to_pil(plt, Image, fig)


def _render_week_final(session_date, placed, figsize=(8, 8)):
    plt, mpatches, Image = _get_mpl()
    fig = plt.figure(figsize=figsize, facecolor=BG)
    ax = _base_ax(plt, fig)
    for angle, radius, color, label, count in placed:
        size = min(count * 120 + 60, 600)
        ax.scatter(angle, radius, s=size, color=color, alpha=0.85,
                  zorder=5, edgecolors="white", linewidths=0.8)
    handles = [mpatches.Patch(color=c, label=k) for k, c in CORE_COLORS.items()
               if any(pc == c for _, _, pc, _, _ in placed)]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.08),
             ncol=4, framealpha=0, labelcolor="#2d2420", fontsize=9)
    fig.suptitle(session_date, color="#2d2420", fontsize=15, fontweight="bold", y=0.97)
    return _fig_to_pil(plt, Image, fig)


def make_gif_sticker(sessions, frame_ms=400, pause_ms=1800):
    frames = []
    durations = []
    for session in sessions:
        emotions = session.get("emotions", [])
        date = session.get("date", "")
        placed = []
        for ei, e in enumerate(emotions):
            angle, radius, color, label = emotion_position(e)
            total_count = e.get("count", 0)
            for step in range(1, total_count + 1):
                entry = (angle, radius, color, label, step)
                if ei < len(placed):
                    placed[ei] = entry
                else:
                    placed.append(entry)
                frame = _render_sticker_frame(date, placed, ei)
                frames.append(frame)
                durations.append(frame_ms)
        final = _render_week_final(date, placed)
        frames.append(final)
        durations.append(pause_ms)
    buf = io.BytesIO()
    frames[0].save(buf, format="GIF", save_all=True,
                  append_images=frames[1:], duration=durations, loop=0)
    buf.seek(0)
    return buf.read()


def make_zip(sessions):
    plt, mpatches, Image = _get_mpl()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for s in sessions:
            img = render_polar_frame(s)
            img_buf = io.BytesIO()
            img.save(img_buf, format="PNG")
            zf.writestr(f"polar_{s['date']}.png", img_buf.getvalue())
    buf.seek(0)
    return buf.read()