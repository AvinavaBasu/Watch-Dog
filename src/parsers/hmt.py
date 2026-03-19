import logging
from typing import Optional

from bs4 import BeautifulSoup

from src.parsers.base import SiteParser

logger = logging.getLogger(__name__)


class HMTParser(SiteParser):
    """Parser for hmtwatches.store"""

    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return None

    def extract_price(self, soup: BeautifulSoup) -> Optional[str]:
        return self.find_price_in_text(soup.get_text())

    def detect_availability(self, soup: BeautifulSoup, raw_html: str) -> bool:
        page_text = soup.get_text()

        if self.text_contains_any(page_text, ["out of stock"]):
            return False

        if self.text_contains_any(page_text, ["add to cart", "buy now", "add to bag"]):
            return True

        return False
