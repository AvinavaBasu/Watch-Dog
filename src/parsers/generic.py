import logging
from typing import Optional

from bs4 import BeautifulSoup

from src.parsers.base import SiteParser

logger = logging.getLogger(__name__)

UNAVAILABLE_SIGNALS = [
    "out of stock",
    "sold out",
    "currently unavailable",
    "coming soon",
    "notify me",
]

AVAILABLE_SIGNALS = [
    "add to cart",
    "buy now",
    "add to bag",
    "buy it now",
]


class GenericParser(SiteParser):
    """Fallback parser for unknown sites."""

    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        title_tag = soup.find("title")
        if title_tag:
            raw = title_tag.get_text(strip=True)
            for sep in ["|", " - ", " – ", " — "]:
                if sep in raw:
                    return raw.split(sep)[0].strip()
            return raw
        return None

    def extract_price(self, soup: BeautifulSoup) -> Optional[str]:
        return self.find_price_in_text(soup.get_text())

    def detect_availability(self, soup: BeautifulSoup, raw_html: str) -> bool:
        page_text = soup.get_text()

        if self.text_contains_any(page_text, UNAVAILABLE_SIGNALS):
            return False

        if self.text_contains_any(page_text, AVAILABLE_SIGNALS):
            return True

        return False
