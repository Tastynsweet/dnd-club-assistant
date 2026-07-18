import builtins
from unittest.mock import Mock

from src.interface.cli import format_response, run_session

def test_format_response_success_with_data():
    result = {
        "status": "success",
        "message": "Found 1 character(s).",
        "data": [{"name": "Feilong", "player": "Andy"}],
    }
    output = format_response(result)

    assert "Feilong" in output
    assert "Andy" in output

def test_format_response_exists():
    result = {"status": "exists", "message": "duplicate character name for this player"}
    output = format_response(result)

    assert "duplicate character name for this player" in output

def test_format_response_incomplete():
    result = {
        "status": "incomplete",
        "message": "I need a bit more information before I can save that character.",
        "missing": ["player", "class"],
    }
    output = format_response(result)

    assert "player" in output
    assert "class" in output

def test_format_response_unknown():
    result = {"status": "unknown", "message": "Could not determine what you're asking for."}
    output = format_response(result)

    assert "register" in output.lower()
    assert "list" in output.lower()

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

def test_format_response_error_fallback():
    result = {"status": "error", "message": "failed to write row: connection reset"}
    output = format_response(result)

    assert "failed to write row" in output

def test_run_session_defaults_to_process_request(monkeypatch, capsys):
    inputs = iter(["quit"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    with_default = Mock(return_value={"status": "unknown", "message": "n/a"})
    monkeypatch.setattr("src.interface.cli.process_request", with_default)

    run_session()

    with_default.assert_not_called()

def test_run_session_handles_eof(monkeypatch, capsys):
    def raise_eof(_):
        raise EOFError

    monkeypatch.setattr(builtins, "input", raise_eof)

    run_session(process_fn=Mock())

    captured = capsys.readouterr()
    assert "Goodbye" in captured.out

def test_run_session_skips_blank_lines(monkeypatch, capsys):
    inputs = iter(["", "   ", "quit"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    mock_process_fn = Mock()
    run_session(process_fn=mock_process_fn)

    mock_process_fn.assert_not_called()