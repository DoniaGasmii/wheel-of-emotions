import json
import re
import base64
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

PROMPT = """You are an expert at reading emotion wheel images.
You will be given a photo of a circular emotion wheel with small black dot stickers placed on it by participants.
Your job is to identify exactly which emotions have dots on them and how many dots each emotion has.

The wheel has 3 levels:
- Core emotions (innermost ring): Happy, Sad, Disgusted, Angry, Fearful, Bad, Surprised
- Sub-emotions (middle ring): e.g. Proud, Content, Playful under Happy
- Sub-sub-emotions (outer ring): e.g. Successful, Confident under Proud

Return ONLY a valid JSON object in this exact format, no markdown, no explanation:
{
  "total_dots": <integer>,
  "emotions": [
    {
      "core": "<core emotion>",
      "sub": "<sub emotion or null>",
      "sub_sub": "<sub-sub emotion or null>",
      "count": <integer>
    }
  ]
}

Rules:
- Be as specific as possible — if a dot is clearly on a sub-sub emotion, use all three levels
- If a dot is between two emotions, pick the closest one
- If a dot is only on a core emotion area, set sub and sub_sub to null
- Count carefully — each sticker = 1 dot
- total_dots must equal the sum of all counts
- Return ONLY the JSON object, nothing else"""

MODEL = "gemini-1.5-flash"


def get_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not found — make sure it's set in your .env file")
    return key


def extract_emotions(image_bytes: bytes, date_str: str) -> dict:
    client = genai.Client(api_key=get_api_key())

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            PROMPT,
        ],
    )

    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    result = json.loads(raw)
    result["date"] = date_str
    return result


def save_session(data: dict, sessions_dir: str = "sessions") -> Path:
    Path(sessions_dir).mkdir(exist_ok=True)
    out_path = Path(sessions_dir) / f"{data['date']}.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    return out_path


def load_all_sessions(sessions_dir: str = "sessions") -> list:
    sessions_path = Path(sessions_dir)
    if not sessions_path.exists():
        return []
    sessions = []
    for f in sorted(sessions_path.glob("*.json")):
        with open(f) as fp:
            sessions.append(json.load(fp))
    return sorted(sessions, key=lambda x: x["date"])