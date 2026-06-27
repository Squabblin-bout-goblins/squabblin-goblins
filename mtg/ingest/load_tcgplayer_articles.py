"""Pull recent MTG articles from TCGPlayer's content hub (ChannelFireball's
new home). Pulls whatever's on the initial archive load (~50 articles) --
deeper pagination is behind a "Load More" trigger, and given the 10s
crawl-delay we honor, a full backfill is a deliberate future choice.
"""
import os
from datetime import datetime

import psycopg2
from dotenv import load_dotenv

from tcgplayer_articles_client import TCGPlayerArticlesSession

load_dotenv()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tcgplayer_articles (
    url TEXT PRIMARY KEY,
    title TEXT,
    author TEXT,
    published_at TIMESTAMPTZ,
    body_text TEXT,
    fetched_at TIMESTAMPTZ DEFAULT now()
);
"""

UPSERT_SQL = """
INSERT INTO tcgplayer_articles (url, title, author, published_at, body_text)
VALUES (%(url)s, %(title)s, %(author)s, %(published_at)s, %(body_text)s)
ON CONFLICT (url) DO UPDATE SET
    title = EXCLUDED.title,
    body_text = EXCLUDED.body_text,
    fetched_at = now();
"""


def parse_published_at(raw: str):
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%b %d, %Y")
    except ValueError:
        return None


def main():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)

    count = 0
    with TCGPlayerArticlesSession() as session:
        urls = session.fetch_article_urls()
        print(f"Found {len(urls)} articles on the archive page.")

        for url in urls:
            article = session.fetch_article(url)
            cur.execute(
                UPSERT_SQL,
                {
                    "url": article["url"],
                    "title": article["title"],
                    "author": article["author"],
                    "published_at": parse_published_at(article["published_at_raw"]),
                    "body_text": article["body_text"],
                },
            )
            count += 1
            print(f"  [{count}/{len(urls)}] {article['title']}")

    print(f"Stored {count} articles.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
