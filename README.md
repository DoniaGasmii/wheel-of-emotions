# feelmap: HUM-496's Wheel of Emotions🌈

> *Because "how are you feeling?" deserves a better answer than a shrug.*

This project was built with love for the professors of a sustainability facilitation course at EPFL university Prof. Tamara Milosevic and Prof. Helena Kovacs, the kind of people who start every session with an emotion wheel and actually mean it. 

Each week, students place stickers on a wheel of emotions to express how they feel as facilitators. Over a semester, this creates a quiet, colorful record of a group's emotional journey, from *scared and stressed* in week one to (hopefully) *proud and confident* by the end.

**feelmap** turns that analog ritual into something digital, reusable, and a little bit beautiful. It uses AI vision to read the emotion wheels from photos. The result is an animated timelapse of the group's emotional evolution, week by week, feeling by feeling.

It's a small tool built for a specific, human purpose: helping reflective educators see the arc of a semester.

---

*Made with care for people who care about how their students feel. You know who you are.* 🤍

---

## How it works

The tool is split into two parts:

**1 · Annotate** — run locally by the session annotator
- Upload a wheel photo (named `dd_mm_yyyy.png`)
- Fill in the emotion tree by marking which emotions have stickers and how many
- Save each session, then export everything as a single `feelmap_sessions.json` file

**2 · Analyse** — hosted publicly on Streamlit Cloud
- Upload the exported `feelmap_sessions.json`
- Explore the polar chart timelapse week by week
- Download all charts as a ZIP of PNGs

---

## Run the annotation tool locally

```bash
git clone https://github.com/yourname/feelmap.git
cd feelmap
pip install -r requirements.txt
python -m streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## Visualise online

👉 **[feelmap.streamlit.app](https://feelmap.streamlit.app)** ← upload your `feelmap_sessions.json` here

---

## Project structure

```
feelmap/
├── app.py                  ← entry point
├── requirements.txt
├── .env.example            ← copy to .env if using Gemini API
├── utils/
│   ├── vision.py           ← session save/load logic
│   └── emotion_tree.py     ← the full emotion hierarchy
├── pages/
│   ├── annotate.py         ← local annotation UI
│   └── visualize.py        ← hosted visualisation UI
└── sessions/               ← generated locally, gitignored
```
