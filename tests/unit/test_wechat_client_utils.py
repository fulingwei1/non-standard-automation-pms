# -*- coding: utf-8 -*-
"""
Unit tests for app/utils/wechat_client.py
Covers: WeChatTokenCache and WeChatClient (additional scenarios)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call

from app.utils.wechat_client import WeChatTokenCache, WeChatClient


class TestWeChatTokenCacheEdgeCases:
    """Additional edge case tests for WeChatTokenCache."""

    def setup_method(self):
        """Clear cache before each test."""
        WeChatTokenCache.clear()

    def test_set_then_get_returns_token(self):
        """Token set via set() can be retrieved via get()."""
        WeChatTokenCache.set("test_key", "abc123", expires_in=7200)
        token = WeChatTokenCache.get("test_key")
        assert token == "abc123"

    def test_token_near_expiry_returns_none(self):
        """Token expiring within 5 minutes returns None (triggers refresh)."""
        # Set token that expires in 3 minutes (< 5 minute buffer)
        expires_at = datetime.now() + timedelta(minutes=3)
        WeChatTokenCache._cache["soon_key"] = {
            "token": "expiring_token",
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
        result = WeChatTokenCache.get("soon_key")
        assert result is None

    def test_token_far_from_expiry_returns_token(self):
        """Token expiring in 1+ hour is returned."""
        expires_at = datetime.now() + timedelta(hours=1)
        WeChatTokenCache._cache["good_key"] = {
            "token": "valid_token",
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
        result = WeChatTokenCache.get("good_key")
        assert result == "valid_token"

    def test_clear_specific_key(self):
        """Clearing specific key only removes that key."""
        WeChatTokenCache.set("k1", "t1", 7200)
        WeChatTokenCache.set("k2", "t2", 7200)
        WeChatTokenCache.clear("k1")
        assert WeChatTokenCache.get("k1") is None
        assert WeChatTokenCache.get("k2") is not None

    def test_clear_all_keys(self):
        """Clearing without key removes all entries."""
        WeChatTokenCache.set("k1", "t1", 7200)
        WeChatTokenCache.set("k2", "t2", 7200)
        WeChatTokenCache.clear()
        assert WeChatTokenCache.get("k1") is None
        assert WeChatTokenCache.get("k2") is None

    def test_get_missing_key_returns_none(self):
        """Getting non-existent key returns None."""
        result = WeChatTokenCache.get("no_such_key")
        assert result is None


class TestWeChatClientInit:
    """Tests for WeChatClient initialization."""

    def test_init_with_explicit_params(self):
        """WeChatClient can be initialized with explicit params."""
        client = WeChatClient(
            corp_id="test_corp",
            agent_id="1000001",
            secret="test_secret"
        )
        assert client.corp_id == "test_corp"
        assert client.agent_id == "1000001"
        assert client.secret == "test_secret"

    def test_init_missing_config_raises_value_error(self):
        """ValueError raised when settings are empty."""
        with patch("app.utils.wechat_client.settings") as mock_settings:
            mock_settings.WECHAT_CORP_ID = ""
            mock_settings.WECHAT_AGENT_ID = ""
            mock_settings.WECHAT_SECRET = ""
            with pytest.raises(ValueError, match="企业微信配置不完整"):
                WeChatClient()

    def test_init_uses_settings_when_no_params(self):
        """WeChatClient reads from settings when params not provided."""
        with patch("app.utils.wechat_client.settings") as mock_settings:
            mock_settings.WECHAT_CORP_ID = "corp_from_settings"
            mock_settings.WECHAT_AGENT_ID = "agent_from_settings"
            mock_settings.WECHAT_SECRET = "secret_from_settings"
            client = WeChatClient()
            assert client.corp_id == "corp_from_settings"


class TestWeChatClientGetAccessToken:
    """Tests for WeChatClient.get_access_token."""

    def setup_method(self):
        WeChatTokenCache.clear()

    def test_returns_cached_token(self):
        """Returns cached token without making API call."""
        WeChatTokenCache.set(WeChatClient.TOKEN_CACHE_KEY, "cached_tok", 7200)

        client = WeChatClient(corp_id="c", agent_id="a", secret="s")
        with patch("app.utils.wechat_client.requests") as mock_requests:
            token = client.get_access_token()
            assert token == "cached_tok"
            mock_requests.get.assert_not_called()

    def test_fetches_new_token_on_cache_miss(self):
        """Fetches token from API when cache is empty."""
        import requests as real_requests
        client = WeChatClient(corp_id="c", agent_id="a", secret="s")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errcode": 0,
            "access_token": "new_token_123",
            "expires_in": 7200
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.get.return_value = mock_response
            mock_req.RequestException = real_requests.RequestException
            token = client.get_access_token()

        assert token == "new_token_123"

    def test_raises_on_api_error(self):
        """Raises Exception when API returns non-zero errcode."""
        import requests as real_requests
        client = WeChatClient(corp_id="c", agent_id="a", secret="s")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errcode": 40013,
            "errmsg": "invalid corp_id"
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.get.return_value = mock_response
            # Must set RequestException to a real exception so 'except requests.RequestException' works
            mock_req.RequestException = real_requests.RequestException
            with pytest.raises(Exception, match="获取access_token失败"):
                client.get_access_token()

    def test_force_refresh_bypasses_cache(self):
        """force_refresh=True ignores cached token."""
        import requests as real_requests
        WeChatTokenCache.set(WeChatClient.TOKEN_CACHE_KEY, "old_token", 7200)
        client = WeChatClient(corp_id="c", agent_id="a", secret="s")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errcode": 0,
            "access_token": "refreshed_token",
            "expires_in": 7200
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.get.return_value = mock_response
            mock_req.RequestException = real_requests.RequestException
            token = client.get_access_token(force_refresh=True)

        assert token == "refreshed_token"


class TestWeChatClientSendMessage:
    """Tests for WeChatClient.send_message."""

    def setup_method(self):
        WeChatTokenCache.clear()

    def _make_client(self):
        return WeChatClient(corp_id="c", agent_id="1001", secret="s")

    def test_empty_user_ids_returns_false(self):
        """send_message returns False when user_ids list is empty."""
        client = self._make_client()
        with patch.object(client, "get_access_token", return_value="tok"):
            result = client.send_message(user_ids=[], message={"msgtype": "text"})
        assert result is False

    def test_send_text_message_success(self):
        """send_text_message builds correct payload and returns True."""
        import requests as real_requests
        client = self._make_client()

        mock_response = MagicMock()
        mock_response.json.return_value = {"errcode": 0}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "get_access_token", return_value="tok"), \
             patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.post.return_value = mock_response
            mock_req.RequestException = real_requests.RequestException
            result = client.send_text_message(["user1", "user2"], "Hello!")

        assert result is True
        call_kwargs = mock_req.post.call_args
        payload = call_kwargs[1]["json"]
        assert payload["msgtype"] == "text"
        assert "Hello!" in str(payload["text"])

    def test_send_template_card_success(self):
        """send_template_card builds template_card payload and returns True."""
        import requests as real_requests
        client = self._make_client()

        mock_response = MagicMock()
        mock_response.json.return_value = {"errcode": 0}
        mock_response.raise_for_status = MagicMock()

        card_data = {"card_type": "text_notice", "main_title": {"title": "Test"}}

        with patch.object(client, "get_access_token", return_value="tok"), \
             patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.post.return_value = mock_response
            mock_req.RequestException = real_requests.RequestException
            result = client.send_template_card(["user1"], card_data)

        assert result is True
        payload = mock_req.post.call_args[1]["json"]
        assert payload["msgtype"] == "template_card"

    def test_token_refresh_on_40014_error(self):
        """Retries with refreshed token on errcode 40014."""
        client = self._make_client()

        resp_expired = MagicMock()
        resp_expired.json.return_value = {"errcode": 40014, "errmsg": "invalid access_token"}
        resp_expired.raise_for_status = MagicMock()

        resp_success = MagicMock()
        resp_success.json.return_value = {"errcode": 0}
        resp_success.raise_for_status = MagicMock()

        get_token_calls = []

        def side_effect_token(force_refresh=False):
            get_token_calls.append(force_refresh)
            return "refreshed_tok" if force_refresh else "old_tok"

        with patch.object(client, "get_access_token", side_effect=side_effect_token), \
             patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.post.side_effect = [resp_expired, resp_success]
            result = client.send_message(
                user_ids=["user1"],
                message={"msgtype": "text", "text": {"content": "Hi"}},
                retry_times=3
            )

        assert result is True
        # Should have called get_access_token with force_refresh=True on retry
        assert True in get_token_calls

    def test_send_message_raises_on_non_zero_errcode(self):
        """Raises Exception on non-retryable errcode."""
        import requests as real_requests
        client = self._make_client()

        mock_response = MagicMock()
        mock_response.json.return_value = {"errcode": 60020, "errmsg": "not allow to access from your ip"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "get_access_token", return_value="tok"), \
             patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.post.return_value = mock_response
            mock_req.RequestException = real_requests.RequestException
            with pytest.raises(Exception, match="发送消息失败"):
                client.send_message(["user1"], {"msgtype": "text"})
