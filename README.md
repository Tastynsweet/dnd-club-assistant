# D&D Club Agentic Assistant

A conversational assistant for managing D&D club character sheets and answering rules questions, built with a three-layer architecture (interface → engine → storage) and powered by Claude Haiku 4.5 using the Tool Use and Reflection design patterns.

Currently supports:
- **Character registration** — describe a character in plain language and the assistant extracts and saves the structured record.
- **Character listing** — ask to see all characters, or filter by player.
- **Rules lookup** — ask a D&D 5e rules question and get a grounded, cited answer retrieved from the official SRD (System Reference Document), using local embeddings for retrieval and Claude for answer synthesis.

*(Campaign/DM Matchmaking is designed in `CONTRACT.md` but not yet implemented.)*

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Sheets access**: place a `service_account.json` (Google Cloud service account key) in the project root. The service account must be shared as an Editor on your Google Sheet. See `google_sheet_setup.md` for full setup steps.

3. **Claude API key**: create a `.env` file in the project root:
   ```
   ANTHROPIC_API_KEY=your_key_here
   ```

4. **Rules index**: build the local rules search index once (requires the D&D 5e SRD PDF, freely available from Wizards of the Coast under the Open Gaming License):
   ```bash
   python build_rules_index.py path/to/SRD-OGL_V5.1.pdf
   ```
   This downloads a small local embedding model (one-time) and produces `rules_index.json`. No API calls or cost are involved in this step -- retrieval runs entirely locally.

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

**Rules lookup:**
```
You: How does advantage stack?
Assistant: Advantage does not stack. If multiple situations affect a roll and
each one grants advantage, you still roll only one additional d20...
```

## Project Structure

| Path | Purpose |
|---|---|
| `src/storage/storage_handler.py` | Persists character records to Google Sheets via `gspread` |
| `src/storage/rules_handler.py` | Cosine-similarity retrieval over a local SRD embedding index |
| `src/storage/embeddings.py` | Local embedding model wrapper (no API key, no network calls at query time) |
| `src/engine/engine.py` | Tool Use (intent extraction) + Reflection (completeness check) + rules Q&A, dispatches to storage |
| `src/interface/cli.py` | Presentation layer — formats engine responses and runs the interactive session |
| `build_rules_index.py` | One-time script: extracts, chunks, and embeds the SRD into `rules_index.json` |
| `tests/storage/`, `tests/engine/`, `tests/interface/` | Unit tests per layer, all mocked (no live API/Sheets/model calls needed to run) |
| `CONTRACT.md` | Full functionality spec, architecture mapping, and interface contracts |

## Known Limitations

Rules lookup retrieval occasionally misses relevant chunks when a question spans multiple rule sections (e.g. an interaction between two named conditions), since only the top 3 most similar chunks are retrieved per query. Increasing `top_k`, smarter chunk boundaries, or a reranking step would improve this.