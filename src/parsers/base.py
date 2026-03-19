import re
import logging
from abc import ABC, abstractmethod
from typing import Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SiteParser(ABC):
    """Base class for site-specific HTML parsers.

    To add support for a new site:
    1. Create a new file in src/parsers/
    2. Subclass SiteParser
    3. Implement extract_title, extract_price, detect_availability
    4. Register domains in src/parsers/registry.py
    """

    @abstractmethod
    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        ...

    @abstractmethod
    def extract_price(self, soup: BeautifulSoup) -> Optional[str]:
        ...

    @abstractmethod
    def detect_availability(self, soup: BeautifulSoup, raw_html: str) -> bool:
        ...

    @staticmethod
    def find_price_in_text(text: str) -> Optional[str]:
        """Extract first price pattern (₹X,XXX or Rs. X,XXX) from text."""
        match = re.search(r"₹\s*[\d,]+(?:\.\d+)?", text)
        if match:
            return match.group(0).replace(" ", "")
        match = re.search(r"Rs\.?\s*[\d,]+(?:\.\d+)?", text)
        if match:
            return match.group(0)
        return None

    @staticmethod
    def text_contains_any(text: str, signals: list[str]) -> bool:
        """Check if text contains any of the given signals (case-insensitive)."""
        text_lower = text.lower()
        return any(s in text_lower for s in signals)
