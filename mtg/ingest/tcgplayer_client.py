"""Thin client for the TCGPlayer pricing API.

Product matching is NOT done here by name -- a card name like "Goblin Welder"
has six different printings on TCGPlayer, each a different product with a
wildly different price. Scryfall already gives us the correct printing-specific
tcgplayer_id on every card, so we just batch-fetch prices by that ID.
"""
import os
import time

import requests

BASE_URL = "https://api.tcgplayer.com"
REQUEST_DELAY_SECONDS = 0.2
BATCH_SIZE = 50


def get_bearer_token() -> str:
    response = requests.post(
        f"{BASE_URL}/token",
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ["TCGPLAYER_PUBLIC_KEY"],
            "client_secret": os.environ["TCGPLAYER_PRIVATE_KEY"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": os.environ["TCGPLAYER_USER_AGENT"],
        "Accept": "application/json",
    }


def get_prices(token: str, product_ids: list[int]) -> list[dict]:
    """Fetch market prices for a batch of TCGPlayer product IDs."""
    if not product_ids:
        return []
    ids_param = ",".join(str(pid) for pid in product_ids)
    response = requests.get(
        f"{BASE_URL}/pricing/product/{ids_param}",
        headers=_headers(token),
        timeout=30,
    )
    if response.status_code == 404:
        return []
    response.raise_for_status()
    return response.json().get("results", [])


def fetch_prices_for_ids(product_ids: list[int]):
    """Yield price rows for the given TCGPlayer product IDs, batched."""
    token = get_bearer_token()

    for i in range(0, len(product_ids), BATCH_SIZE):
        batch = product_ids[i : i + BATCH_SIZE]
        for price_row in get_prices(token, batch):
            yield price_row
        time.sleep(REQUEST_DELAY_SECONDS)
