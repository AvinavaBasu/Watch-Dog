import logging
from datetime import datetime

import requests

from src.checker import ProductStatus

logger = logging.getLogger(__name__)


class DiscordNotifier:

    def __init__(self, webhook_url: str):
        self._webhook_url = webhook_url
        self._session = requests.Session()

    def send_notification(self, product_status: ProductStatus, product_name: str) -> bool:
        embed = self._build_embed(product_status, product_name)
        return self._send_webhook({"embeds": [embed]})

    def send_test_message(self) -> bool:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed = {
            "title": "✅ Watch Dog Test Message",
            "description": "Discord notifications are working correctly!",
            "color": 0x00FF00,
            "footer": {"text": f"Sent at: {now}"},
        }
        return self._send_webhook({"embeds": [embed]})

    def _build_embed(self, product_status: ProductStatus, product_name: str) -> dict:
        price_display = product_status.price if product_status.price else "Price not available"

        try:
            dt = datetime.fromisoformat(product_status.timestamp)
            time_display = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, TypeError):
            time_display = product_status.timestamp

        return {
            "title": "🚨 PRODUCT AVAILABLE! 🚨",
            "description": f"**{product_name}** is now available on Amazon!",
            "color": 0x00FF00,
            "fields": [
                {"name": "📦 Product", "value": product_name, "inline": True},
                {"name": "💰 Price", "value": price_display, "inline": True},
                {"name": "🔗 Link", "value": f"[Buy Now on Amazon]({product_status.url})", "inline": False},
            ],
            "footer": {"text": f"⏰ Detected at: {time_display}"},
            "url": product_status.url,
        }

    def _send_webhook(self, payload: dict) -> bool:
        try:
            response = self._session.post(
                self._webhook_url,
                json=payload,
                timeout=15,
            )

            if response.status_code in (200, 204):
                logger.info("Discord notification sent successfully")
                return True

            if response.status_code == 429:
                retry_after = response.json().get("retry_after", 30)
                logger.warning(
                    "Discord rate limited — retry after %.1f seconds", retry_after,
                )
                return False

            logger.error(
                "Discord webhook error: %d — %s",
                response.status_code, response.text[:200],
            )
            return False

        except requests.exceptions.RequestException as exc:
            logger.error("Failed to send Discord notification: %s", exc)
            return False
