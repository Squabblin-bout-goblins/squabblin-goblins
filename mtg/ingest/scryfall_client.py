"""Thin client for the Scryfall card search API."""
import time
import requests

BASE_URL = "https://api.scryfall.com/cards/search"
REQUEST_DELAY_SECONDS = 0.1  # Scryfall asks for 50-100ms between requests
HEADERS = {
    "User-Agent": "SquabblinGoblins/0.1 (+https://github.com/Squabblin-bout-goblins/squabblin-goblins)",
    "Accept": "application/json",
}


def fetch_cards(query: str):
    """Yield card dicts matching a Scryfall search query, following pagination."""
    url = BASE_URL
    params = {"q": query}

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
