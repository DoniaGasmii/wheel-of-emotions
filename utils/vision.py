import anthropic
import base64
import json
import re
from pathlib import Path


SYSTEM_PROMPT = """You are an expert at reading emotion wheel images. 
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
- total_dots must equal the sum of all counts"""


def encode_image(image_bytes: bytes) -> str:
    return base64.standard_b64encode(image_bytes).decode("utf-8")


def extract_emotions(image_bytes: bytes, api_key: str, date_str: str) -> dict:
    client = anthropic.Anthropic(api_key=api_key)

    image_data = encode_image(image_bytes)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Please identify all the dot stickers on this emotion wheel and return the structured JSON."
                    }
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
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


def load_all_sessions(sessions_dir: str = "sessions") -> list[dict]:
    sessions_path = Path(sessions_dir)
    if not sessions_path.exists():
        return []
    sessions = []
    for f in sorted(sessions_path.glob("*.json")):
        with open(f) as fp:
            sessions.append(json.load(fp))
    return sorted(sessions, key=lambda x: x["date"])

