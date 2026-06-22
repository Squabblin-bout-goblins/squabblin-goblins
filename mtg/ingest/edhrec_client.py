"""Playwright-based client for EDHREC tag/tribal pages.

EDHREC is a Next.js app -- rather than scraping rendered DOM text, we pull
the embedded __NEXT_DATA__ JSON blob, which is the same structured data the
page itself renders from. Far more reliable than text scraping.
"""
import json

from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_tag_cardlists(tag_slug: str) -> list[dict]:
    """Return the raw cardlists array for an EDHREC tag page
    (e.g. 'goblins' -> https://edhrec.com/tags/goblins).

    Each entry looks like:
      {"header": "High Synergy Cards", "tag": "highsynergycards",
       "cardviews": [{"name", "sanitized", "url", "inclusion", "num_decks", "potential_decks"}, ...]}
    """
    url = f"https://edhrec.com/tags/{tag_slug}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT)
        page.goto(url, timeout=20000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        raw = page.eval_on_selector("script#__NEXT_DATA__", "el => el.textContent")
        browser.close()

    data = json.loads(raw)
    return data["props"]["pageProps"]["data"]["container"]["json_dict"]["cardlists"]
