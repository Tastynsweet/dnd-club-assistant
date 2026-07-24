# D&D Session Assistant - Design Document

## 1. Overview

Architecture and implementation design for the D&D Session Assistant, a
conversational agent built to be useful both during game sessions (quick
rules lookups without breaking the table's flow) and between them (character
management, finding your next campaign). Covers Rules Lookup, Character
Sheet Management, and Campaign/DM Matchmaking. See `REQUIREMENTS_SPEC.md`
for functional requirements.

## 2. Architecture

**3-Tier Design:** Interface -> Engine -> Storage

```
┌───────────────────────────────────────────────────┐
│  Interface  (src/interface/cli.py)                │
│  └── Collects raw text, calls the engine, formats │
│      and prints the result. No AI calls, no       │
│      storage access.                              │
├───────────────────────────────────────────────────┤
│  Engine  (src/engine/engine.py)                   │
│  └── Tool Use: one Claude call classifies intent  │
│      (register / list / rules_question /          │
│      matchmaking / null) and extracts structured  │
│      data.                                        │
│  └── Reflection: a second Claude call validates   │
│      completeness for character registration      │
│      before any storage write.                    │
├───────────────────────────────────────────────────┤
│  Storage  (src/storage/)                          │
│  ├── storage_handler.py    — character save/list  │
│  ├── rules_handler.py      — SRD chunk retrieval  │
│  ├── embeddings.py         — local embedding model│
│  └── campaigns_handler.py  — campaign matchmaking │
└───────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|---|---|
| LLM (intent + generation) | Claude Haiku 4.5 (Anthropic API) |
| Embeddings (retrieval) | `sentence-transformers` (`all-MiniLM-L6-v2`), local, free |
| Character/campaign storage | Google Sheets via `gspread` |
| Rules index storage | Local JSON file (chunk text + embedding per entry) |
| Interface | CLI (`src/interface/cli.py`) |
| Testing | `pytest` + `pytest-cov`, all layers mocked |

## 3. Data Models

```
Character:  { "id": "char_045", "name": "Feilong", "player": "Andy",
              "class": "Monk", "level": 4, "stats": {...}, "inventory": [...] }

Campaign:   { "campaign_id": "camp_012", "name": "Lost Mine of Phandelver",
              "day": "Saturday", "level_range": "1-5",
              "preference_tags": "low-level, one-shot", "contact": "..." }

Rules chunk: { "id": 500, "text": "...800 chars of SRD text...",
               "source": "SRD 5.1 (section 500)", "embedding": [0.1, ...] }
```

Google Sheets layout:
- **Characters** tab — columns: `id, name, player, class, level, stats, inventory`
- **Campaigns** tab — columns: `campaign_id, name, day, level_range, preference_tags, contact`
- Rules index lives outside Sheets, in `rules_index.json` (local file, not a live database)

## 4. Interface Contracts

### Functionality 1: Rules Lookup
- `interface -> engine`: `get_rules_answer(user_query: str) -> response_payload`
- `engine -> storage`: `retrieve_context(query_embedding: vector, top_k: int) -> response_payload`

### Functionality 2: Character Management
- `interface -> engine`: `process_request(user_input: str) -> response_payload`
- `engine -> storage`: `save_character(character_data) -> response_payload`, `list_characters(player) -> response_payload`

### Functionality 3: Campaign Matchmaking
- `interface -> engine`: `find_campaign_match(request_text, day, preference_tags) -> response_payload`
- `engine -> storage`: `query_campaigns_by_schedule(day, preference_tags) -> response_payload`

All three functionalities share a single `process_request(user_input: str)`
entry point at the interface boundary (see Key Technical Decisions below);
the per-functionality functions above are what the engine calls internally
once intent is classified.

## 5. Key Technical Decisions

- **Unified engine entry point instead of one function per functionality.**
  The original design specified a separate typed function per functionality
  at the interface/engine boundary. The final implementation consolidates
  these behind a single `process_request(user_input: str) -> dict`, which
  uses one Claude call to classify intent across all cases and dispatches
  internally. This reduced duplication in the interface layer and made
  adding new intents a same-function extension rather than a new interface
  method.

- **Local embeddings instead of a hosted embeddings API.** Anthropic does
  not offer a first-party embeddings endpoint. Rather than add a second paid
  API dependency, retrieval embeddings are generated with a local
  `sentence-transformers` model. Rules Lookup's retrieval step is entirely
  free and runs offline after a one-time index build; only the final
  answer-synthesis call uses the paid Claude API.

- **Word-window chunking instead of section-boundary chunking.** The SRD is
  chunked into ~800-character word-window segments with ~150-character
  overlap, rather than by rule/section boundaries as originally envisioned,
  since reliable section-boundary detection from the PDF's extracted text
  was not feasible in the available time. Known limitation: retrieval
  occasionally underperforms on questions spanning multiple rule sections
  (e.g. how the Grappled condition interacts with spellcasting).

- **Campaign matchmaking is read-only by design.** Per the original
  contract, the only `engine -> storage` function specified for
  Functionality 3 is `query_campaigns_by_schedule` — there is no function to
  create new campaign records through the assistant. Campaign data is
  assumed to be seeded/managed outside the chat interface; the assistant's
  role is purely to match against existing records.

- **Google Sheets and a local JSON file instead of a dedicated database.**
  Both choices prioritize simplicity and zero infrastructure cost over
  production scalability, an explicit tradeoff given project scope and
  timeline. Google Sheets also provides a free, visual UI for debugging
  character/campaign data during development.

- **Defensive JSON parsing around all Claude responses.** Claude
  occasionally wraps structured JSON output in markdown code fences
  (` ```json ... ``` `) despite explicit prompt instructions not to. A
  shared `_parse_json_response()` helper strips fences defensively before
  parsing, discovered and fixed after live testing surfaced the failure
  mode (see Testing Notes).

## 6. Testing Notes

45 automated tests across all three layers, all using dependency injection
and mocking (fake worksheets, fake embeddings, mocked Claude responses) —
no test requires a live network call, live Google Sheets connection, or real
API key to run. Coverage is 88% overall; the uncovered ~12% is limited to
real-credential authentication code paths (Google Sheets auth, the Claude
client constructor) that are intentionally excluded from unit testing and
instead verified via a separate live connectivity check
(`verify_connection.py`) and manual end-to-end walkthrough.

## 7. Known Limitations (Beyond Current Scope)

These were not part of the original Lab 4 contract and are documented here for completeness, not as bugs against the current spec:

No per-user access control. player is a freeform field extracted from user input, not an authenticated identity, so any user of the assistant can list or reference any other player's characters by name. A production deployment (e.g. as a Discord bot) would tie requests to the platform's real user identity (e.g. Discord's message.author.id) rather than trusting free text.
No character editing. Only save_character (create) and list_characters (read) exist; there is no way to update an existing character's level, HP, inventory, etc. through the assistant. Changes currently require manually editing the Google Sheet.