import json
import uuid

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

REQUIRED_KEYS = ["name", "player", "class", "level", "stats"]


def get_worksheet(sheet_name="Characters", spreadsheet_key="1thahE8pmZmuO7Jr6Do3Y-vqUK2H-VhR2ahQKmIU2Pao"):
    """Real auth path — only used in production, never in tests."""
    creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = (
        client.open_by_key(spreadsheet_key)
    )
    return spreadsheet.worksheet(sheet_name)


def save_character(character_data: dict, worksheet=None) -> dict:
    missing = [key for key in REQUIRED_KEYS if key not in character_data]
    if missing:
        return {"status": "error", "message": f"missing required keys: {missing}"}

    if worksheet is None:
        worksheet = get_worksheet(sheet_name="Characters")  # default tab name; adjust if you renamed it

    # duplicate check on (name, player), read BEFORE writing
    existing_records = worksheet.get_all_records()
    for record in existing_records:
        if (record.get("name") == character_data["name"]
                and record.get("player") == character_data["player"]):
            return {"status": "exists", "message": "duplicate character name for this player"}

    char_id = f"char_{uuid.uuid4().hex[:6]}"
    row = [
        char_id,
        character_data["name"],
        character_data["player"],
        character_data["class"],
        character_data["level"],
        json.dumps(character_data["stats"]),
        json.dumps(character_data.get("inventory", [])),
    ]

    try:
        worksheet.append_row(row)
    except Exception as exc:
        return {"status": "error", "message": f"failed to write row: {exc}"}

    return {"status": "success", "id": char_id}