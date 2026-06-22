"""Playwright-based client for MTGGoldfish metagame and decklist pages.

MTGGoldfish isn't actually behind a hard bot-block -- plain Playwright with a
normal desktop user-agent gets through fine. The earlier 30s timeout was the
page's ad/tracking scripts delaying the "load" event, not Cloudflare; using
wait_until="domcontentloaded" instead fixes it.
"""
import re

from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

CARD_ROW_RE = re.compile(r"^(\d+)\t(.+?)\t+\$")
SECTION_HEADER_RE = re.compile(r"^([A-Za-z][A-Za-z /]*) \(\d+\)$")


class GoldfishSession:
    """Keeps one browser/page alive across many page fetches instead of
    paying browser launch cost per request.
    """

    def __enter__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self.page = self._browser.new_page(user_agent=USER_AGENT)
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._playwright.stop()

    def fetch_archetype_slugs(self, format_slug: str) -> list[str]:
        """Return unique archetype slugs (e.g. 'modern-affinity') for a
        format's metagame page, in descending order of meta share.
        """
        url = f"https://www.mtggoldfish.com/metagame/{format_slug}/full"
        self.page.goto(url, timeout=20000, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2000)
        hrefs = self.page.eval_on_selector_all(
            "a[href*='/archetype/']", "els => els.map(e => e.getAttribute('href'))"
        )

        slugs = []
        seen = set()
        for href in hrefs:
            slug = href.split("/archetype/")[-1].split("#")[0]
            if slug and slug not in seen:
                seen.add(slug)
                slugs.append(slug)
        return slugs

    def fetch_decklist(self, archetype_slug: str) -> dict:
        """Return {"name": str, "sections": {section: [(qty, card_name), ...]}}
        for the representative paper decklist of an archetype.
        """
        url = f"https://www.mtggoldfish.com/archetype/{archetype_slug}#paper"
        self.page.goto(url, timeout=20000, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2000)
        title = self.page.title()
        rows = self.page.eval_on_selector_all(
            ".deck-view-deck-table tr", "els => els.map(e => e.innerText)"
        )

        return _parse_decklist_rows(title, rows)


def _parse_decklist_rows(title: str, rows: list[str]) -> dict:
    sections: dict[str, list[tuple[int, str]]] = {}
    current_section = "Unknown"
    for row in rows:
        section_match = SECTION_HEADER_RE.match(row)
        if section_match:
            current_section = section_match.group(1).strip()
            continue
        card_match = CARD_ROW_RE.match(row)
        if card_match:
            qty = int(card_match.group(1))
            name = card_match.group(2).strip()
            sections.setdefault(current_section, []).append((qty, name))

    return {"name": title, "sections": sections}
