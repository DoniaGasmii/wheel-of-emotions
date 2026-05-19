"""
Export utilities using matplotlib — no Chrome/Kaleido needed.
Generates PNG frames for each session and assembles them into a GIF.
"""
import io
import zipfile
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image
from utils.emotion_tree import EMOTION_TREE

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


def deg_to_rad(deg):
    # matplotlib polar: 0=right, counterclockwise
    # we want 0=top, clockwise → convert
    return np.radians(90 - deg)


def get_core_totals(session):
    totals = {c: 0 for c in CORE_COLORS}
    for e in session.get("emotions", []):
        c = e.get("core")
        if c in totals:
            totals[c] += e.get("count", 0)
    return totals


def render_polar_frame(session, figsize=(8, 8)) -> Image.Image:
    fig = plt.figure(figsize=figsize, facecolor="#0d1117")
    ax = fig.add_subplot(111, polar=True, facecolor="#0d1117")

    # Draw core emotion labels around the wheel
    for core, deg in CORE_ANGLES_DEG.items():
        angle = deg_to_rad(deg)
        ax.text(angle, 2.3, core, ha="center", va="center",
                color=CORE_COLORS[core], fontsize=11, fontweight="bold")

    # Build angle map
    sector = np.radians(50)
    plotted = []
    for core, base_deg in CORE_ANGLES_DEG.items():
        base = deg_to_rad(base_deg)
        color = CORE_COLORS[core]
        subs = list(EMOTION_TREE[core]["subs"].items())
        n = len(subs)

        for e in session.get("emotions", []):
            if e.get("core") != core:
                continue
            count = e.get("count", 0)
            sub = e.get("sub")
            sub_sub = e.get("sub_sub")

            if sub is None:
                # dot directly on core
                angle = base
                radius = 0.4
            elif sub_sub is None:
                # dot on sub
                try:
                    i = [s for s, _ in subs].index(sub)
                except ValueError:
                    continue
                angle = base - sector/2 + (i + 0.5) * sector / n
                radius = 0.9
            else:
                # dot on leaf
                try:
                    i = [s for s, _ in subs].index(sub)
                except ValueError:
                    continue
                angle = base - sector/2 + (i + 0.5) * sector / n
                leaves = subs[i][1]
                try:
                    j = leaves.index(sub_sub)
                    angle += np.radians(-4 + (j + 0.5) * 8 / max(len(leaves), 1))
                except ValueError:
                    pass
                radius = 1.5

            size = min(count * 120 + 60, 600)
            ax.scatter(angle, radius, s=size, color=color, alpha=0.85,
                      zorder=5, edgecolors="white", linewidths=0.8)
            label = sub_sub or sub or core
            ax.text(angle, radius + 0.18, f"{label}\n({count})",
                   ha="center", va="bottom", color="white",
                   fontsize=7, zorder=6)

    # Grid styling
    ax.set_ylim(0, 2.6)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.grid(color="#1e1e2e", linewidth=0.5)
    ax.spines["polar"].set_color("#1e1e2e")

    # Legend
    handles = [mpatches.Patch(color=c, label=k) for k, c in CORE_COLORS.items()
               if get_core_totals(session).get(k, 0) > 0]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.08),
             ncol=4, framealpha=0, labelcolor="white", fontsize=9)

    # Title
    fig.suptitle(f"Session — {session['date']}  ({session.get('total_dots','?')} dots)",
                color="#e0e0e0", fontsize=13, y=0.97)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
               facecolor="#0d1117")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).copy()


def make_gif(sessions, duration_ms=1200) -> bytes:
    frames = [render_polar_frame(s) for s in sessions]
    buf = io.BytesIO()
    frames[0].save(
        buf, format="GIF", save_all=True,
        append_images=frames[1:],
        duration=duration_ms, loop=0,
        optimize=False
    )
    buf.seek(0)
    return buf.read()


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