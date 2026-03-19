import json
import logging
import random
import signal
import time
from pathlib import Path
from typing import Optional

from src.checker import ProductChecker, ProductStatus
from src.config import Config
from src.notifiers.discord import DiscordNotifier
from src.notifiers.telegram import TelegramNotifier

logger = logging.getLogger(__name__)

STATE_FILE = "state.json"


class WatchDog:

    def __init__(self, config: Config):
        self._config = config
        self._checker = ProductChecker(config)
        self._running = False
        self._previous_statuses: dict[str, ProductStatus] = {}
        self._notifiers: list = []

        if config.telegram.get("enabled"):
            self._notifiers.append(
                TelegramNotifier(
                    bot_token=config.telegram["bot_token"],
                    chat_id=config.telegram["chat_id"],
                )
            )
            logger.info("Telegram notifier enabled")

        if config.discord.get("enabled"):
            self._notifiers.append(
                DiscordNotifier(webhook_url=config.discord["webhook_url"])
            )
            logger.info("Discord notifier enabled")

        if not self._notifiers:
            logger.warning("No notifiers enabled — status changes will only be logged")

        self._load_state()

    def start(self) -> None:
        self._running = True
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        product_count = len(self._config.products)
        logger.info(
            "Watch Dog started — monitoring %d product(s) every %d seconds",
            product_count, self._config.check_interval_seconds,
        )

        while self._running:
            try:
                results = self.check_all_products()
                self._log_summary(results)
                self._save_state()
            except Exception:
                logger.exception("Error during check cycle")

            if not self._running:
                break

            jitter = random.uniform(0, 30)
            sleep_time = self._config.check_interval_seconds + jitter
            logger.info("Next check in %.0f seconds (includes %.0fs jitter)", sleep_time, jitter)

            wake_time = time.monotonic() + sleep_time
            while self._running and time.monotonic() < wake_time:
                time.sleep(min(1.0, wake_time - time.monotonic()))

        logger.info("Watch Dog stopped")

    def check_all_products(self) -> list[ProductStatus]:
        results: list[ProductStatus] = []

        for product in self._config.products:
            name = product.get("name", "Unknown Product")
            url = product.get("url", "")

            if not url:
                logger.warning("Skipping product '%s' — no URL configured", name)
                continue

            status = self._checker.check_product(url)
            results.append(status)

            old_status = self._previous_statuses.get(name)
            self._handle_status_change(name, old_status, status)
            self._previous_statuses[name] = status

        return results

    def _handle_status_change(
        self,
        product_name: str,
        old_status: Optional[ProductStatus],
        new_status: ProductStatus,
    ) -> None:
        if new_status.error:
            logger.warning(
                "Error checking '%s': %s", product_name, new_status.error,
            )
            return

        was_available = old_status.available if old_status else False
        now_available = new_status.available

        if now_available and not was_available:
            logger.info(
                "STATUS CHANGE: '%s' is now AVAILABLE (price: %s)",
                product_name, new_status.price or "N/A",
            )
            self._notify(new_status, product_name)
        elif not now_available and was_available:
            logger.info("STATUS CHANGE: '%s' is now UNAVAILABLE", product_name)
        elif now_available:
            logger.debug("'%s' is still available", product_name)
        else:
            logger.debug("'%s' is still unavailable", product_name)

    def _notify(self, product_status: ProductStatus, product_name: str) -> None:
        for notifier in self._notifiers:
            try:
                notifier.send_notification(product_status, product_name)
            except Exception:
                logger.exception(
                    "Failed to send notification via %s",
                    type(notifier).__name__,
                )

    def stop(self) -> None:
        logger.info("Stopping Watch Dog...")
        self._running = False
        self._save_state()

    def _signal_handler(self, signum: int, _frame) -> None:
        sig_name = signal.Signals(signum).name
        logger.info("Received %s — shutting down gracefully", sig_name)
        self.stop()

    def _log_summary(self, results: list[ProductStatus]) -> None:
        total = len(results)
        available = sum(1 for r in results if r.available)
        errors = sum(1 for r in results if r.error)

        logger.info(
            "Check cycle complete: %d products checked, %d available, %d errors",
            total, available, errors,
        )

    def _save_state(self) -> None:
        state = {}
        for name, status in self._previous_statuses.items():
            state[name] = {
                "url": status.url,
                "available": status.available,
                "price": status.price,
                "title": status.title,
                "timestamp": status.timestamp,
                "error": status.error,
            }

        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            logger.debug("State saved to %s", STATE_FILE)
        except OSError:
            logger.exception("Failed to save state file")

    def _load_state(self) -> None:
        path = Path(STATE_FILE)
        if not path.exists():
            logger.debug("No previous state file found")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)

            for name, data in state.items():
                self._previous_statuses[name] = ProductStatus(
                    url=data.get("url", ""),
                    available=data.get("available", False),
                    price=data.get("price"),
                    title=data.get("title"),
                    timestamp=data.get("timestamp", ""),
                    error=data.get("error"),
                )

            logger.info(
                "Restored state for %d product(s) from %s",
                len(self._previous_statuses), STATE_FILE,
            )
        except (json.JSONDecodeError, OSError):
            logger.exception("Failed to load state file — starting fresh")
