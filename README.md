# feelmap: HUM-496's Wheel of Emotions🌈

> *Because "how are you feeling?" deserves a better answer than a shrug.*

This project was built with love for the professors of a sustainability facilitation course at EPFL university Prof. Tamara Milosevic and Prof. Helena Kovacs, the kind of people who start every session with an emotion wheel and actually mean it. 

Each week, students place stickers on a wheel of emotions to express how they feel as facilitators. Over a semester, this creates a quiet, colorful record of a group's emotional journey, from *scared and stressed* in week one to (hopefully) *proud and confident* by the end.

**feelmap** turns that analog ritual into something digital, reusable, and a little bit beautiful. It uses AI vision to read the emotion wheels from photos. The result is an animated timelapse of the group's emotional evolution, week by week, feeling by feeling.

It's a small tool built for a specific, human purpose: helping reflective educators see the arc of a semester.

---

*Made with care for people who care about how their students feel. You know who you are.* 🤍

---

## Usage

### What you need
Just a browser. No installation required — visit the hosted app at:
**https://wheel-of-emotions-cqk8dbrvhgrfgptcqh8s5q.streamlit.app**

Or run it locally:
```bash
git clone https://github.com/yourname/feelmap.git
cd feelmap
pip install -r requirements.txt
python -m streamlit run app.py
```

---

### 1 · Annotate

Each week, after the emotion wheel session:

1. Open the app and go to **1 · Annotate**
2. If you've annotated before, first **load your save file** (`feelmap_sessions.json`) in the top section to pick up where you left off
3. Upload the wheel photo — the date is detected automatically from the filename (`dd_mm_yyyy.png`)
4. Open each emotion group and enter the dot count for any emotion that had a sticker
5. Hit **Save session**
6. Click **Export save file** and keep the downloaded `feelmap_sessions.json` safe on your desktop — this is your data, bring it back next week

> ⚠️ Always export after annotating. The app doesn't remember your data between visits.

---

### 2 · Analyse

When you're ready to explore the data (end of semester, or anytime):

1. Go to **2 · Analyse**
2. Upload your `feelmap_sessions.json`
3. Use the slider to move through sessions and see the polar emotion chart evolve week by week
4. Scroll down for the full semester evolution chart
5. Click **Export ZIP** to download all charts as PNGs

---

## File structure
```
feelmap/
├── app.py                  ← entry point
├── requirements.txt
├── utils/
│   ├── vision.py           ← session state helpers
│   └── emotion_tree.py     ← emotion hierarchy
└── pages/
    ├── annotate.py         ← annotation UI
    └── visualize.py        ← visualisation UI
```
