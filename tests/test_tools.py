from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── search_listings ──────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []   # empty list, no exception

def test_search_price_filter():
    results = search_listings("tee", size=None, max_price=20)
    assert all(item["price"] <= 20 for item in results)


# ── suggest_outfit ───────────────────────────────────────────────────

def test_suggest_outfit_with_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    out = suggest_outfit(results[0], get_example_wardrobe())
    assert isinstance(out, str)
    assert len(out) > 0

def test_suggest_outfit_empty_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    out = suggest_outfit(results[0], get_empty_wardrobe())
    assert isinstance(out, str)
    assert len(out) > 0   # general advice, not a crash


# ── create_fit_card ──────────────────────────────────────────────────

def test_fit_card_empty_outfit():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    card = create_fit_card("", results[0])
    assert isinstance(card, str)
    assert len(card) > 0   # error message string, not an exception