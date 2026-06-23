"""Pull recent MTG articles from StarCityGames. Defaults to the most recent
N pages of the MTG-only category archive (each page ~10-12 articles) rather
than the full 2,259-page history -- a full backfill is a deliberate future
choice, not something to do by accident.
"""
import os
import sys

import psycopg2
from dotenv import load_dotenv

from starcitygames_client import StarCityGamesSession

load_dotenv()

DEFAULT_PAGES = 5

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS scg_articles (
    url TEXT PRIMARY KEY,
    title TEXT,
    author TEXT,
    published_at TIMESTAMPTZ,
    body_text TEXT,
    fetched_at TIMESTAMPTZ DEFAULT now()
);
"""

UPSERT_SQL = """
INSERT INTO scg_articles (url, title, author, published_at, body_text)
VALUES (%(url)s, %(title)s, %(author)s, %(published_at)s, %(body_text)s)
ON CONFLICT (url) DO UPDATE SET
    title = EXCLUDED.title,
    body_text = EXCLUDED.body_text,
    fetched_at = now();
"""


def main():
    num_pages = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PAGES

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)

    count = 0
    with StarCityGamesSession() as session:
        article_urls = []
        for page_num in range(1, num_pages + 1):
            urls = session.fetch_article_urls_for_page(page_num)
            print(f"page {page_num}: {len(urls)} articles")
            article_urls.extend(urls)

        for url in dict.fromkeys(article_urls):
            article = session.fetch_article(url)
            cur.execute(UPSERT_SQL, article)
            count += 1

    print(f"Stored {count} articles.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
