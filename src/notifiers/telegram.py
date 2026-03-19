import logging
from datetime import datetime

import requests

from src.checker import ProductStatus

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramNotifier:

    def __init__(self, bot_token: str, chat_id: str):
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._api_url = f"{TELEGRAM_API_BASE}/bot{bot_token}"
        self._session = requests.Session()

    def send_notification(self, product_status: ProductStatus, product_name: str) -> bool:
        message = self._format_message(product_status, product_name)
        return self._send_message(message)

    def send_test_message(self) -> bool:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            "✅ <b>Watch Dog Test Message</b>\n\n"
            "Telegram notifications are working correctly!\n"
            f"⏰ Sent at: {now}"
        )
        return self._send_message(message)

    def _format_message(self, product_status: ProductStatus, product_name: str) -> str:
        price_display = product_status.price if product_status.price else "Price not available"

        try:
            dt = datetime.fromisoformat(product_status.timestamp)
            time_display = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, TypeError):
            time_display = product_status.timestamp

        return (
            '🚨 <b>PRODUCT AVAILABLE!</b> 🚨\n'
            '\n'
            f'📦 Product: {product_name}\n'
            f'💰 Price: {price_display}\n'
            f'🔗 <a href="{product_status.url}">Buy Now on Amazon</a>\n'
            f'⏰ Detected at: {time_display}\n'
            '\n'
            '⚡ Hurry! This product sells out fast!'
        )

    def _send_message(self, text: str) -> bool:
        url = f"{self._api_url}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }

        try:
            response = self._session.post(url, json=payload, timeout=15)
            data = response.json()

            if response.status_code == 200 and data.get("ok"):
                logger.info("Telegram notification sent successfully")
                return True

            if response.status_code == 429:
                retry_after = data.get("parameters", {}).get("retry_after", 30)
                logger.warning(
                    "Telegram rate limited — retry after %d seconds", retry_after,
                )
                return False

            logger.error(
                "Telegram API error: %d — %s",
                response.status_code, data.get("description", "Unknown error"),
            )
            return False

        except requests.exceptions.RequestException as exc:
            logger.error("Failed to send Telegram notification: %s", exc)
            return False
