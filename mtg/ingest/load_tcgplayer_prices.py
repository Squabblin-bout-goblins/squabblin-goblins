"""Fetch TCGPlayer market prices for cards already in Postgres, matched by the
printing-specific tcgplayer_id that Scryfall provides on each card.
"""
import os

import psycopg2
from dotenv import load_dotenv

from tcgplayer_client import fetch_prices_for_ids

load_dotenv()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tcgplayer_prices (
    product_id BIGINT NOT NULL,
    sub_type_name TEXT NOT NULL,
    low_price NUMERIC,
    mid_price NUMERIC,
    high_price NUMERIC,
    market_price NUMERIC,
    direct_low_price NUMERIC,
    fetched_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (product_id, sub_type_name)
);
"""

UPSERT_SQL = """
INSERT INTO tcgplayer_prices (product_id, sub_type_name, low_price, mid_price, high_price, market_price, direct_low_price)
VALUES (%(product_id)s, %(sub_type_name)s, %(low_price)s, %(mid_price)s, %(high_price)s, %(market_price)s, %(direct_low_price)s)
ON CONFLICT (product_id, sub_type_name) DO UPDATE SET
    low_price = EXCLUDED.low_price,
    mid_price = EXCLUDED.mid_price,
    high_price = EXCLUDED.high_price,
    market_price = EXCLUDED.market_price,
    direct_low_price = EXCLUDED.direct_low_price,
    fetched_at = now();
"""


def main():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)

    cur.execute("SELECT DISTINCT tcgplayer_id FROM cards WHERE tcgplayer_id IS NOT NULL;")
    product_ids = [row[0] for row in cur.fetchall()]
    print(f"Fetching TCGPlayer prices for {len(product_ids)} known product IDs...")

    stored = 0
    for price_row in fetch_prices_for_ids(product_ids):
        cur.execute(
            UPSERT_SQL,
            {
                "product_id": price_row.get("productId"),
                "sub_type_name": price_row.get("subTypeName") or "Normal",
                "low_price": price_row.get("lowPrice"),
                "mid_price": price_row.get("midPrice"),
                "high_price": price_row.get("highPrice"),
                "market_price": price_row.get("marketPrice"),
                "direct_low_price": price_row.get("directLowPrice"),
            },
        )
        stored += 1

    print(f"Stored TCGPlayer prices for {stored} products.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
