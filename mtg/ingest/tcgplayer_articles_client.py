"""Playwright client for TCGPlayer's content hub (ChannelFireball articles
now live here: tcgplayer.com/content/magic-the-gathering).

robots.txt allows /content/ article paths (only deck/player views are
disallowed) but sets Crawl-Delay: 10 -- we honor that strictly between every
request, including between the archive page and each article, since we
already have a real API relationship with TCGPlayer and don't want to be a
bad citizen on the website side.
"""
import re

from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
ARCHIVE_URL = "https://www.tcgplayer.com/content/magic-the-gathering/articles"
CRAWL_DELAY_MS = 10_000

AUTHOR_RE = re.compile(r"^By (.+)$", re.MULTILINE)
PUBLISHED_RE = re.compile(r"^Published (.+)$", re.MULTILINE)


class TCGPlayerArticlesSession:
    def __enter__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self.page = self._browser.new_page(user_agent=USER_AGENT)
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._playwright.stop()

    def fetch_article_urls(self) -> list[str]:
        self.page.goto(ARCHIVE_URL, timeout=20000, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2500)
        hrefs = self.page.eval_on_selector_all(
            "a", "els => els.map(e => e.getAttribute('href')).filter(Boolean)"
        )
        urls = sorted({h for h in hrefs if "/content/article/" in h})
        self.page.wait_for_timeout(CRAWL_DELAY_MS)
        return [f"https://www.tcgplayer.com{u}" if u.startswith("/") else u for u in urls]

    def fetch_article(self, url: str) -> dict:
        self.page.goto(url, timeout=20000, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1500)
        title = self.page.eval_on_selector("h1", "el => el ? el.innerText : null")
        main_text = self.page.eval_on_selector("main", "el => el ? el.innerText : null") or ""

        author_match = AUTHOR_RE.search(main_text)
        published_match = PUBLISHED_RE.search(main_text)

        self.page.wait_for_timeout(CRAWL_DELAY_MS)
        return {
            "url": url,
            "title": title,
            "author": author_match.group(1).strip() if author_match else None,
            "published_at_raw": published_match.group(1).strip() if published_match else None,
            "body_text": main_text,
        }
