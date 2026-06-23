"""Playwright-based client for StarCityGames' MTG article archive.

robots.txt is wide open (no disallows) and the site is server-side
rendered, so this could run on plain requests -- Playwright is used anyway
for consistency with the other MTG scrapers and because some interactive
elements (share widgets, embedded decklists) render more reliably with a
real browser.
"""
import re

from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
CATEGORY_URL = "https://articles.starcitygames.com/magic-the-gathering"


def fetch_article_urls_for_page(page, page_num: int) -> list[str]:
    url = CATEGORY_URL if page_num == 1 else f"{CATEGORY_URL}/page/{page_num}/"
    page.goto(url, timeout=20000, wait_until="domcontentloaded")
    page.wait_for_timeout(1500)
    hrefs = page.eval_on_selector_all(
        "a", "els => els.map(e => e.getAttribute('href')).filter(Boolean)"
    )
    pattern = re.compile(r"^https://articles\.starcitygames\.com/magic-the-gathering/[^/]+/$")
    return sorted({h for h in hrefs if pattern.match(h)})


def fetch_article(page, url: str) -> dict:
    page.goto(url, timeout=20000, wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    title = page.eval_on_selector("h1", "el => el ? el.innerText : null")
    published_at = page.eval_on_selector("time", "el => el ? el.getAttribute('datetime') : null")
    author = page.eval_on_selector(
        "[class*='author']", "el => el ? el.innerText.replace(/^By\\s*/i, '').trim() : null"
    )
    body_text = page.eval_on_selector("article", "el => el ? el.innerText : null")
    return {
        "url": url,
        "title": title,
        "author": author,
        "published_at": published_at,
        "body_text": body_text,
    }


class StarCityGamesSession:
    def __enter__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self.page = self._browser.new_page(user_agent=USER_AGENT)
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._playwright.stop()

    def fetch_article_urls_for_page(self, page_num: int) -> list[str]:
        return fetch_article_urls_for_page(self.page, page_num)

    def fetch_article(self, url: str) -> dict:
        return fetch_article(self.page, url)
