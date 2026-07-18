# D&D Club Agentic Assistant

A conversational assistant for managing D&D club character sheets, built with a three-layer architecture (interface → engine → storage) and powered by an LLM agent using the Tool Use and Reflection design patterns.

Currently supports:
- **Character registration** — describe a character in plain language and the assistant extracts and saves the structured record.
- **Character listing** — ask to see all characters, or filter by player.

*(Rules Lookup and Campaign Matchmaking are designed in `CONTRACT.md` but not yet implemented — see Project Structure below.)*

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Sheets access**: place a `service_account.json` (Google Cloud service account key) in the project root. The service account must be shared as an Editor on your Google Sheet. See `google_sheet_setup.md` for full setup steps.

3. **Gemini API key**: create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_key_here
   ```

## How to Run

```bash
python -m src.interface.cli
```

Type your request in plain English. Type `quit` or `exit` to leave.

## Usage Examples

**Registering a character:**
```
You: Register Feilong, a level 4 Monk played by Andy.
Assistant: Saved Feilong for Andy.
```

**Listing characters:**
```
You: Show me all my characters.
Assistant: Found 1 character(s).
  - Feilong (Andy)
```

**Incomplete registration:**
```
You: Register Bob.
Assistant: I need a bit more information before I can save that character.
  Missing: player, class, level, stats
```

## Project Structure

| Path | Purpose |
|---|---|
| `src/storage/storage_handler.py` | Persists character records to Google Sheets via `gspread` |
| `src/engine/engine.py` | Tool Use (intent extraction) + Reflection (completeness check), dispatches to storage |
| `src/interface/cli.py` | Presentation layer — formats engine responses and runs the interactive session |
| `tests/storage/`, `tests/engine/`, `tests/interface/` | Unit tests per layer, all mocked (no live API/Sheets calls needed to run) |
| `CONTRACT.md` | Full functionality spec, architecture mapping, and interface contracts |