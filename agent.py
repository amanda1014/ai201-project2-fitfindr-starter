"""
agent.py — The FitFindr planning loop.
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


def _new_session(query: str, wardrobe: dict) -> dict:
    """Initialize a fresh session dict for one user interaction."""
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from a natural language query
    using regex. Returns a dict with keys: description, size, max_price.
    """
    q = query or ""

    # max_price: look for "$30", "under 30", "under $40"
    max_price = None
    price_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)", q)
    if re.search(r"under|below|max|less than|\$", q, re.IGNORECASE) and price_match:
        max_price = float(price_match.group(1))

    # size: look for "size M", "size 8", "in size XS"
    size = None
    size_match = re.search(
        r"size\s+(XXS|XS|S|M|L|XL|XXL|\d{1,2})",
        q,
        re.IGNORECASE,
    )
    if size_match:
        size = size_match.group(1).upper()

    # description: strip out the size/price phrases, keep the rest as keywords
    description = q
    description = re.sub(r"size\s+\S+", "", description, flags=re.IGNORECASE)
    description = re.sub(r"(under|below|max|less than)\s*\$?\s*\d+(\.\d+)?", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\$\s*\d+(\.\d+)?", "", description)
    description = description.strip()

    return {"description": description, "size": size, "max_price": max_price}


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
    """
    # Step 1: init session
    session = _new_session(query, wardrobe)

    # Step 2: parse the query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # Step 3: search
    results = search_listings(
        parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )
    session["search_results"] = results

    # Branch: no results -> set error and return early. Do NOT call suggest_outfit.
    if not results:
        bits = []
        if parsed["size"]:
            bits.append(f"size {parsed['size']}")
        if parsed["max_price"] is not None:
            bits.append(f"under ${parsed['max_price']:.0f}")
        constraints = (" with " + " and ".join(bits)) if bits else ""
        session["error"] = (
            f"No listings found for \"{parsed['description']}\"{constraints}. "
            "Try removing the size or price filter, or describing the item differently."
        )
        return session

    # Step 4: select top result
    session["selected_item"] = results[0]

    # Step 5: suggest outfit
    session["outfit_suggestion"] = suggest_outfit(
        session["selected_item"], wardrobe
    )

    # Step 6: create fit card
    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"], session["selected_item"]
    )

    # Step 7: return
    return session


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")