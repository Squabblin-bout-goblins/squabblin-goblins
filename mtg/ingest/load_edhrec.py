"""Pull EDHREC synergy/inclusion data for a tribal/theme tag (default:
goblins, our anchor example for the SYNERGIZES_WITH graph).
"""
import os
import sys

import psycopg2
from dotenv import load_dotenv

from edhrec_client import fetch_tag_cardlists

load_dotenv()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS edhrec_synergy (
    tag TEXT NOT NULL,
    category TEXT NOT NULL,
    card_name TEXT NOT NULL,
    card_slug TEXT,
    num_decks INTEGER,
    potential_decks INTEGER,
    synergy_pct NUMERIC,
    fetched_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (tag, category, card_name)
);
"""

UPSERT_SQL = """
INSERT INTO edhrec_synergy (tag, category, card_name, card_slug, num_decks, potential_decks, synergy_pct)
VALUES (%(tag)s, %(category)s, %(card_name)s, %(card_slug)s, %(num_decks)s, %(potential_decks)s, %(synergy_pct)s)
ON CONFLICT (tag, category, card_name) DO UPDATE SET
    num_decks = EXCLUDED.num_decks,
    potential_decks = EXCLUDED.potential_decks,
    synergy_pct = EXCLUDED.synergy_pct,
    fetched_at = now();
"""


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "goblins"

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)

    cardlists = fetch_tag_cardlists(tag)

    count = 0
    for cardlist in cardlists:
        category = cardlist.get("header")
        for card in cardlist.get("cardviews", []):
            num_decks = card.get("num_decks")
            potential_decks = card.get("potential_decks")
            synergy_pct = (
                round(100 * num_decks / potential_decks, 2)
                if num_decks and potential_decks
                else None
            )
            cur.execute(
                UPSERT_SQL,
                {
                    "tag": tag,
                    "category": category,
                    "card_name": card.get("name"),
                    "card_slug": card.get("sanitized"),
                    "num_decks": num_decks,
                    "potential_decks": potential_decks,
                    "synergy_pct": synergy_pct,
                },
            )
            count += 1

    print(f"Stored {count} EDHREC synergy rows for tag {tag!r} across {len(cardlists)} categories.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
