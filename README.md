# Watch Dog 🐕

**Never miss a restock. Monitor Amazon product availability and get instant notifications.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/yourusername/Watch_Dog/actions/workflows/test.yml/badge.svg)](https://github.com/yourusername/Watch_Dog/actions)

---

## Features

- **Real-time Amazon product monitoring** — Continuously checks product pages for availability
- **Telegram and Discord notifications** — Get instant alerts when products come back in stock
- **Configurable check intervals** — Set how often to check (default: 5 minutes)
- **Multiple product tracking** — Monitor several products at once
- **Rotating user agents** — Reduces detection risk with randomized browser fingerprints
- **GitHub Actions support** — Serverless monitoring with no infrastructure to maintain
- **Docker support** — Self-hosted deployment with a single command
- **State persistence** — Remembers availability across restarts; only notifies on state change

---

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Watch_Dog.git
   cd Watch_Dog
   ```

2. **Copy configuration files**
   ```bash
   cp config.yaml.example config.yaml
   cp .env.example .env
   ```

3. **Edit `config.yaml`** with the products you want to monitor (see [Configuration](#configuration))

4. **Set up Telegram** (see [Telegram Setup](#telegram-setup))

5. **Run the monitor**
   ```bash
   python run.py run
   ```

---

## Telegram Setup

1. **Create a bot** — Message [@BotFather](https://t.me/BotFather) on Telegram
2. **Send** `/newbot` and follow the prompts to name your bot
3. **Copy the bot token** — BotFather will give you a token like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
4. **Get your chat ID** — Message [@userinfobot](https://t.me/userinfobot) and it will reply with your chat ID
5. **Add to `.env`**:
   ```env
   WATCHDOG_TELEGRAM_ENABLED=true
   WATCHDOG_TELEGRAM_BOT_TOKEN=your-bot-token-here
   WATCHDOG_TELEGRAM_CHAT_ID=your-chat-id-here
   ```

---

## Discord Setup

1. Go to your Discord server → **Server Settings** → **Integrations** → **Webhooks**
2. Click **New Webhook**, configure name and channel, then **Copy Webhook URL**
3. Add to `.env`:
   ```env
   WATCHDOG_DISCORD_ENABLED=true
   WATCHDOG_DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

---

## Configuration

### `config.yaml`

| Key | Description | Default |
|-----|-------------|---------|
| `products` | List of products to monitor | `[]` |
| `check_interval_seconds` | Seconds between checks | `300` |
| `request_timeout` | HTTP request timeout (seconds) | `30` |
| `max_retries` | Retries per failed request | `3` |
| `user_agent_rotation` | Rotate user agents per request | `true` |
| `log_level` | Logging level | `INFO` |

**Product format:**
```yaml
products:
  - name: "Product Display Name"
    url: "https://www.amazon.in/dp/XXXXXXXXXX/"
    asin: "XXXXXXXXXX"
```

**Example — monitoring multiple products:**
```yaml
products:
  - name: "Casio Youth AE-1200WHL-5AVDF"
    url: "https://www.amazon.in/dp/B0DRQSHJSC/"
    asin: "B0DRQSHJSC"
  - name: "Another Product"
    url: "https://www.amazon.in/dp/B0XXXXXXXX/"
    asin: "B0XXXXXXXX"

check_interval_seconds: 300
```

### Environment Variables

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

## Usage

```bash
# Start continuous monitoring
python run.py run

# One-time check (useful for GitHub Actions)
python run.py check

# Test notifications
python run.py test-notify
```

---

## Deployment Options

### Option 1: GitHub Actions (Recommended — Free)

1. **Fork** this repository
2. **Add secrets** in Settings → Secrets and variables → Actions:
   - `TELEGRAM_BOT_TOKEN` — Your bot token
   - `TELEGRAM_CHAT_ID` — Your chat ID
   - Optional: `DISCORD_ENABLED`, `DISCORD_WEBHOOK_URL`
3. **Enable GitHub Actions** — The workflow runs automatically every 5 minutes

No server, no cost.

### Option 2: Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f watchdog
```

State is persisted in `./data` for availability tracking across restarts.

### Option 3: Local / VPS

```bash
# Using screen (recommended for long-running)
screen -S watchdog
python run.py run
# Ctrl+A, D to detach

# Or using tmux
tmux new -s watchdog
python run.py run
# Ctrl+B, D to detach
```

---

## Adding More Products

1. Open `config.yaml`
2. Add a new entry under `products`:

```yaml
products:
  - name: "Existing Product"
    url: "https://www.amazon.in/dp/B0DRQSHJSC/"
    asin: "B0DRQSHJSC"
  - name: "New Product"
    url: "https://www.amazon.in/dp/B0XXXXXXXX/"
    asin: "B0XXXXXXXX"
```

3. Restart the monitor (or wait for the next check cycle)

---

## How It Works

1. **Fetch** — Fetches the product page with rotating user agents
2. **Parse** — Parses HTML to detect availability (e.g., "Add to Cart", "In stock", "Currently unavailable")
3. **Compare** — Compares current state with the previous state
4. **Notify** — Sends a notification only when the state changes from unavailable → available
5. **Persist** — Saves state to `state.json` so restarts don't trigger duplicate notifications

---

## Project Structure

```
Watch_Dog/
├── .github/
│   └── workflows/
│       ├── monitor.yml      # GitHub Actions (every 5 min)
│       └── test.yml        # CI tests
├── src/
│   ├── checker.py          # Amazon availability checker
│   ├── config.py           # Configuration loader
│   └── notifiers/
│       ├── __init__.py
│       ├── telegram.py     # Telegram notifications
│       └── discord.py      # Discord notifications
├── tests/
│   └── fixtures/           # HTML fixtures for tests
├── config.yaml.example     # Example config
├── .env.example            # Example environment variables
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── run.py                  # Main entry point
└── README.md
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Disclaimer

This tool is for personal use. Be respectful of Amazon's terms of service. Use reasonable check intervals (5+ minutes recommended) to avoid excessive requests.
