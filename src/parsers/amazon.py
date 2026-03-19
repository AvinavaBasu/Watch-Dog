import re
import logging
from typing import Optional

from bs4 import BeautifulSoup

from src.parsers.base import SiteParser

logger = logging.getLogger(__name__)


class AmazonParser(SiteParser):

    UNAVAILABLE_SIGNALS = [
        "currently unavailable",
        "currently out of stock",
        "we don't know when or if this item will be back in stock",
    ]

    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        el = soup.find(id="productTitle")
        if el:
            return el.get_text(strip=True)
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True).split("|")[0].strip()
        return None

    def extract_price(self, soup: BeautifulSoup) -> Optional[str]:
        buybox = (
            soup.find(id="buyBoxAccordion")
            or soup.find(id="desktop_buybox")
            or soup.find(id="ppd")
            or soup
        )

        for sel_id in [
            "priceblock_ourprice",
            "priceblock_dealprice",
            "price_inside_buybox",
            "newBuyBoxPrice",
            "corePrice_feature_div",
        ]:
            container = buybox.find(id=sel_id)
            if container:
                price_whole = container.find("span", class_="a-price-whole")
                if price_whole:
                    return "₹" + price_whole.get_text(strip=True).rstrip(".")
                text = container.get_text(strip=True)
                match = re.search(r"₹[\d,]+(?:\.\d+)?", text)
                if match:
                    return match.group(0)

        price_whole = buybox.find("span", class_="a-price-whole")
        if price_whole:
            parent = price_whole.find_parent(class_="a-price")
            if parent and not parent.find_parent(class_="a-section a-spacing-small"):
                return "₹" + price_whole.get_text(strip=True).rstrip(".")

        return None

    def detect_availability(self, soup: BeautifulSoup, raw_html: str) -> bool:
        if soup.find(id="add-to-cart-button") or soup.find(id="buy-now-button"):
            return True

        availability_div = soup.find(id="availability")
        if availability_div:
            text = availability_div.get_text(strip=True).lower()
            if "unavailable" in text or "out of stock" in text:
                return False
            if "in stock" in text:
                return True

        buybox = soup.find(id="buyBoxAccordion") or soup.find(id="desktop_buybox")
        if buybox:
            buybox_text = buybox.get_text(strip=True).lower()
            if "add to cart" in buybox_text or "buy now" in buybox_text:
                return True

        center_col = soup.find(id="centerCol") or soup.find(id="ppd")
        if center_col:
            center_text = center_col.get_text(strip=True).lower()
            if self.text_contains_any(center_text, self.UNAVAILABLE_SIGNALS):
                return False

        return False
