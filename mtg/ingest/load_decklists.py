"""Pull representative paper decklists from MTGGoldfish for each archetype
across the paper-relevant constructed formats. Commander isn't tracked the
same way here -- EDHREC owns that data separately. Alchemy is excluded by
construction (MTGGoldfish doesn't track it as a metagame format).
"""
import os
import sys

import psycopg2
from dotenv import load_dotenv

from mtggoldfish_client import GoldfishSession

load_dotenv()

PAPER_FORMATS = ["standard", "pioneer", "modern", "legacy", "vintage", "pauper"]

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS decks (
    id SERIAL PRIMARY KEY,
    format TEXT NOT NULL,
    archetype_slug TEXT NOT NULL,
    name TEXT,
    fetched_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (format, archetype_slug)
);

CREATE TABLE IF NOT EXISTS deck_cards (
    deck_id INTEGER REFERENCES decks(id) ON DELETE CASCADE,
    section TEXT NOT NULL,
    card_name TEXT NOT NULL,
    quantity INTEGER NOT NULL
);
"""

UPSERT_DECK_SQL = """
INSERT INTO decks (format, archetype_slug, name)
VALUES (%(format)s, %(archetype_slug)s, %(name)s)
ON CONFLICT (format, archetype_slug) DO UPDATE SET
    name = EXCLUDED.name,
    fetched_at = now()
RETURNING id;
"""


def main():
    formats = [sys.argv[1]] if len(sys.argv) > 1 else PAPER_FORMATS

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(CREATE_TABLES_SQL)

    deck_count = 0
    card_row_count = 0

    with GoldfishSession() as session:
        for fmt in formats:
            slugs = session.fetch_archetype_slugs(fmt)
            print(f"{fmt}: {len(slugs)} archetypes")

            for slug in slugs:
                try:
                    deck = session.fetch_decklist(slug)
                except Exception as exc:
                    print(f"  skip {slug}: {exc}")
                    continue

                cur.execute(
                    UPSERT_DECK_SQL,
                    {"format": fmt, "archetype_slug": slug, "name": deck["name"]},
                )
                deck_id = cur.fetchone()[0]
                cur.execute("DELETE FROM deck_cards WHERE deck_id = %s;", (deck_id,))

                for section, cards in deck["sections"].items():
                    for qty, card_name in cards:
                        cur.execute(
                            "INSERT INTO deck_cards (deck_id, section, card_name, quantity) VALUES (%s, %s, %s, %s);",
                            (deck_id, section, card_name, qty),
                        )
                        card_row_count += 1
                deck_count += 1

    print(f"Stored {deck_count} decks, {card_row_count} deck_cards rows.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
