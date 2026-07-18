import builtins
from unittest.mock import Mock

from src.interface.cli import format_response, run_session


# ---------------------------------------------------------------------------
# Test 1: success with data list -> character name + player appear
# ---------------------------------------------------------------------------
def test_format_response_success_with_data():
    result = {
        "status": "success",
        "message": "Found 1 character(s).",
        "data": [{"name": "Feilong", "player": "Andy"}],
    }
    output = format_response(result)

    assert "Feilong" in output
    assert "Andy" in output


# ---------------------------------------------------------------------------
# Test 2: exists -> duplicate message appears
# ---------------------------------------------------------------------------
def test_format_response_exists():
    result = {"status": "exists", "message": "duplicate character name for this player"}
    output = format_response(result)

    assert "duplicate character name for this player" in output


# ---------------------------------------------------------------------------
# Test 3: incomplete -> each missing field name appears
# ---------------------------------------------------------------------------
def test_format_response_incomplete():
    result = {
        "status": "incomplete",
        "message": "I need a bit more information before I can save that character.",
        "missing": ["player", "class"],
    }
    output = format_response(result)

    assert "player" in output
    assert "class" in output


# ---------------------------------------------------------------------------
# Test 4: unknown -> help text with available actions appears
# ---------------------------------------------------------------------------
def test_format_response_unknown():
    result = {"status": "unknown", "message": "Could not determine what you're asking for."}
    output = format_response(result)

    assert "register" in output.lower()
    assert "list" in output.lower()


# ---------------------------------------------------------------------------
# Test 5: run_session with a mocked engine -> formatted response hits stdout
# ---------------------------------------------------------------------------
def test_run_session_prints_formatted_response(monkeypatch, capsys):
    inputs = iter(["Show me all my characters.", "quit"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    mock_process_fn = Mock(return_value={
        "status": "success",
        "message": "Found 1 character(s).",
        "data": [{"name": "Feilong", "player": "Andy"}],
    })

    run_session(process_fn=mock_process_fn)

    captured = capsys.readouterr()
    assert "Feilong" in captured.out
    assert "Andy" in captured.out
    mock_process_fn.assert_called_once_with("Show me all my characters.")