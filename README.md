# FitFindr 🛍️

A multi-tool AI agent that helps users find secondhand clothing and figure out how to wear it. Given a natural-language request, FitFindr searches a mock listings dataset, picks the best match, suggests an outfit using the user's existing wardrobe, and writes a shareable caption ("fit card"). Built for CodePath AI201, Project 2.

## Setup
python -m venv .venv

.venv\Scripts\activate          # Windows (Command Prompt)

pip install -r requirements.txt
Create a `.env` file in the repo root (already gitignored):
GROQ_API_KEY=your_key_here
Run the app:
python app.py
Then open the localhost URL shown in your terminal.

## Tool Inventory

### search_listings(description, size, max_price)
- **Inputs:** `description` (str) — keywords for the item; `size` (str | None) — case-insensitive substring size filter; `max_price` (float | None) — inclusive price ceiling.
- **Output:** `list[dict]` of matching listings sorted by relevance (best first). Each dict has id, title, description, category, style_tags, size, condition, price, colors, brand, platform.
- **Purpose:** Find candidate items matching the user's request.

### suggest_outfit(new_item, wardrobe)
- **Inputs:** `new_item` (dict) — the chosen listing; `wardrobe` (dict) — dict with an `items` list of wardrobe pieces.
- **Output:** `str` — 1–2 outfit suggestions referencing specific wardrobe pieces by name.
- **Purpose:** Style the found item against what the user already owns.

### create_fit_card(outfit, new_item)
- **Inputs:** `outfit` (str) — the suggestion from suggest_outfit; `new_item` (dict) — the listing.
- **Output:** `str` — a 2–4 sentence casual caption mentioning item name, price, and platform.
- **Purpose:** Produce a shareable OOTD-style caption for the look.

## How the Planning Loop Works

The loop runs in `run_agent(query, wardrobe)`. It initializes a `session` dict, parses the query into description/size/max_price using regex, then calls `search_listings`. It branches on the result: if the list is empty, it sets `session["error"]` to a helpful message and returns early — `suggest_outfit` and `create_fit_card` never run. If there are matches, it sets `selected_item = results[0]`, calls `suggest_outfit` on it, then `create_fit_card` on that outfit, storing each result in the session. Because the empty-results case terminates early, the agent's behavior changes with the input rather than running a fixed three-call sequence every time.

## State Management

A single `session` dict carries state through one interaction. The parser writes `session["parsed"]`; `search_listings` results go into `session["search_results"]` and the loop sets `session["selected_item"]`; `suggest_outfit` reads `selected_item` and writes `session["outfit_suggestion"]`; `create_fit_card` reads `outfit_suggestion` and `selected_item` and writes `session["fit_card"]`. The found item flows from search through to the later tools via the session, so the user never re-enters it. `session["error"]` is set only when the run ends early.

## Error Handling

- **search_listings — no matches:** Returns `[]` (never raises). The loop sets an error naming the search terms and any size/price filter and suggests loosening them, then stops before the later tools. Example: querying "designer ballgown" size XXS under $5 returns `[]`, and the agent responds: *No listings found for "designer ballgown" with size XXS and under $5. Try removing the size or price filter, or describing the item differently.*
- **suggest_outfit — empty wardrobe:** Prompts the LLM for general styling advice instead of named pairings, returning a useful string rather than crashing.
- **create_fit_card — empty outfit:** Returns a descriptive "⚠️ Can't make a fit card…" message string instead of raising an exception.

## Spec Reflection

The planning document helped me organize the project before coding by clearly defining each tool's responsibilities, inputs, outputs, and failure cases. Having the planning loop and state management written out beforehand made it easier to understand how information should flow between tools and where branching behavior should occur.

One way my implementation diverged from the original plan was in query parsing. The planning stage suggested that an LLM could be used to interpret user requests, but I chose to use regular expressions instead. Regex was faster, deterministic, and worked well for extracting sizes and price limits from user queries without requiring an additional AI call.


## AI Usage

I used Claude to help generate the initial implementations for the three tools. I provided the Tool Inventory section describing each tool's purpose, inputs, outputs, and error handling requirements. Claude generated starter code for the functions, but I reviewed and modified the implementation to ensure `search_listings` handled filtering correctly, returned an empty list when no matches existed, and that the other tools returned fallback responses instead of failing.

I also used Claude to help implement the planning loop and session-based state management. I provided the Planning Loop and State Management sections from the specification and described the desired workflow. Claude generated an initial version of the agent logic, but I verified that the code correctly branched when no search results were found and made adjustments to ensure the later tools were not called unconditionally. I tested both successful and unsuccessful search scenarios before finalizing the implementation.


## Testing

Run the tool tests with:
