import json
import os

from dotenv import load_dotenv
from google import genai

from src.storage.storage_handler import save_character, list_characters

load_dotenv()

REQUIRED_CHARACTER_FIELDS = ["name", "player", "class", "level", "stats"]

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
    return _client

EXTRACTION_PROMPT = """You are extracting structured intent from a D&D club member's message.
Return ONLY JSON, no markdown fences, no preamble.

Valid intents: "register" (create a new character), "list" (show characters), null (anything else).

If intent is "register", extract any of these fields you can find: name, player, class, level, stats, inventory.
Only include fields that were actually stated -- do not invent values.

Message: {user_input}

Respond with exactly this shape:
{{"intent": "register" | "list" | null, "data": {{...}}}}
"""

REFLECTION_PROMPT = """You are validating whether a character registration has all required fields.
Required fields: name, player, class, level, stats.

Extracted data: {data}

Respond with ONLY JSON, no markdown fences:
{{"complete": true | false, "missing": [list of missing required field names]}}
"""

def _extract_intent(user_input: str) -> dict:
    response = _get_client().models.generate_content(
        model="gemini-2.5-flash",
        contents=EXTRACTION_PROMPT.format(user_input=user_input),
    )
    return json.loads(response.text)


def _reflect(intent: str, data: dict) -> dict:
    response = _get_client().models.generate_content(
        model="gemini-2.5-flash",
        contents=REFLECTION_PROMPT.format(data=json.dumps(data)),
    )
    return json.loads(response.text)


def process_request(user_input: str) -> dict:
    extraction = _extract_intent(user_input)
    intent = extraction.get("intent")
    data = extraction.get("data", {})

    if intent == "register":
        reflection = _reflect(intent, data)
        if not reflection.get("complete", False):
            missing = reflection.get("missing", [])
            return {
                "status": "incomplete",
                "message": "I need a bit more information before I can save that character.",
                "missing": missing,
            }

        result = save_character(data)
        if result["status"] == "success":
            return {
                "status": "success",
                "message": f"Saved {data.get('name')} for {data.get('player')}.",
                "id": result["id"],
            }
        return result

    if intent == "list":
        result = list_characters(player=data.get("player"))
        if result["status"] == "success":
            count = len(result["data"])
            return {
                "status": "success",
                "message": f"Found {count} character(s).",
                "data": result["data"],
            }
        return result

    return {"status": "unknown", "message": "Could not determine what you're asking for."}