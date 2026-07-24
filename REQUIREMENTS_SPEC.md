# D&D Session Assistant - Requirements Specification

## Overview
The D&D Session Assistant is a conversational LLM agent designed for use both during game sessions (quick rules lookups) and between them (managing characters, finding your next campaign).

## Functional Requirements

### Functionality 1: Rules Lookup Chatbot

#### Input:
* Free-text rules question (e.g. "Can a wizard cast a spell while grappled?", "How does advantage stack?")

#### Output:
* Natural-language answer grounded in retrieved rulebook text (SRD 5.1), with a citation to the source section.

#### Success:
* Returned answer is accurate to the rulebook source and cites the relevant section.

#### Failure/Edge Cases:
* Question not covered by the rulebook corpus (e.g. homebrew rules) --> return fallback: "This isn't covered in the core rules; check with your DM."
* Empty input --> prompt user to enter a question.
* Retrieval returns no matching context above a similarity threshold --> treated as not-found rather than guessing.

### Functionality 2: Character Sheet Management

#### Input:
* Free-text description of a character (e.g. name, class, level, stats, inventory).

#### Output:
* Submission result message (success, exists, incomplete) and, on lookup, the stored character list.

#### Success:
* Required fields (character name, owner/player, class, level, stats) are present and the record is saved.

#### Failure/Edge Cases:
* Missing required field(s) --> return incomplete with the list of missing fields.
* Duplicate character name for the same player --> return exists.
* Stat values or other malformed data --> handled by the Reflection step before any write occurs.
* Storage write failure (e.g. connectivity) --> return error rather than crashing.

### Functionality 3: Campaign / DM Matchmaking

#### Input:
* A request describing availability and interest (e.g. "Looking for a Saturday campaign, prefer low-level one-shots").

#### Output:
* A ranked list of matching campaigns based on schedule/preference overlap.

#### Success:
* Returns at least one relevant match when a compatible campaign exists.

#### Failure/Edge Cases:
* No matches for the given schedule/preference --> return no_match instead of an empty silent result.
* Malformed/ambiguous request (no day or preferences parseable) --> return unclear_request.
* Matched campaign with no contact info on file --> flagged as incomplete_contact rather than silently omitted.