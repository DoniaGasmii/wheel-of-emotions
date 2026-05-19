# feelmap: HUM-496's Wheel of Emotions

> *Because "how are you feeling?" deserves a better answer than a shrug.*

Built for Prof. Tamara Milosevic and Prof. Helena Kovacs at EPFL. Each week, students place stickers on an emotion wheel to express how they feel as facilitators. **feelmap** turns that analog ritual into an annotated, animated record of a cohort's emotional journey across the semester.

---

## Usage

Just a browser — visit the hosted app at:
**https://wheel-of-emotions-cqk8dbrvhgrfgptcqh8s5q.streamlit.app**

Or run locally:
```bash
git clone https://github.com/yourname/feelmap.git
cd feelmap
pip install -r requirements.txt
python -m streamlit run app.py
```

---

### 1 · Annotate

1. Open the app and go to **1 · Annotate**
2. If returning, load your `feelmap_sessions.json` save file first
3. Upload the wheel photo — date is detected automatically from the filename (`dd_mm_yyyy.png`)
4. Open each emotion group and enter the dot count for emotions that had stickers
5. Hit **Save session**
6. Click **Export save file** and keep `feelmap_sessions.json` on your desktop

> Always export after annotating — the app does not persist data between visits.

---

### 2 · Analyse

1. Go to **2 · Analyse** and upload your `feelmap_sessions.json`
2. Choose a granularity level: **Core / Sub / Sub-sub**
3. Explore across 8 visualisation tabs: polar wheel, radar, positive vs negative arc, stacked bar, line trends, heatmap, bubble timeline, word cloud
4. Export as an animated GIF, a photo timelapse, or a ZIP of PNG charts

---

## Structure

```
feelmap/
├── app.py
├── requirements.txt
├── utils/
│   ├── vision.py           ← session state helpers
│   ├── emotion_tree.py     ← emotion hierarchy
│   └── export.py           ← matplotlib/GIF export
└── views/
    ├── annotate.py
    └── visualize.py
```