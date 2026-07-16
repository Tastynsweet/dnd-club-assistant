from src.storage.storage_handler import save_character

class FakeWorksheet:
    def __init__(self, existing_records=None):
        self._records = existing_records or []
        self.appended_rows = []

    def get_all_records(self):
        return self._records
    
    def append_row(self, row):
        self.appended_rows.append(row)

VALID_CHARACTER = {
    "name": "Feilong",
    "player": "Andy",
    "class": "Monk",
    "level": 4,
    "stats": {"str": 12, "dex": 20, "con": 11, "int": 10, "wis": 16, "cha": 11},
    "inventory": ["staff", "spellbook", "healing potion"],
}

def test_save_character_success():
    ws = FakeWorksheet(existing_records=[])
    result = save_character(VALID_CHARACTER, worksheet=ws)
    assert result["status"] == "success"
    assert "id" in result
    assert len(ws.appended_rows) == 1

def test_save_character_duplicate():
    ws = FakeWorksheet(existing_records=[{"name": "Feilong", "player": "Andy"}])
    result = save_character(VALID_CHARACTER, worksheet=ws)
    assert result == {"status": "exists", "message": "duplicate character name for this player"}
    assert len(ws.appended_rows) == 0


def test_save_character_missing_fields():
    ws = FakeWorksheet(existing_records=[])
    incomplete = {"name": "Feilong", "player": "Andy"}
    result = save_character(incomplete, worksheet=ws)
    assert result["status"] == "error"
    assert len(ws.appended_rows) == 0


def test_save_character_allows_same_name_different_player():
    ws = FakeWorksheet(existing_records=[{"name": "Feilong", "player": "SomeoneElse"}])
    result = save_character(VALID_CHARACTER, worksheet=ws)
    assert result["status"] == "success"