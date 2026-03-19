import re
import logging
from typing import Optional

from bs4 import BeautifulSoup

from src.parsers.base import SiteParser

logger = logging.getLogger(__name__)


class ShopifyParser(SiteParser):
    """Parser for Shopify stores (Delhi Watch Company, etc.)"""

    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        title_tag = soup.find("title")
        if title_tag:
            raw = title_tag.get_text(strip=True)
            for sep in ["–", "|", "-"]:
                if sep in raw:
                    return raw.split(sep)[0].strip()
            return raw
        return None

    def extract_price(self, soup: BeautifulSoup) -> Optional[str]:
        price_el = soup.find(class_="price-item--regular") or soup.find(
            class_="product__price"
        )
        if price_el:
            text = price_el.get_text(strip=True)
            match = re.search(r"(?:Rs\.|₹)\s*[\d,]+(?:\.\d+)?", text)
            if match:
                return match.group(0)

        return self.find_price_in_text(soup.get_text())

    def detect_availability(self, soup: BeautifulSoup, raw_html: str) -> bool:
        buttons = soup.find_all("button")
        for btn in buttons:
            btn_text = btn.get_text(strip=True).lower()
            if "sold out" in btn_text:
                return False
            if "add to cart" in btn_text or "buy now" in btn_text:
                return True

        page_text = soup.get_text()
        if self.text_contains_any(page_text, ["sold out"]):
            return False
        if self.text_contains_any(page_text, ["add to cart", "buy now"]):
            return True

        return False
