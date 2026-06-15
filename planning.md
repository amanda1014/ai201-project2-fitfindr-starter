# FitFindr — planning.md

## Tools

### Tool 1: search_listings

**What it does:**
Filters the mock listings dataset by optional size and price, then scores the remaining items by keyword overlap with the description and returns them sorted best-match first.

**Input parameters:**
- `description` (str): keywords describing the item the user wants, e.g. "vintage graphic tee"
- `size` (str | None): size to filter by, matched case-insensitively as a substring (so "M" matches "S/M"); None skips size filtering
- `max_price` (float | None): inclusive maximum price; None skips price filtering

**What it returns:**
A `list[dict]` of matching listings sorted by relevance score (highest first). Each dict contains: id, title, description, category, style_tags (list), size, condition, price (float), colors (list), brand, platform.

**What happens if it fails or returns nothing:**
Returns an empty list `[]`. It never raises. The planning loop detects the empty list, sets an error message naming the search terms and filters used, and stops before calling the other tools.

---

### Tool 2: suggest_outfit

**What it does:**
Asks the LLM to combine the found item with named pieces from the user's wardrobe into 1–2 complete outfit suggestions.

**Input parameters:**
- `new_item` (dict): the listing dict the user is considering
- `wardrobe` (dict): a dict with an `items` key holding a list of wardrobe pieces (name, category, colors, style_tags, notes)

**What it returns:**
A non-empty `str` describing 1–2 outfits that reference specific wardrobe pieces by name.

**What happens if it fails or returns nothing:**
If `wardrobe['items']` is empty, the tool prompts the LLM for general styling advice instead of named pairings, so it still returns a useful non-empty string rather than crashing.

---

### Tool 3: create_fit_card

**What it does:**
Asks the LLM (at high temperature) to write a short, casual, shareable OOTD caption for the find.

**Input parameters:**
- `outfit` (str): the outfit suggestion produced by suggest_outfit
- `new_item` (dict): the listing dict for the thrifted item

**What it returns:**
A 2–4 sentence `str` caption mentioning the item name, price, and platform once each, that varies between runs for different inputs.

**What happens if it fails or returns nothing:**
If `outfit` is empty or whitespace-only, it returns a descriptive error message string ("⚠️ Can't make a fit card…") instead of raising.

---

### Additional Tools (if any)

None — the three required tools only.

---

## Planning Loop

The loop lives in `run_agent(query, wardrobe)`. It initializes a `session` dict, parses the query into description/size/max_price, then calls `search_listings`. It then branches on the result: if the result list is empty, it sets `session["error"]` to a helpful message and returns early, so suggest_outfit and create_fit_card never run. If the list has matches, it sets `selected_item = results[0]`, calls `suggest_outfit` on it, then `create_fit_card` on that outfit, storing each result in the session. The agent is done when it returns the session — either early via the error branch or after the fit card is built. Because the empty-results case terminates early, the agent does not call all three tools unconditionally.

---

## State Management

A single `session` dict is the source of truth for one interaction. The query parser writes `session["parsed"]`; search_listings writes `session["search_results"]` and the loop sets `session["selected_item"]`; suggest_outfit reads `selected_item` and writes `session["outfit_suggestion"]`; create_fit_card reads `outfit_suggestion` and `selected_item` and writes `session["fit_card"]`. The found item flows from search into the later tools through the session, so the user never re-enters it. `session["error"]` is set only when the interaction ends early.

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Returns `[]`; the loop sets an error message naming the search terms and any size/price filter, suggests loosening them, and stops before the later tools run. |
| suggest_outfit | Wardrobe is empty | Prompts the LLM for general styling advice instead of named pairings; still returns a useful non-empty string. |
| create_fit_card | Outfit input is missing or incomplete | Returns a descriptive "⚠️ Can't make a fit card…" message string instead of raising an exception. |

---

## Architecture
User query

│

▼

Planning Loop (run_agent)

│

├─► parse query → session["parsed"]

│

├─► search_listings(description, size, max_price)

│       │ results=[]

│       ├──► [ERROR] session["error"] set → return early

│       │

│       │ results=[item, ...]

│       ▼

│   session["selected_item"] = results[0]

│

├─► suggest_outfit(selected_item, wardrobe)

│       ▼

│   session["outfit_suggestion"] = "..."

│

└─► create_fit_card(outfit_suggestion, selected_item)

▼

session["fit_card"] = "..."

│

▼

Return session

---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**

I used Claude to help generate the initial implementations for the three tools based on the specifications above. I provided the tool descriptions, input parameters, expected outputs, and failure-handling requirements, and expected the generated code to follow those requirements exactly. I verified the implementations by testing different inputs, confirming that `search_listings` correctly filtered by description, size, and price, returned `[]` when no matches were found, and that the other tools returned useful fallback responses instead of crashing. I also ran pytest to ensure the functions behaved as expected.


**Milestone 4 — Planning loop and state management:**

I used Claude to help create the planning loop and session-based state management using the Planning Loop, State Management, and Architecture sections as guidance. I expected the agent to store intermediate results in the session dictionary and terminate early when `search_listings` returned no matches. I verified the behavior by testing both successful and unsuccessful search scenarios and confirmed that the agent branched correctly, only calling `suggest_outfit` and `create_fit_card` when a valid listing was available.


---

## A Complete Interaction (Step by Step)

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The query is parsed into description="vintage graphic tee", size=None, max_price=30.0. The agent calls `search_listings("vintage graphic tee", size=None, max_price=30.0)`, which returns matching listings sorted by relevance. The top result is the Y2K Baby Tee — Butterfly Print ($18, Depop). It is stored in `session["selected_item"]`.

**Step 2:**
The agent calls `suggest_outfit(selected_item, wardrobe)` with the tee and the example wardrobe. It returns a suggestion pairing the tee with the user's baggy straight-leg jeans and chunky white sneakers, stored in `session["outfit_suggestion"]`.

**Step 3:**
The agent calls `create_fit_card(outfit_suggestion, selected_item)`, which returns a casual caption mentioning the Y2K Baby Tee, $18, and Depop, stored in `session["fit_card"]`.

**Final output to user:**
The UI shows three panels: the top listing details, the outfit idea, and the shareable fit card caption.
