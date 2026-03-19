import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Config:
    products: list[dict[str, str]] = field(default_factory=list)
    check_interval_seconds: int = 300
    telegram: dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "bot_token": "",
        "chat_id": "",
    })
    discord: dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "webhook_url": "",
    })
    user_agent_rotation: bool = True
    request_timeout: int = 30
    max_retries: int = 3
    log_level: str = "INFO"


def _deep_merge(base: dict, override: dict) -> dict:
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in ("true", "1", "yes")


def _apply_env_overrides(config_dict: dict[str, Any]) -> dict[str, Any]:
    env_map = {
        "WATCHDOG_CHECK_INTERVAL": ("check_interval_seconds", int),
        "WATCHDOG_LOG_LEVEL": ("log_level", str),
    }

    for env_var, (config_key, cast_fn) in env_map.items():
        value = os.environ.get(env_var)
        if value is not None:
            config_dict[config_key] = cast_fn(value)
            logger.debug("Override %s from env var %s", config_key, env_var)

    telegram_env = {
        "WATCHDOG_TELEGRAM_ENABLED": ("enabled", _parse_bool),
        "WATCHDOG_TELEGRAM_BOT_TOKEN": ("bot_token", str),
        "WATCHDOG_TELEGRAM_CHAT_ID": ("chat_id", str),
    }
    if "telegram" not in config_dict:
        config_dict["telegram"] = {}
    for env_var, (key, cast_fn) in telegram_env.items():
        value = os.environ.get(env_var)
        if value is not None:
            config_dict["telegram"][key] = cast_fn(value)
            logger.debug("Override telegram.%s from env var %s", key, env_var)

    discord_env = {
        "WATCHDOG_DISCORD_ENABLED": ("enabled", _parse_bool),
        "WATCHDOG_DISCORD_WEBHOOK_URL": ("webhook_url", str),
    }
    if "discord" not in config_dict:
        config_dict["discord"] = {}
    for env_var, (key, cast_fn) in discord_env.items():
        value = os.environ.get(env_var)
        if value is not None:
            config_dict["discord"][key] = cast_fn(value)
            logger.debug("Override discord.%s from env var %s", key, env_var)

    return config_dict


def load_config(config_path: str = "config.yaml") -> Config:
    config_dict: dict[str, Any] = {}

    path = Path(config_path)
    if path.exists():
        logger.info("Loading configuration from %s", config_path)
        with open(path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
        if isinstance(yaml_data, dict):
            config_dict = yaml_data
    else:
        logger.warning(
            "Config file %s not found — using defaults and environment variables",
            config_path,
        )

    config_dict = _apply_env_overrides(config_dict)

    defaults = {
        "products": [],
        "check_interval_seconds": 300,
        "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
        "discord": {"enabled": False, "webhook_url": ""},
        "user_agent_rotation": True,
        "request_timeout": 30,
        "max_retries": 3,
        "log_level": "INFO",
    }

    merged = _deep_merge(defaults, config_dict)

    return Config(
        products=merged["products"],
        check_interval_seconds=int(merged["check_interval_seconds"]),
        telegram=merged["telegram"],
        discord=merged["discord"],
        user_agent_rotation=bool(merged["user_agent_rotation"]),
        request_timeout=int(merged["request_timeout"]),
        max_retries=int(merged["max_retries"]),
        log_level=str(merged["log_level"]).upper(),
    )
