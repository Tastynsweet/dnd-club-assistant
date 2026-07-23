from unittest.mock import patch

from src.engine.engine import process_request

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

# Test 2: Register duplicate
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

# Test 3: List characters
@patch("src.engine.engine.list_characters")
@patch("src.engine.engine._extract_intent")
def test_list_characters(mock_extract, mock_list):
    mock_extract.return_value = {"intent": "list", "data": {}}
    mock_list.return_value = {"status": "success", "data": [{"name": "Feilong", "player": "Andy"}]}

    result = process_request("Show me all my characters.")

    assert result["status"] == "success"
    assert result["data"] == [{"name": "Feilong", "player": "Andy"}]

# Test 4: Reflection blocks incomplete input -- storage is NEVER called
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

# Test 5: Unknown intent
@patch("src.engine.engine._extract_intent")
def test_unknown_intent(mock_extract):
    mock_extract.return_value = {"intent": None, "data": {}}

    result = process_request("What's the weather like today?")

    assert result["status"] == "unknown"

# Test 6: list storage error passes through unchanged (line 124's "return result")
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

# Rules Lookup: get_rules_answer + process_request dispatch
@patch("src.engine.engine._get_client")
@patch("src.engine.engine.retrieve_context")
@patch("src.engine.engine.embed_text")
def test_get_rules_answer_success(mock_embed, mock_retrieve, mock_get_client):
    from src.engine.engine import get_rules_answer

    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_retrieve.return_value = {
        "status": "success",
        "data": {"chunks": ["Grappled rules text."], "sources": ["SRD (section 42)"]},
    }
    fake_block = type("FakeBlock", (), {
        "text": '{"answer": "Yes, with restrictions.", "source": "SRD (section 42)"}'
    })()
    fake_response = type("FakeResponse", (), {"content": [fake_block]})()
    mock_get_client.return_value.messages.create.return_value = fake_response

    result = get_rules_answer("Can a wizard cast a spell while grappled?")

    assert result["status"] == "success"
    assert result["data"]["answer"] == "Yes, with restrictions."
    assert result["data"]["source"] == "SRD (section 42)"

@patch("src.engine.engine.retrieve_context")
@patch("src.engine.engine.embed_text")
def test_get_rules_answer_not_found(mock_embed, mock_retrieve):
    from src.engine.engine import get_rules_answer

    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_retrieve.return_value = {"status": "no_match", "message": "no documents above similarity threshold"}

    result = get_rules_answer("What is the airspeed velocity of an unladen swallow?")

    assert result["status"] == "not_found"

def test_get_rules_answer_empty_input():
    from src.engine.engine import get_rules_answer

    result = get_rules_answer("   ")

    assert result["status"] == "empty_input"

@patch("src.engine.engine.get_rules_answer")
@patch("src.engine.engine._extract_intent")
def test_process_request_dispatches_rules_question(mock_extract, mock_get_answer):
    mock_extract.return_value = {
        "intent": "rules_question",
        "data": {"question": "Can a wizard cast a spell while grappled?"},
    }
    mock_get_answer.return_value = {
        "status": "success",
        "data": {"answer": "Yes, with restrictions.", "source": "SRD (section 42)"},
    }

    result = process_request("Can a wizard cast a spell while grappled?")

    assert result["status"] == "success"
    assert result["message"] == "Yes, with restrictions."
    mock_get_answer.assert_called_once_with("Can a wizard cast a spell while grappled?")

def test_parse_json_response_strips_markdown_fences():
    from src.engine.engine import _parse_json_response

    fenced = '```json\n{"answer": "Yes", "source": "SRD (section 1)"}\n```'
    result = _parse_json_response(fenced)

    assert result == {"answer": "Yes", "source": "SRD (section 1)"}

def test_parse_json_response_handles_unfenced_json():
    from src.engine.engine import _parse_json_response

    result = _parse_json_response('{"intent": "list", "data": {}}')

    assert result == {"intent": "list", "data": {}}

# Campaign/DM Matchmaking
@patch("src.engine.engine.query_campaigns_by_schedule")
def test_find_campaign_match_success(mock_query):
    from src.engine.engine import find_campaign_match
 
    mock_query.return_value = {
        "status": "success",
        "data": {"campaigns": [{"campaign_id": "camp_012", "name": "Lost Mine of Phandelver"}]},
    }
 
    result = find_campaign_match("Saturday one-shot please", day="Saturday", preference_tags=["one-shot"])
 
    assert result["status"] == "success"
    assert result["data"]["matches"][0]["campaign_id"] == "camp_012"
 
def test_find_campaign_match_unclear_request_with_no_day_or_tags():
    from src.engine.engine import find_campaign_match
 
    result = find_campaign_match("hi there")
 
    assert result["status"] == "unclear_request"
 
@patch("src.engine.engine.query_campaigns_by_schedule")
def test_find_campaign_match_no_match_passthrough(mock_query):
    from src.engine.engine import find_campaign_match
 
    mock_query.return_value = {"status": "no_match", "message": "no campaigns found for this schedule/preference"}
 
    result = find_campaign_match("Sunday horror campaign", day="Sunday", preference_tags=["horror"])
 
    assert result["status"] == "no_match"
 
@patch("src.engine.engine.find_campaign_match")
@patch("src.engine.engine._extract_intent")
def test_process_request_dispatches_matchmaking(mock_extract, mock_match):
    mock_extract.return_value = {
        "intent": "matchmaking",
        "data": {"day": "Saturday", "preference_tags": ["one-shot"]},
    }
    mock_match.return_value = {
        "status": "success",
        "data": {"matches": [{"campaign_id": "camp_012", "name": "Lost Mine of Phandelver"}]},
    }
 
    result = process_request("Looking for a Saturday one-shot")
 
    assert result["status"] == "success"
    assert result["data"][0]["campaign_id"] == "camp_012"