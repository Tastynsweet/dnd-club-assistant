import json
import os
import re

import anthropic
from dotenv import load_dotenv

from src.storage.storage_handler import save_character, list_characters
from src.storage.rules_handler import retrieve_context
from src.storage.embeddings import embed_text
from src.storage.campaigns_handler import query_campaigns_by_schedule

load_dotenv()

REQUIRED_CHARACTER_FIELDS = ["name", "player", "class", "level", "stats"]

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    return _client

def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()
    return json.loads(text)

EXTRACTION_PROMPT = """You are extracting structured intent from a D&D club member's message.
Return ONLY JSON, no markdown fences, no preamble.

Valid intents: "register" (create a new character), "list" (show characters),
"rules_question" (a question about D&D 5e rules),
"matchmaking" (looking for a campaign/DM based on schedule or preferences), null (anything else).

If intent is "register", extract any of these fields you can find: name, player, class, level, stats, inventory.
Only include fields that were actually stated -- do not invent values.

If intent is "rules_question", set data to {{"question": <the user's question, verbatim>}}.

If intent is "matchmaking", extract "day" (e.g. "Saturday") if stated, and "preference_tags"
as a list of short lowercase keywords (e.g. ["low-level", "one-shot", "horror"]) based on what
the user described wanting. Only include a day/tags that were actually implied -- do not invent values.
If nothing usable can be extracted (no day AND no preferences), set intent to null instead.

Message: {user_input}

Respond with exactly this shape:
{{"intent": "register" | "list" | "rules_question" | "matchmaking" | null, "data": {{...}}}}
"""

REFLECTION_PROMPT = """You are validating whether a character registration has all required fields.
Required fields: name, player, class, level, stats.

Extracted data: {data}

Respond with ONLY JSON, no markdown fences:
{{"complete": true | false, "missing": [list of missing required field names]}}
"""

RULES_ANSWER_PROMPT = """You are a D&D 5e rules assistant. Answer the question using ONLY the
rulebook excerpts below. Do not use outside knowledge -- if the excerpts don't
answer the question, say so.

Question: {question}

Rulebook excerpts:
{context}

Respond with ONLY JSON, no markdown fences:
{{"answer": "<grounded answer citing what the excerpts say>", "source": "<the source label of the excerpt(s) you used>"}}
"""

def _extract_intent(user_input: str) -> dict:
    response = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(user_input=user_input)}],
    )
    return _parse_json_response(response.content[0].text)

def _reflect(intent: str, data: dict) -> dict:
    response = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": REFLECTION_PROMPT.format(data=json.dumps(data))}],
    )
    return _parse_json_response(response.content[0].text)

def get_rules_answer(user_query: str) -> dict:
    if not user_query or not user_query.strip():
        return {"status": "empty_input", "message": "Please enter a question."}

    query_embedding = embed_text(user_query)
    retrieval = retrieve_context(query_embedding, top_k=3)

    if retrieval["status"] == "no_match":
        return {
            "status": "not_found",
            "message": "This isn't covered in the core rules; check with your DM.",
        }

    context = "\n\n---\n\n".join(
        f"[{source}]\n{chunk}"
        for chunk, source in zip(retrieval["data"]["chunks"], retrieval["data"]["sources"])
    )

    response = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": RULES_ANSWER_PROMPT.format(question=user_query, context=context),
        }],
    )
    parsed = _parse_json_response(response.content[0].text)

    return {
        "status": "success",
        "data": {"answer": parsed["answer"], "source": parsed["source"]},
    }

def find_campaign_match(request_text: str, day: str = None, preference_tags: list = None) -> dict:
    if not day and not preference_tags:
        return {
            "status": "unclear_request",
            "message": "could not parse schedule or preferences",
        }

    result = query_campaigns_by_schedule(day=day, preference_tags=preference_tags)
    if result["status"] == "no_match":
        return result

    return {"status": "success", "data": {"matches": result["data"]["campaigns"]}}

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

    if intent == "rules_question":
        question = data.get("question", user_input)
        result = get_rules_answer(question)
        if result["status"] == "success":
            return {
                "status": "success",
                "message": result["data"]["answer"],
                "source": result["data"]["source"],
            }
        return result

    if intent == "matchmaking":
        result = find_campaign_match(user_input, day=data.get("day"), preference_tags=data.get("preference_tags"))
        if result["status"] == "success":
            count = len(result["data"]["matches"])
            return {
                "status": "success",
                "message": f"Found {count} matching campaign(s).",
                "data": result["data"]["matches"],
            }
        return result

    return {"status": "unknown", "message": "Could not determine what you're asking for."}