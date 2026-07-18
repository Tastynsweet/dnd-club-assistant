from unittest.mock import patch

from src.engine.engine import process_request


# ---------------------------------------------------------------------------
# Test 1: Register success

@patch("src.engine.engine.save_character")
@patch("src.engine.engine._reflect")
@patch("src.engine.engine._extract_intent")
def test_register_success(mock_extract, mock_reflect, mock_save):
    mock_extract.return_value = {
        "intent": "register",
        "data": {
            "name": "Feilong", "player": "Andy", "class": "Monk",
            "level": 4, "stats": {"str": 12}, "inventory": [],
        },
    }
    mock_reflect.return_value = {"complete": True, "missing": []}
    mock_save.return_value = {"status": "success", "id": "char_045"}

    result = process_request("Register Feilong, a level 4 Monk played by Andy.")

    assert result["status"] == "success"
    mock_save.assert_called_once()


# ---------------------------------------------------------------------------
# Test 2: Register duplicate
# ---------------------------------------------------------------------------
@patch("src.engine.engine.save_character")
@patch("src.engine.engine._reflect")
@patch("src.engine.engine._extract_intent")
def test_register_duplicate(mock_extract, mock_reflect, mock_save):
    mock_extract.return_value = {
        "intent": "register",
        "data": {
            "name": "Feilong", "player": "Andy", "class": "Monk",
            "level": 4, "stats": {"str": 12}, "inventory": [],
        },
    }
    mock_reflect.return_value = {"complete": True, "missing": []}
    mock_save.return_value = {"status": "exists", "message": "duplicate character name for this player"}

    result = process_request("Register Feilong again.")

    assert result["status"] == "exists"


# ---------------------------------------------------------------------------
# Test 3: List characters
# ---------------------------------------------------------------------------
@patch("src.engine.engine.list_characters")
@patch("src.engine.engine._extract_intent")
def test_list_characters(mock_extract, mock_list):
    mock_extract.return_value = {"intent": "list", "data": {}}
    mock_list.return_value = {"status": "success", "data": [{"name": "Feilong", "player": "Andy"}]}

    result = process_request("Show me all my characters.")

    assert result["status"] == "success"
    assert result["data"] == [{"name": "Feilong", "player": "Andy"}]


# ---------------------------------------------------------------------------
# Test 4: Reflection blocks incomplete input -- storage is NEVER called
# ---------------------------------------------------------------------------
@patch("src.engine.engine.save_character")
@patch("src.engine.engine._reflect")
@patch("src.engine.engine._extract_intent")
def test_reflection_blocks_incomplete_input(mock_extract, mock_reflect, mock_save):
    mock_extract.return_value = {
        "intent": "register",
        "data": {"name": "Bob"},
    }
    mock_reflect.return_value = {"complete": False, "missing": ["player", "class", "level", "stats"]}

    result = process_request("Register Bob.")

    assert result["status"] == "incomplete"
    mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# Test 5: Unknown intent
# ---------------------------------------------------------------------------
@patch("src.engine.engine._extract_intent")
def test_unknown_intent(mock_extract):
    mock_extract.return_value = {"intent": None, "data": {}}

    result = process_request("What's the weather like today?")

    assert result["status"] == "unknown"