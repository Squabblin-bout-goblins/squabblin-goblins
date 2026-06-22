"""Pull active eBay listings for each unique goblin card name and store them.

Unlike TCGPlayer, eBay search is keyword/title based, not an exact printing
match -- a single query can return listings spanning several printings,
conditions, and sellers. We store every listing raw rather than trying to
force a one-to-one card match; that ambiguity is itself useful signal (e.g.
asking-price spread across sellers for the "same" card).
"""
import os

import psycopg2
from dotenv import load_dotenv

from ebay_client import fetch_listings_for_queries

load_dotenv()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ebay_listings (
    item_id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    title TEXT,
    price NUMERIC,
    currency TEXT,
    condition TEXT,
    item_url TEXT,
    seller_username TEXT,
    fetched_at TIMESTAMPTZ DEFAULT now()
);
"""

UPSERT_SQL = """
INSERT INTO ebay_listings (item_id, query, title, price, currency, condition, item_url, seller_username)
VALUES (%(item_id)s, %(query)s, %(title)s, %(price)s, %(currency)s, %(condition)s, %(item_url)s, %(seller_username)s)
ON CONFLICT (item_id) DO UPDATE SET
    price = EXCLUDED.price,
    condition = EXCLUDED.condition,
    fetched_at = now();
"""


PROXY_KEYWORDS = ("proxy", "custom art", "playtest", "fake", "replica", "altered art", "art card")


def is_likely_proxy(title: str) -> bool:
    lowered = (title or "").lower()
    return any(keyword in lowered for keyword in PROXY_KEYWORDS)


def to_row(query: str, item: dict) -> dict:
    price = item.get("price") or {}
    seller = item.get("seller") or {}
    return {
        "item_id": item.get("itemId"),
        "query": query,
        "title": item.get("title"),
        "price": price.get("value"),
        "currency": price.get("currency"),
        "condition": item.get("condition"),
        "item_url": item.get("itemWebUrl"),
        "seller_username": seller.get("username"),
    }


def main():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)

    cur.execute("SELECT DISTINCT name FROM cards ORDER BY name;")
    card_names = [row[0] for row in cur.fetchall()]
    queries = [f"{name} mtg" for name in card_names]
    print(f"Searching eBay for {len(queries)} card names...")

    count = 0
    skipped = 0
    for query, item in fetch_listings_for_queries(queries):
        if is_likely_proxy(item.get("title")):
            skipped += 1
            continue
        cur.execute(UPSERT_SQL, to_row(query, item))
        count += 1

    print(f"Stored {count} eBay listings, skipped {skipped} likely proxy/custom listings.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
