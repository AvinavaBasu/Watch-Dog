import pytest
import os
import tempfile
import yaml
from src.config import load_config, Config


def test_load_config_from_yaml():
    config_data = {
        "products": [{"name": "Test", "url": "https://amazon.in/dp/TEST/", "asin": "TEST"}],
        "check_interval_seconds": 600,
        "request_timeout": 15,
        "max_retries": 2,
        "log_level": "DEBUG"
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        f.flush()
        config = load_config(f.name)

    os.unlink(f.name)
    assert config.check_interval_seconds == 600
    assert len(config.products) == 1
    assert config.products[0]["name"] == "Test"


def test_env_vars_override_yaml(monkeypatch):
    monkeypatch.setenv("WATCHDOG_CHECK_INTERVAL", "120")
    monkeypatch.setenv("WATCHDOG_TELEGRAM_ENABLED", "true")
    monkeypatch.setenv("WATCHDOG_TELEGRAM_BOT_TOKEN", "env-token")
    monkeypatch.setenv("WATCHDOG_TELEGRAM_CHAT_ID", "env-chat-id")

    config_data = {
        "products": [{"name": "Test", "url": "https://amazon.in/dp/TEST/", "asin": "TEST"}],
        "check_interval_seconds": 600,
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        f.flush()
        config = load_config(f.name)

    os.unlink(f.name)
    assert config.check_interval_seconds == 120
    assert config.telegram["enabled"] is True
    assert config.telegram["bot_token"] == "env-token"


def test_default_config_without_file():
    config = load_config("/nonexistent/path.yaml")
    assert config.check_interval_seconds == 300
    assert config.telegram["enabled"] is False
