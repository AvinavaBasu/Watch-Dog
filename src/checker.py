import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

from src.config import Config
from src.parsers import get_parser

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
]


@dataclass
class ProductStatus:
    url: str
    available: bool
    price: Optional[str]
    title: Optional[str]
    timestamp: str
    error: Optional[str]


class ProductChecker:
    """HTTP layer with retry logic. Delegates HTML parsing to site-specific parsers."""

    def __init__(self, config: Config):
        self._config = config
        self._session = requests.Session()

    def check_product(self, url: str) -> ProductStatus:
        parser = get_parser(url)
        timestamp = datetime.now(timezone.utc).isoformat()

        for attempt in range(1, self._config.max_retries + 1):
            try:
                logger.info("Checking product (attempt %d/%d): %s", attempt, self._config.max_retries, url)

                time.sleep(random.uniform(2.0, 5.0))

                response = self._session.get(url, headers=self._get_headers(), timeout=self._config.request_timeout)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                title = parser.extract_title(soup)
                available = parser.detect_availability(soup, response.text)
                price = parser.extract_price(soup) if available else None

                logger.info("Product: %s | Available: %s | Price: %s | URL: %s", title or "Unknown", available, price or "N/A", url)

                return ProductStatus(url=url, available=available, price=price, title=title, timestamp=timestamp, error=None)

            except requests.exceptions.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else 0
                logger.warning("HTTP %d for %s (attempt %d/%d)", status_code, url, attempt, self._config.max_retries)
                if attempt == self._config.max_retries:
                    return ProductStatus(url=url, available=False, price=None, title=None, timestamp=timestamp, error=f"HTTP {status_code}")
            except requests.exceptions.ConnectionError:
                logger.warning("Connection error for %s (attempt %d/%d)", url, attempt, self._config.max_retries)
                if attempt == self._config.max_retries:
                    return ProductStatus(url=url, available=False, price=None, title=None, timestamp=timestamp, error="Connection error")
            except requests.exceptions.Timeout:
                logger.warning("Timeout for %s (attempt %d/%d)", url, attempt, self._config.max_retries)
                if attempt == self._config.max_retries:
                    return ProductStatus(url=url, available=False, price=None, title=None, timestamp=timestamp, error="Request timed out")
            except Exception as exc:
                logger.exception("Unexpected error checking %s (attempt %d/%d): %s", url, attempt, self._config.max_retries, exc)
                if attempt == self._config.max_retries:
                    return ProductStatus(url=url, available=False, price=None, title=None, timestamp=timestamp, error=str(exc))

            backoff = min(2 ** attempt + random.uniform(0, 1), 60)
            time.sleep(backoff)

        return ProductStatus(url=url, available=False, price=None, title=None, timestamp=timestamp, error="Max retries exhausted")

    def _get_headers(self) -> dict[str, str]:
        ua = random.choice(USER_AGENTS) if self._config.user_agent_rotation else USER_AGENTS[0]
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }


AmazonChecker = ProductChecker
