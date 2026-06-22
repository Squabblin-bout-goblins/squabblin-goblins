"""Pull cards from Scryfall by query and load them into Postgres, raw."""
import json
import os
import sys

import psycopg2
from dotenv import load_dotenv

from scryfall_client import fetch_cards

load_dotenv()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cards (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    mana_cost TEXT,
    type_line TEXT,
    oracle_text TEXT,
    set_code TEXT,
    set_name TEXT,
    rarity TEXT,
    price_usd NUMERIC,
    tcgplayer_id BIGINT,
    image_url TEXT,
    raw JSONB NOT NULL,
    ingested_at TIMESTAMPTZ DEFAULT now()
);
"""

UPSERT_SQL = """
INSERT INTO cards (id, name, mana_cost, type_line, oracle_text, set_code, set_name, rarity, price_usd, tcgplayer_id, image_url, raw)
VALUES (%(id)s, %(name)s, %(mana_cost)s, %(type_line)s, %(oracle_text)s, %(set_code)s, %(set_name)s, %(rarity)s, %(price_usd)s, %(tcgplayer_id)s, %(image_url)s, %(raw)s)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    price_usd = EXCLUDED.price_usd,
    tcgplayer_id = EXCLUDED.tcgplayer_id,
    raw = EXCLUDED.raw,
    ingested_at = now();
"""


def to_row(card: dict) -> dict:
    image_url = (card.get("image_uris") or {}).get("normal")
    prices = card.get("prices") or {}
    usd = prices.get("usd")
    return {
        "id": card["id"],
        "name": card.get("name"),
        "mana_cost": card.get("mana_cost"),
        "type_line": card.get("type_line"),
        "oracle_text": card.get("oracle_text"),
        "set_code": card.get("set"),
        "set_name": card.get("set_name"),
        "rarity": card.get("rarity"),
        "price_usd": float(usd) if usd else None,
        "tcgplayer_id": card.get("tcgplayer_id"),
        "image_url": image_url,
        "raw": json.dumps(card),
    }


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "type:goblin"

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)

    count = 0
    for card in fetch_cards(query):
        cur.execute(UPSERT_SQL, to_row(card))
        count += 1

    print(f"Ingested {count} cards for query: {query!r}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
