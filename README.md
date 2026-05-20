# feelmap: HUM-496's Wheel of Emotions

> *Because "how are you feeling?" deserves a better answer than a shrug.*

Built for Prof. Tamara Milosevic and Prof. Helena Kovacs at EPFL — the kind of educators who start every session with an emotion wheel and actually mean it. **feelmap** turns that analog ritual into an annotated, animated record of a cohort's emotional journey across the semester.

This tool is open to anyone using emotion wheels in teaching. If you track how your students feel, feelmap can help you see the arc of a semester.

---

## Usage

Just a browser — visit the hosted app at:
**https://wheel-of-emotions-hum-496.streamlit.app/**

Or run locally:
```bash
git clone https://github.com/yourname/feelmap.git
cd feelmap
pip install -r requirements.txt
python -m streamlit run app.py
```

---

### Getting started

On the **Home** page, choose your wheel:
- **Default wheel** — the standard 7-core emotion wheel (Happy, Sad, Angry, Fearful, Bad, Disgusted, Surprised)
- **Custom wheel** — define your own emotion tree with any structure and labels

Then choose what to do:

---

### 1 · Annotate

1. If returning, load your `feelmap_sessions.json` save file first
2. Upload the wheel photo — date is detected automatically from the filename (`dd_mm_yyyy.png`)
3. Open each emotion group and enter the dot count for emotions that had stickers
4. Hit **Save session**
5. Click **Export save file** — keep `feelmap_sessions.json` on your desktop

> Always export after annotating — the app does not persist data between visits.

---

### 2 · Visualise

1. Upload your `feelmap_sessions.json`
2. Choose a granularity level: **Core / Sub / Sub-sub**
3. Explore across 8 tabs: polar wheel, radar, positive vs negative arc, stacked bar, line trends, heatmap, bubble timeline, word cloud
4. Export as a **sticker-by-sticker GIF**, a **week timelapse GIF**, a **photo timelapse**, or a **ZIP of PNGs**

---

### 3 · Analyse

Upload your `feelmap_sessions.json` to get:
- Emotions **never chosen** — candidates for removal from the wheel
- **Rarely chosen** emotions
- **Most dominant** emotions across the semester
- **Biggest week-over-week shifts**
- **Positive vs challenging** ratio per session
- Emotions **present every single week**

---

## Structure

```
feelmap/
├── app.py
├── requirements.txt
├── utils/
│   ├── vision.py           ← session state helpers
│   ├── emotion_tree.py     ← default emotion hierarchy
│   ├── tree_state.py       ← active tree resolver (default or custom)
│   └── export.py           ← matplotlib/GIF export
└── views/
    ├── home.py             ← landing page
    ├── wheel_builder.py    ← custom wheel form
    ├── annotate.py
    ├── visualize.py
    └── analyse.py
```
