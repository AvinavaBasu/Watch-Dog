import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.checker import ProductChecker, ProductStatus
from src.config import Config

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def config():
    return Config(
        products=[],
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
    return ProductChecker(config)


def _mock_response(html: str):
    mock = MagicMock()
    mock.status_code = 200
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


# --- Amazon tests ---

def test_amazon_unavailable(checker):
    html = (FIXTURES_DIR / "unavailable.html").read_text()
    with patch("requests.Session.get", return_value=_mock_response(html)):
        status = checker.check_product("https://www.amazon.in/dp/B0DRQSHJSC/")
        assert status.available is False
        assert status.title is not None
        assert "Casio" in status.title


def test_amazon_available(checker):
    html = (FIXTURES_DIR / "available.html").read_text()
    with patch("requests.Session.get", return_value=_mock_response(html)):
        status = checker.check_product("https://www.amazon.in/dp/B0DRQSHJSC/")
        assert status.available is True
        assert status.price is not None
        assert "4,495" in status.price


# --- HMT tests ---

def test_hmt_unavailable(checker):
    html = (FIXTURES_DIR / "hmt_unavailable.html").read_text()
    with patch("requests.Session.get", return_value=_mock_response(html)):
        status = checker.check_product("https://www.hmtwatches.store/product/test-id")
        assert status.available is False
        assert status.title == "HMT NASS 12"


def test_hmt_available(checker):
    html = (FIXTURES_DIR / "hmt_available.html").read_text()
    with patch("requests.Session.get", return_value=_mock_response(html)):
        status = checker.check_product("https://www.hmtwatches.store/product/test-id")
        assert status.available is True
        assert status.price is not None
        assert "7275" in status.price
        assert status.title == "HMT NASS 12"


# --- Shopify/DWC tests ---

def test_shopify_unavailable(checker):
    html = (FIXTURES_DIR / "shopify_unavailable.html").read_text()
    with patch("requests.Session.get", return_value=_mock_response(html)):
        status = checker.check_product("https://delhiwatchcompany.com/products/dwc-terra")
        assert status.available is False
        assert status.title == "DWC Terra"


def test_shopify_available(checker):
    html = (FIXTURES_DIR / "shopify_available.html").read_text()
    with patch("requests.Session.get", return_value=_mock_response(html)):
        status = checker.check_product("https://delhiwatchcompany.com/products/dwc-terra")
        assert status.available is True
        assert status.price is not None
        assert "3,999" in status.price
        assert status.title == "DWC Terra"


# --- General tests ---

def test_network_error(checker):
    with patch("requests.Session.get", side_effect=Exception("Connection timeout")):
        status = checker.check_product("https://www.amazon.in/dp/B0DRQSHJSC/")
        assert status.available is False
        assert status.error is not None


def test_user_agent_rotation(checker):
    headers1 = checker._get_headers()
    headers2 = checker._get_headers()
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
