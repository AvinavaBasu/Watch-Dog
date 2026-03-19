import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.checker import AmazonChecker, ProductStatus
from src.config import Config

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def config():
    return Config(
        products=[{"name": "Test Watch", "url": "https://www.amazon.in/dp/B0DRQSHJSC/", "asin": "B0DRQSHJSC"}],
        check_interval_seconds=300,
        telegram={"enabled": False, "bot_token": "", "chat_id": ""},
        discord={"enabled": False, "webhook_url": ""},
        user_agent_rotation=True,
        request_timeout=30,
        max_retries=1,
        log_level="DEBUG"
    )


@pytest.fixture
def checker(config):
    return AmazonChecker(config)


def test_product_unavailable(checker):
    html = (FIXTURES_DIR / "unavailable.html").read_text()
    with patch("requests.Session.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        status = checker.check_product("https://www.amazon.in/dp/B0DRQSHJSC/")
        assert status.available is False
        assert status.title is not None
        assert "Casio" in status.title


def test_product_available(checker):
    html = (FIXTURES_DIR / "available.html").read_text()
    with patch("requests.Session.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        status = checker.check_product("https://www.amazon.in/dp/B0DRQSHJSC/")
        assert status.available is True
        assert status.price is not None
        assert "4,495" in status.price
        assert status.title is not None


def test_product_network_error(checker):
    with patch("requests.Session.get") as mock_get:
        mock_get.side_effect = Exception("Connection timeout")

        status = checker.check_product("https://www.amazon.in/dp/B0DRQSHJSC/")
        assert status.available is False
        assert status.error is not None


def test_user_agent_rotation(checker):
    headers1 = checker._get_headers()
    headers2 = checker._get_headers()
    # Should have User-Agent header
    assert "User-Agent" in headers1
    assert "User-Agent" in headers2


def test_product_status_dataclass():
    status = ProductStatus(
        url="https://example.com",
        available=True,
        price="4,495",
        title="Test Product",
        timestamp="2026-03-19T12:00:00",
        error=None
    )
    assert status.available is True
    assert status.price == "4,495"
