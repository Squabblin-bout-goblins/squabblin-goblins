"""Thin client for the eBay Browse API (active listing search), using the
OAuth client credentials grant for an application access token.
"""
import base64
import os
import time

import requests

TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
SCOPE = "https://api.ebay.com/oauth/api_scope"
REQUEST_DELAY_SECONDS = 0.2
CCG_INDIVIDUAL_CARDS_CATEGORY = "183454"


def get_application_token() -> str:
    credentials = f"{os.environ['EBAY_APP_ID']}:{os.environ['EBAY_CERT_ID']}"
    basic_auth = base64.b64encode(credentials.encode()).decode()

    response = requests.post(
        TOKEN_URL,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}",
        },
        data={"grant_type": "client_credentials", "scope": SCOPE},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def search_items(token: str, query: str, limit: int = 50) -> list[dict]:
    """Search active listings by keyword, scoped to the CCG Individual Cards
    category so we don't pick up sealed boxes, playmats, or unrelated items.
    Returns raw item_summary dicts.
    """
    response = requests.get(
        SEARCH_URL,
        params={
            "q": query,
            "category_ids": CCG_INDIVIDUAL_CARDS_CATEGORY,
            "limit": limit,
        },
        headers={
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("itemSummaries", [])


def fetch_listings_for_queries(queries: list[str], limit_per_query: int = 50):
    """Yield (query, item) pairs for each query, fetching a fresh token once."""
    token = get_application_token()

    for query in queries:
        for item in search_items(token, query, limit_per_query):
            yield query, item
        time.sleep(REQUEST_DELAY_SECONDS)
