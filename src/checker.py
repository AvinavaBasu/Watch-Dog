import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

from src.config import Config

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

UNAVAILABLE_SIGNALS = [
    "currently unavailable",
    "currently out of stock",
    "we don't know when or if this item will be back in stock",
]

AVAILABLE_SIGNALS = [
    "add to cart",
    "buy now",
]


@dataclass
class ProductStatus:
    url: str
    available: bool
    price: Optional[str]
    title: Optional[str]
    timestamp: str
    error: Optional[str]


class AmazonChecker:

    def __init__(self, config: Config):
        self._config = config
        self._session = requests.Session()
        self._ua_index = 0

    def check_product(self, url: str) -> ProductStatus:
        timestamp = datetime.now(timezone.utc).isoformat()

        for attempt in range(1, self._config.max_retries + 1):
            try:
                logger.info(
                    "Checking product (attempt %d/%d): %s",
                    attempt, self._config.max_retries, url,
                )

                delay = random.uniform(2.0, 5.0)
                time.sleep(delay)

                headers = self._get_headers()
                response = self._session.get(
                    url,
                    headers=headers,
                    timeout=self._config.request_timeout,
                )
                response.raise_for_status()

                return self._parse_response(response.text, url, timestamp)

            except requests.exceptions.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else 0
                logger.warning(
                    "HTTP %d for %s (attempt %d/%d)",
                    status_code, url, attempt, self._config.max_retries,
                )
                if attempt == self._config.max_retries:
                    return ProductStatus(
                        url=url, available=False, price=None, title=None,
                        timestamp=timestamp, error=f"HTTP {status_code}",
                    )

            except requests.exceptions.ConnectionError:
                logger.warning(
                    "Connection error for %s (attempt %d/%d)",
                    url, attempt, self._config.max_retries,
                )
                if attempt == self._config.max_retries:
                    return ProductStatus(
                        url=url, available=False, price=None, title=None,
                        timestamp=timestamp, error="Connection error",
                    )

            except requests.exceptions.Timeout:
                logger.warning(
                    "Timeout for %s (attempt %d/%d)",
                    url, attempt, self._config.max_retries,
                )
                if attempt == self._config.max_retries:
                    return ProductStatus(
                        url=url, available=False, price=None, title=None,
                        timestamp=timestamp, error="Request timed out",
                    )

            except Exception as exc:
                logger.exception(
                    "Unexpected error checking %s (attempt %d/%d): %s",
                    url, attempt, self._config.max_retries, exc,
                )
                if attempt == self._config.max_retries:
                    return ProductStatus(
                        url=url, available=False, price=None, title=None,
                        timestamp=timestamp, error=str(exc),
                    )

            backoff = min(2 ** attempt + random.uniform(0, 1), 60)
            logger.debug("Backing off %.1f seconds before retry", backoff)
            time.sleep(backoff)

        return ProductStatus(
            url=url, available=False, price=None, title=None,
            timestamp=timestamp, error="Max retries exhausted",
        )

    def _get_headers(self) -> dict[str, str]:
        if self._config.user_agent_rotation:
            ua = random.choice(USER_AGENTS)
        else:
            ua = USER_AGENTS[0]

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

    def _parse_response(self, html: str, url: str, timestamp: str) -> ProductStatus:
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as exc:
            logger.error("Failed to parse HTML for %s: %s", url, exc)
            return ProductStatus(
                url=url, available=False, price=None, title=None,
                timestamp=timestamp, error=f"Parse error: {exc}",
            )

        title = self._extract_title(soup)
        available = self._detect_availability(soup, html)
        price = self._extract_price(soup) if available else None

        logger.info(
            "Product: %s | Available: %s | Price: %s | URL: %s",
            title or "Unknown", available, price or "N/A", url,
        )

        return ProductStatus(
            url=url, available=available, price=price, title=title,
            timestamp=timestamp, error=None,
        )

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        title_el = soup.find(id="productTitle")
        if title_el:
            return title_el.get_text(strip=True)

        title_el = soup.find("span", {"id": "productTitle"})
        if title_el:
            return title_el.get_text(strip=True)

        return None

    def _extract_price(self, soup: BeautifulSoup) -> Optional[str]:
        buybox = (
            soup.find(id="buyBoxAccordion")
            or soup.find(id="desktop_buybox")
            or soup.find(id="ppd")
            or soup
        )

        id_selectors = [
            "priceblock_ourprice",
            "priceblock_dealprice",
            "price_inside_buybox",
            "newBuyBoxPrice",
            "corePrice_feature_div",
        ]
        for sel_id in id_selectors:
            container = buybox.find(id=sel_id)
            if container:
                price_whole = container.find("span", class_="a-price-whole")
                if price_whole:
                    return "₹" + price_whole.get_text(strip=True).rstrip(".")
                text = container.get_text(strip=True)
                if "₹" in text:
                    import re
                    match = re.search(r"₹[\d,]+(?:\.\d+)?", text)
                    if match:
                        return match.group(0)

        price_whole = buybox.find("span", class_="a-price-whole")
        if price_whole:
            parent = price_whole.find_parent(class_="a-price")
            if parent and not parent.find_parent(class_="a-section a-spacing-small"):
                return "₹" + price_whole.get_text(strip=True).rstrip(".")

        return None

    def _detect_availability(self, soup: BeautifulSoup, raw_html: str) -> bool:
        add_to_cart = soup.find(id="add-to-cart-button")
        buy_now = soup.find(id="buy-now-button")

        if add_to_cart or buy_now:
            logger.debug("Found purchase button(s) — product is available")
            return True

        availability_div = soup.find(id="availability")
        if availability_div:
            text = availability_div.get_text(strip=True).lower()
            if "unavailable" in text or "out of stock" in text:
                logger.debug("Availability div says unavailable: '%s'", text[:80])
                return False
            if "in stock" in text:
                return True

        buybox = soup.find(id="buyBoxAccordion") or soup.find(id="desktop_buybox")
        if buybox:
            buybox_text = buybox.get_text(strip=True).lower()
            if "add to cart" in buybox_text or "buy now" in buybox_text:
                logger.debug("Found purchase text in buy box")
                return True

        center_col = soup.find(id="centerCol") or soup.find(id="ppd")
        if center_col:
            center_text = center_col.get_text(strip=True).lower()
            for signal in UNAVAILABLE_SIGNALS:
                if signal in center_text:
                    logger.debug("Unavailability signal in product area: '%s'", signal)
                    return False

        logger.debug("Could not determine availability, defaulting to unavailable")
        return False
