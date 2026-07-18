# Task 2 Worksheet (Submission File)

## Project: D&D Club Agentic Assistant

## Part A: Functionality (2-4 Functionalities Required)

### Functionality 1: <Rules Lookup Chatbot>
- Input: 
    - Free-text rules question (ex. "Can a wizard cast a spell while grappled?", "How does advantage stack?")
- Output: 
    - Natural-language answer grounded in retrieved rulebook text (with a reference to the relevant rule/section)
- Success: 
    - Returned answer is accurate to the rulebook source and cites the relevant section.
- Failure/Edge Cases: 
    - Question not covered by the rulebook corpus (ex. homebrew rules) -> return fallback: "This isn't covered in the core rules; check with your DM."
    - Empty input -> prompt user to enter a question
    - Ambiguous question referencing multiple editions/rulesets -> ask a clarifying question (ex. "Which edition are you using?")
    - Retrieval returns no matching context above a similar threshold -> treat as not-found rather than guessing


### Functionality 2: <Character Sheet Management>
- Input: 
    - Free-text or form submission with character fields (ex. name, class, level, stats, spells, etc)
- Output:
    - Submission result message (success, exists, incomplete) and, on lookup, the stored character sheet
- Success:
    - Required fields (character name, owner/player, class, level) are present, stats are validated within legal ranges, and the record is saved
- Failure/Edge Cases:
    - Missing required field(s) -> return incomplete with list of missing fields
    - Duplicate character name for the same player -> return exists
    - Stat values outside legal range -> return validation error
    - Free-text inventory list needs parsing into structured items before storing

### Functionality 3: <Campaign / DM Matchmaking>
- Input: 
    - A request describing availability and interest (ex. "Looking for a Saturday campaign, prefer low-level one-shots")
- Output:
    - A ranked list of matchmaking campaigns for players or matchamking players for DMS, based on schedule/preference overlap
- Success:
    - Returns at least one relevant matchc when a compatible campaign/player exists
- Failure/Edge Cases:
    - No matches for the given schedule/preference -> return no_match instead of an empty silent result
    - Malformed/ambiguous request -> ask a clarifying question or return unclear_request
    - Matched campaign/player has no contact info on file -> flag result as incomplete_contact

## Part B: Architecture Mapping
For each functionality, map responsibilities to components.

### Functionality 1 Mapping
- `interface` responsibilities: collect member's typed rules question, display the LLM's answer or fallback/clarifying message
- `engine` responsibilities: embed/query the question, retrieve relevant rulebook chunks (RAG), detect ambiguous edition references, call Gemini to generate a grounded, cited answer, apply the not-found fallback rule
- `storage` responsibilities: hold the rulebook text in a retrivable, indexed form chunked by section or rule

### Functionality 2 Mapping
- `interface` responsibilities: present the character creation/edit form, display the result message and the character sheet on lookup
- `engine` responsibilities: validate required fields and stat ranges, parse free-text inventory into structured items(LLM-assisted parsing optional)
- `storage` responsibilities: check for duplicate character names per player, persist the validated character record, serve lookups by player or character name

### Functionality 3 Mapping
- `interface` responsibilities: collect the player's or DM's availability/preference request, display ranked match results
- `engine` responsibilities: interpret the requrest (LLM function calling), query storage for campaigns or player by schedule/preference, rank/filter matches, flag incomplete contact info
- `storage` responsibilities: serve campaign and player records filtered/queried by schedule/preference; no logic beyond lookup and filtering

## Part C: Interface Contracts

### Functionality 1

#### `interface -> engine`
- Function(s): get_rules_answer(user_query: str) -> response_payload
- Input payload: {"query": "Can a wizard cast a spell while grappled?"}
- Return payload/status: {"status": "success", "data": {"answer": "Yes, as long as the spell has no somatic component requiring both hands...", "source": "PHB Ch.9, Conditions - Grappled"}}
- Failure statuses: {"status": "not_found", "message": "This isn't covered in the core rules; check with your DM."}, {"status": "clarify", "message": "Which edition are you using?"}

#### `engine -> storage`
- Function(s): retrieve_context(query_embedding: vector, top_k: int) -> response_payload
- Input payload: {"query_embedding": [...], "top_k": 3}
- Return payload/status: {"status": "success", "data": {"chunks": ["...", "..."], "sources": ["PHB Ch.9"]}}
- Failure statuses: {"status": "no_match", "message": "no documents above similarity threshold"}

### Functionality 2

#### `interface -> engine`
- Function(s): parse_character_sheet(raw_text: str) -> response_payload
- Input payload: {"raw_text": "name: Thistle, player: Andy, class: Wizard, level: 3, str: 8, dex: 14, int: 18, inventory: staff, spellbook, healing potion"}
- Return payload/status: {"status": "success", "data": {"name": "Feilong", "player": "Andy", "class": "Monk", "level": 4, "stats": {"str": 12, "dex": 20, "cons: "11", "int": 10, "wis: 16, "cha": 11}, "inventory": ["staff", "spellbook", "healing potion"]}}
- Failure statuses: {"status": "incomplete", "missing": ["level"]}, {"status": "invalid_stat", "message": "str value out of legal range"}

#### `engine -> storage`
- Function(s): save_character(character_data: character_record) -> response_payload
- Input payload: {"name": "Feilong", "player": "Andy", "class": "Monk", "level": 4, "stats": {...}, "inventory": [...]}
- Return payload/status: {"status": "success", "id": "char_045"}
- Failure statuses: {"status": "exists", "message": "duplicate character name for this player"}

### Functionality 3

#### `interface -> engine`
- Function(s): match_campaign_request(request_text: str) -> response_payload
- Input payload: {"request_text": "Looking for a Saturday campaign, prefer low-level one-shots"}
- Return payload/status: {"status": "success", "data": {"matches": [{"campaign_id": "camp_012", "name": "Lost Mine of Phandelver", "schedule": "Saturdays 4pm", "level_range": "1-5"}]}}
- Failure statuses: {"status": "unclear_request", "message": "could not parse schedule or preferences"}

#### `engine -> storage`
- Function(s): query_campaigns_by_schedule(day: str, preference_tags: list[str]) -> response_payload
- Input payload: {"day": "Saturday", "preference_tags": ["low-level", "one-shot"]}
- Return payload/status: {"status": "success", "data": {"campaigns": ["camp_012", "camp_019"]}}
- Failure statuses: {"status": "no_match", "message": "no campaigns found for this schedule/preference"}

## Part D: Implementation Notes (Lab 6–7 Evolution)

The interface/engine contract evolved from the original Part C design during implementation:

- `parse_character_sheet(raw_text)` was superseded by a single unified entry point,
  `process_request(user_input: str) -> dict`, which handles both character registration
  and character listing under one function using LLM-based intent classification
  (Tool Use pattern) rather than separate typed functions per intent.
- A new `engine -> storage` function, `list_characters(player: str = None) -> response_payload`,
  was added to support the "list my characters" intent. Return payload:
  `{"status": "success", "data": [...]}`.
- `save_character` gained an independent required-keys check inside the storage layer
  itself (in addition to the engine's Reflection step), as defense-in-depth: even if the
  engine's Reflection call is ever bypassed or misconfigured, storage will not silently
  accept an incomplete record.