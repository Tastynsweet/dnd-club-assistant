from unittest.mock import patch

from src.engine.engine import process_request

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

@patch("src.engine.engine.list_characters")
@patch("src.engine.engine._extract_intent")
def test_list_characters(mock_extract, mock_list):
    mock_extract.return_value = {"intent": "list", "data": {}}
    mock_list.return_value = {"status": "success", "data": [{"name": "Feilong", "player": "Andy"}]}

    result = process_request("Show me all my characters.")

    assert result["status"] == "success"
    assert result["data"] == [{"name": "Feilong", "player": "Andy"}]

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

@patch("src.engine.engine._extract_intent")
def test_unknown_intent(mock_extract):
    mock_extract.return_value = {"intent": None, "data": {}}

    result = process_request("What's the weather like today?")

    assert result["status"] == "unknown"

@patch("src.engine.engine.list_characters")
@patch("src.engine.engine._extract_intent")
def test_list_characters_error_passthrough(mock_extract, mock_list):
    mock_extract.return_value = {"intent": "list", "data": {}}
    mock_list.return_value = {"status": "error", "message": "sheet unreachable"}

    result = process_request("Show me all my characters.")

    assert result == {"status": "error", "message": "sheet unreachable"}

@patch("src.engine.engine._get_client")
def test_extract_intent_parses_model_json_response(mock_get_client):
    from src.engine.engine import _extract_intent

    fake_block = type("FakeBlock", (), {"text": '{"intent": "list", "data": {}}'})()
    fake_response = type("FakeResponse", (), {"content": [fake_block]})()
    mock_get_client.return_value.messages.create.return_value = fake_response

    result = _extract_intent("Show me all my characters.")

    assert result == {"intent": "list", "data": {}}

@patch("src.engine.engine._get_client")
def test_reflect_parses_model_json_response(mock_get_client):
    from src.engine.engine import _reflect

    fake_block = type("FakeBlock", (), {"text": '{"complete": true, "missing": []}'})()
    fake_response = type("FakeResponse", (), {"content": [fake_block]})()
    mock_get_client.return_value.messages.create.return_value = fake_response

    result = _reflect("register", {"name": "Feilong"})

    assert result == {"complete": True, "missing": []}