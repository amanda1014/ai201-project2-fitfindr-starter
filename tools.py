"""
tools.py — The three required FitFindr tools.
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()

MODEL = "llama-3.3-70b-versatile"


def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ──────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Returns a list of matching listing dicts sorted by relevance (best first).
    Returns an empty list if nothing matches — does NOT raise.
    """
    listings = load_listings()

    # Build keyword set from the description
    keywords = [w.lower() for w in re.findall(r"\w+", description or "")]

    scored = []
    for item in listings:
        # Price filter
        if max_price is not None and item["price"] > max_price:
            continue
        # Size filter (case-insensitive substring match)
        if size is not None:
            if size.lower() not in str(item.get("size", "")).lower():
                continue

        # Score by keyword overlap against title, description, style_tags
        haystack = " ".join([
            item.get("title", ""),
            item.get("description", ""),
            " ".join(item.get("style_tags", [])),
            item.get("category", ""),
            " ".join(item.get("colors", [])),
            str(item.get("brand", "") or ""),
        ]).lower()

        score = sum(1 for kw in keywords if kw in haystack)

        if score > 0:
            scored.append((score, item))

    # Sort by score, highest first
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored]


# ── Tool 2: suggest_outfit ───────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.
    Handles an empty wardrobe by giving general styling advice.
    Returns a non-empty string.
    """
    client = _get_groq_client()

    item_desc = (
        f"{new_item.get('title', 'item')} — "
        f"{new_item.get('description', '')} "
        f"(style: {', '.join(new_item.get('style_tags', []))}; "
        f"colors: {', '.join(new_item.get('colors', []))})"
    )

    items = wardrobe.get("items", [])

    if not items:
        prompt = (
            f"A user just found this secondhand piece: {item_desc}. "
            "They have not entered any wardrobe items yet. "
            "Suggest general styling ideas: what kinds of pieces pair well with it, "
            "what vibe it suits, and how to wear it. Keep it to 2-3 sentences, "
            "concrete and friendly."
        )
    else:
        wardrobe_lines = "\n".join(
            f"- {it['name']} ({it['category']}, {', '.join(it.get('colors', []))})"
            for it in items
        )
        prompt = (
            f"A user just found this secondhand piece: {item_desc}.\n\n"
            f"Their current wardrobe:\n{wardrobe_lines}\n\n"
            "Suggest 1-2 complete outfit combinations that pair the new item with "
            "SPECIFIC named pieces from their wardrobe above. Reference the pieces by "
            "name. Keep it to 2-4 sentences, concrete and stylish."
        )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ──────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.
    Returns a descriptive error message string if outfit is empty — does NOT raise.
    """
    if not outfit or not outfit.strip():
        return (
            "⚠️ Can't make a fit card — no outfit suggestion was provided. "
            "Try finding an item and generating an outfit first."
        )

    title = new_item.get("title", "this piece")
    price = new_item.get("price", "?")
    platform = new_item.get("platform", "a thrift app")

    prompt = (
        f"Write a short, casual Instagram/TikTok caption (2-4 sentences) for an "
        f"outfit-of-the-day post about a thrifted find.\n\n"
        f"Item: {title}, ${price}, found on {platform}.\n"
        f"Outfit: {outfit}\n\n"
        "Make it sound like a real person's OOTD caption — casual, a little excited, "
        "NOT a product description. Mention the item name, price, and platform once "
        "each, naturally. Capture the vibe of the outfit in specific terms. "
        "A tasteful emoji or two is fine."
    )

    client = _get_groq_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
    )
    return response.choices[0].message.content.strip()