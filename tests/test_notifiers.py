import pytest
from unittest.mock import patch, MagicMock
import requests
from src.notifiers.telegram import TelegramNotifier
from src.notifiers.discord import DiscordNotifier
from src.checker import ProductStatus


@pytest.fixture
def product_status():
    return ProductStatus(
        url="https://www.amazon.in/dp/B0DRQSHJSC/",
        available=True,
        price="4,495",
        title="Casio Youth AE-1200WHL-5AVDF",
        timestamp="2026-03-19T12:00:00",
        error=None
    )


class TestTelegramNotifier:
    def test_format_message(self, product_status):
        notifier = TelegramNotifier("test-token", "test-chat-id")
        message = notifier._format_message(product_status, "Test Watch")
        assert "PRODUCT AVAILABLE" in message
        assert "4,495" in message
        assert "amazon.in" in message

    @patch("requests.Session.post")
    def test_send_notification_success(self, mock_post, product_status):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        notifier = TelegramNotifier("test-token", "test-chat-id")
        result = notifier.send_notification(product_status, "Test Watch")
        assert result is True
        mock_post.assert_called_once()

    @patch("requests.Session.post")
    def test_send_notification_failure(self, mock_post, product_status):
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        notifier = TelegramNotifier("test-token", "test-chat-id")
        result = notifier.send_notification(product_status, "Test Watch")
        assert result is False

    @patch("requests.Session.post")
    def test_send_test_message(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        notifier = TelegramNotifier("test-token", "test-chat-id")
        result = notifier.send_test_message()
        assert result is True


class TestDiscordNotifier:
    @patch("requests.Session.post")
    def test_send_notification_success(self, mock_post, product_status):
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        notifier = DiscordNotifier("https://discord.com/api/webhooks/test")
        result = notifier.send_notification(product_status, "Test Watch")
        assert result is True

    @patch("requests.Session.post")
    def test_send_notification_failure(self, mock_post, product_status):
        mock_post.side_effect = requests.exceptions.RequestException("Webhook Error")

        notifier = DiscordNotifier("https://discord.com/api/webhooks/test")
        result = notifier.send_notification(product_status, "Test Watch")
        assert result is False
