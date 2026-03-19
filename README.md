# Watch Dog 🐕

**Never miss a restock. Monitor product availability across e-commerce sites and get instant notifications.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/AvinavaBasu/Watch-Dog/actions/workflows/test.yml/badge.svg)](https://github.com/AvinavaBasu/Watch-Dog/actions)

---

## Features

- **Multi-site monitoring** — Amazon, HMT Watches, Shopify stores (DWC), and any e-commerce site via generic fallback
- **Auto-detection** — Just add a URL. The parser is selected automatically from the domain
- **Telegram and Discord notifications** — Instant alerts when products come back in stock
- **Pluggable architecture** — Add a new site with one file and one line of config
- **State persistence** — Only notifies on state changes (unavailable → available); survives restarts
- **Rotating user agents** — Reduces detection risk with randomized browser fingerprints
- **Docker and GitHub Actions** — Deploy however you want

### Supported Sites

| Site | Domain | Parser |
|------|--------|--------|
| Amazon | `amazon.in`, `amazon.com`, `amazon.co.uk`, `amazon.de` | `AmazonParser` |
| HMT Watches | `hmtwatches.store` | `HMTParser` |
| Shopify stores | `delhiwatchcompany.com` + any Shopify site | `ShopifyParser` |
| Everything else | Any URL | `GenericParser` (fallback) |

---

## Quick Start

```bash
git clone https://github.com/AvinavaBasu/Watch-Dog.git
cd Watch-Dog
pip install -r requirements.txt

cp config.yaml.example config.yaml
cp .env.example .env
# Edit config.yaml with your products
# Edit .env with your Telegram bot token and chat ID

python run.py run
```

---

## Configuration

### `config.yaml`

Just add a name and URL — the site parser is auto-detected:

```yaml
products:
  - name: "Casio Youth AE-1200WHL-5AVDF"
    url: "https://www.amazon.in/dp/B0DRQSHJSC/"

  - name: "HMT NASS 12"
    url: "https://www.hmtwatches.store/product/44f66e4a-d6b0-4f96-a3c6-a82f1906d8bd"

  - name: "DWC Terra"
    url: "https://delhiwatchcompany.com/products/dwc-terra"

  - name: "Any Product on Any Site"
    url: "https://www.some-shop.com/product/123"

check_interval_seconds: 300
request_timeout: 30
max_retries: 3
user_agent_rotation: true
log_level: "INFO"
```

| Key | Description | Default |
|-----|-------------|---------|
| `products` | List of products (name + URL) | `[]` |
| `check_interval_seconds` | Seconds between checks | `300` |
| `request_timeout` | HTTP timeout (seconds) | `30` |
| `max_retries` | Retries per failed request | `3` |
| `user_agent_rotation` | Rotate user agents | `true` |
| `log_level` | Logging level | `INFO` |

### Environment Variables (`.env`)

| Variable | Description |
|---------|-------------|
| `WATCHDOG_TELEGRAM_ENABLED` | `true` or `false` |
| `WATCHDOG_TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `WATCHDOG_TELEGRAM_CHAT_ID` | Telegram chat ID |
| `WATCHDOG_DISCORD_ENABLED` | `true` or `false` |
| `WATCHDOG_DISCORD_WEBHOOK_URL` | Discord webhook URL |
| `WATCHDOG_CHECK_INTERVAL` | Overrides `check_interval_seconds` |
| `WATCHDOG_LOG_LEVEL` | Overrides `log_level` |

---

## Telegram Setup

1. Message [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`, follow the prompts
2. Copy the bot token
3. Message [@userinfobot](https://t.me/userinfobot) to get your chat ID
4. Add both to `.env`
5. Send your bot a message (required one-time step)
6. Test: `python run.py test-notify`

## Discord Setup

1. Server Settings → Integrations → Webhooks → New Webhook
2. Copy the webhook URL
3. Add to `.env`

---

## Usage

```bash
# Start continuous monitoring (checks every 5 min)
python run.py run

# One-time check of all products
python run.py check

# Test notifications
python run.py test-notify
```

---

## Deployment

### Local / VPS (recommended)

```bash
screen -S watchdog
python run.py run
# Ctrl+A, D to detach
```

### Docker

```bash
docker-compose up -d
docker-compose logs -f watchdog
```

### GitHub Actions

> Note: GitHub throttles scheduled workflows on free repos to ~30-60 min intervals.

1. Fork this repo
2. Add secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
3. Enable Actions — runs on schedule automatically

---

## Adding a New Site

The parser architecture uses the Strategy Pattern. Adding support for a new e-commerce site is two steps:

**1. Create a parser** in `src/parsers/`:

```python
# src/parsers/newsite.py
from typing import Optional
from bs4 import BeautifulSoup
from src.parsers.base import SiteParser

class NewSiteParser(SiteParser):
    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        h1 = soup.find("h1")
        return h1.get_text(strip=True) if h1 else None

    def extract_price(self, soup: BeautifulSoup) -> Optional[str]:
        return self.find_price_in_text(soup.get_text())

    def detect_availability(self, soup: BeautifulSoup, raw_html: str) -> bool:
        if self.text_contains_any(raw_html, ["out of stock", "sold out"]):
            return False
        if self.text_contains_any(raw_html, ["add to cart"]):
            return True
        return False
```

**2. Register it** in `src/parsers/registry.py`:

```python
from src.parsers.newsite import NewSiteParser
register_parser(["newsite.com"], NewSiteParser)
```

That's it. The checker auto-detects the parser from the URL.

---

## How It Works

```
URL → Domain Detection → Site Parser → HTML Parsing → State Comparison → Notification
```

1. **Fetch** — Product page fetched with rotating user agents and retry logic
2. **Detect** — Parser auto-selected from URL domain (`amazon.in` → `AmazonParser`)
3. **Parse** — Site-specific parser extracts title, price, and availability
4. **Compare** — Current state compared with previous (persisted in `state.json`)
5. **Notify** — Alert sent only on state change: unavailable → available

---

## Project Structure

```
Watch_Dog/
├── run.py                      # CLI entry point (run / check / test-notify)
├── requirements.txt
├── config.yaml.example
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── src/
│   ├── checker.py              # HTTP layer (retries, user agents)
│   ├── config.py               # YAML + env var config loader
│   ├── monitor.py              # Orchestrator with state persistence
│   ├── parsers/                # Site-specific HTML parsers
│   │   ├── base.py             # Abstract SiteParser base class
│   │   ├── registry.py         # Domain → Parser auto-detection
│   │   ├── amazon.py           # Amazon (.in, .com, .co.uk, .de)
│   │   ├── hmt.py              # HMT Watches
│   │   ├── shopify.py          # Shopify stores (DWC, etc.)
│   │   └── generic.py          # Fallback for unknown sites
│   └── notifiers/
│       ├── telegram.py         # Telegram Bot API
│       └── discord.py          # Discord webhooks
├── tests/
│   ├── test_checker.py         # Integration tests (all sites)
│   ├── test_parsers.py         # Unit tests for each parser
│   ├── test_config.py
│   ├── test_notifiers.py
│   └── fixtures/               # HTML fixtures per site
└── .github/workflows/
    ├── monitor.yml             # Scheduled monitoring
    └── test.yml                # CI tests
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Add tests for your changes
4. Run tests: `pytest tests/ -v`
5. Open a Pull Request

---

## License

MIT License

---

## Disclaimer

This tool is for personal use. Respect the terms of service of the sites you monitor. Use reasonable check intervals (5+ minutes) to avoid excessive requests.
