"""Thin client for the Scryfall card search API."""
import time
import requests

BASE_URL = "https://api.scryfall.com/cards/search"
REQUEST_DELAY_SECONDS = 0.1  # Scryfall asks for 50-100ms between requests
HEADERS = {
    "User-Agent": "SquabblinGoblins/0.1 (+https://github.com/Squabblin-bout-goblins/squabblin-goblins)",
    "Accept": "application/json",
}


def fetch_cards(query: str, exclude_basic_lands: bool = True):
    """Yield card dicts matching a Scryfall search query, following pagination.

    Uses unique=prints so every set printing, promo, and special edition comes
    back as its own row (foil/nonfoil pricing lives on each printing's own
    prices.usd / prices.usd_foil fields -- they aren't separate objects).

    exclude_basic_lands uses Scryfall's "Basic" supertype filter, which only
    matches the true basics (Mountain, Plains, Island, Swamp, Forest, Wastes)
    -- dual lands like Plateau are untouched.
    """
    effective_query = query
    if exclude_basic_lands:
        effective_query = f"({query}) -type:basic"

    url = BASE_URL
    params = {"q": effective_query, "unique": "prints"}

    while url:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        payload = response.json()

        for card in payload.get("data", []):
            yield card

        if payload.get("has_more"):
            url = payload["next_page"]
            params = None  # next_page is already a full URL with query params
            time.sleep(REQUEST_DELAY_SECONDS)
        else:
            url = None
