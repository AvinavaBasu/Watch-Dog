#!/usr/bin/env python3
import argparse
import logging
import sys

from dotenv import load_dotenv

from src.config import load_config
from src.monitor import WatchDog


def setup_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def cmd_run(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting Watch Dog monitor")

    if not config.products:
        logger.error("No products configured — add products to config.yaml")
        sys.exit(1)

    watchdog = WatchDog(config)
    watchdog.start()


def cmd_check(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Running one-time product check")

    if not config.products:
        logger.error("No products configured — add products to config.yaml")
        sys.exit(1)

    watchdog = WatchDog(config)
    results = watchdog.check_all_products()

    print("\n" + "=" * 60)
    print("  WATCH DOG — Product Availability Report")
    print("=" * 60)

    for status in results:
        indicator = "✅ AVAILABLE" if status.available else "❌ UNAVAILABLE"
        if status.error:
            indicator = f"⚠️  ERROR: {status.error}"

        print(f"\n  {indicator}")
        print(f"  Title: {status.title or 'Unknown'}")
        print(f"  Price: {status.price or 'N/A'}")
        print(f"  URL:   {status.url}")

    print("\n" + "=" * 60)


def cmd_test_notify(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Sending test notifications")

    sent_any = False

    if config.telegram.get("enabled"):
        from src.notifiers.telegram import TelegramNotifier
        notifier = TelegramNotifier(
            bot_token=config.telegram["bot_token"],
            chat_id=config.telegram["chat_id"],
        )
        success = notifier.send_test_message()
        print(f"Telegram: {'✅ Sent' if success else '❌ Failed'}")
        sent_any = True

    if config.discord.get("enabled"):
        from src.notifiers.discord import DiscordNotifier
        notifier = DiscordNotifier(webhook_url=config.discord["webhook_url"])
        success = notifier.send_test_message()
        print(f"Discord:  {'✅ Sent' if success else '❌ Failed'}")
        sent_any = True

    if not sent_any:
        print("No notifiers are enabled. Enable Telegram or Discord in config.yaml or via environment variables.")
        sys.exit(1)


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="watchdog",
        description="Watch Dog — Amazon Product Availability Monitor",
    )
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("run", help="Start the continuous monitor")
    subparsers.add_parser("check", help="One-time check of all products")
    subparsers.add_parser("test-notify", help="Send test notifications to verify setup")

    args = parser.parse_args()

    commands = {
        "run": cmd_run,
        "check": cmd_check,
        "test-notify": cmd_test_notify,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
