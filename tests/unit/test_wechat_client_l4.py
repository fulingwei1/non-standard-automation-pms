# -*- coding: utf-8 -*-
"""
Unit tests for app/utils/wechat_client.py — L4组补充
覆盖 markdown 消息、网络重试、WeChatTokenCache 的 set 语义
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.utils.wechat_client import WeChatClient, WeChatTokenCache


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client():
    return WeChatClient(corp_id="corp1", agent_id="1000001", secret="secret1")


def _mock_ok_response():
    resp = MagicMock()
    resp.json.return_value = {"errcode": 0, "errmsg": "ok"}
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# WeChatTokenCache — extra coverage
# ---------------------------------------------------------------------------

class TestWeChatTokenCacheL4:
    """Extra tests for WeChatTokenCache."""

    def setup_method(self):
        WeChatTokenCache.clear()

    def test_expires_in_sets_future_expiry(self):
        """expires_in=7200 sets expires_at ~1h55m from now."""
        WeChatTokenCache.set("k", "tok", expires_in=7200)
        entry = WeChatTokenCache._cache["k"]
        # expires_at should be approximately now + (7200-300)s = now + 6900s
        delta = (entry["expires_at"] - datetime.now()).total_seconds()
        assert 6800 < delta < 7000

    def test_short_expires_in_immediately_expired(self):
        """Very short expires_in (< 300s) is already past the buffer → returns None."""
        # expires_in=60 → expires_at = now + (60-300) = now - 240s (in the past)
        WeChatTokenCache.set("k", "tok", expires_in=60)
        result = WeChatTokenCache.get("k")
        assert result is None

    def test_clear_nonexistent_key_is_noop(self):
        """Clearing a key that doesn't exist doesn't raise."""
        WeChatTokenCache.clear("no_such_key")  # should not raise

    def test_created_at_set_correctly(self):
        """created_at is set to approximately now."""
        before = datetime.now()
        WeChatTokenCache.set("k2", "tok2", expires_in=7200)
        after = datetime.now()
        entry = WeChatTokenCache._cache["k2"]
        assert before <= entry["created_at"] <= after


# ---------------------------------------------------------------------------
# WeChatClient.get_access_token — extra
# ---------------------------------------------------------------------------

class TestGetAccessTokenL4:
    """Extra tests for get_access_token."""

    def setup_method(self):
        WeChatTokenCache.clear()

    def test_request_exception_is_wrapped(self):
        """requests.RequestException is caught and re-raised as generic Exception."""
        import requests as real_requests
        client = _make_client()

        with patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.get.side_effect = real_requests.ConnectionError("timeout")
            mock_req.RequestException = real_requests.RequestException

            with pytest.raises(Exception, match="请求企业微信API失败"):
                client.get_access_token()

    def test_token_cached_after_fetch(self):
        """After a successful fetch, subsequent call uses cache (no 2nd HTTP call)."""
        import requests as real_requests
        client = _make_client()

        resp = MagicMock()
        resp.json.return_value = {
            "errcode": 0,
            "access_token": "tok_cache",
            "expires_in": 7200
        }
        resp.raise_for_status = MagicMock()

        with patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.get.return_value = resp
            mock_req.RequestException = real_requests.RequestException

            t1 = client.get_access_token()
            t2 = client.get_access_token()  # should use cache

        assert t1 == "tok_cache"
        assert t2 == "tok_cache"
        assert mock_req.get.call_count == 1  # only one HTTP call


# ---------------------------------------------------------------------------
# WeChatClient.send_message — markdown and misc
# ---------------------------------------------------------------------------

class TestSendMessageL4:
    """Extra tests for send_message."""

    def setup_method(self):
        WeChatTokenCache.clear()

    def test_send_markdown_message(self):
        """Builds correct payload for markdown msgtype."""
        import requests as real_requests
        client = _make_client()

        with patch.object(client, "get_access_token", return_value="tok"), \
             patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.post.return_value = _mock_ok_response()
            mock_req.RequestException = real_requests.RequestException

            result = client.send_message(
                user_ids=["user1"],
                message={
                    "msgtype": "markdown",
                    "markdown": {"content": "**Hello**"}
                }
            )

        assert result is True
        payload = mock_req.post.call_args[1]["json"]
        assert payload["msgtype"] == "markdown"
        assert payload["markdown"]["content"] == "**Hello**"

    def test_send_unknown_msgtype_uses_update(self):
        """Unknown msgtype falls through to payload.update(message)."""
        import requests as real_requests
        client = _make_client()

        with patch.object(client, "get_access_token", return_value="tok"), \
             patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.post.return_value = _mock_ok_response()
            mock_req.RequestException = real_requests.RequestException

            result = client.send_message(
                user_ids=["user1"],
                message={
                    "msgtype": "news",
                    "news": {"articles": [{"title": "Test"}]}
                }
            )

        assert result is True
        payload = mock_req.post.call_args[1]["json"]
        assert "news" in payload

    def test_user_ids_joined_with_pipe(self):
        """Multiple user_ids are joined with '|' in touser field."""
        import requests as real_requests
        client = _make_client()

        with patch.object(client, "get_access_token", return_value="tok"), \
             patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.post.return_value = _mock_ok_response()
            mock_req.RequestException = real_requests.RequestException

            client.send_text_message(["alice", "bob", "charlie"], "Hi all")

        payload = mock_req.post.call_args[1]["json"]
        assert payload["touser"] == "alice|bob|charlie"

    def test_request_exception_retries_then_raises(self):
        """RequestException triggers retry; after retry_times exhausted, raises."""
        import requests as real_requests
        client = _make_client()

        with patch.object(client, "get_access_token", return_value="tok"), \
             patch("app.utils.wechat_client.requests") as mock_req, \
             patch("app.utils.wechat_client.time") as mock_time:
            mock_req.post.side_effect = real_requests.ConnectionError("net down")
            mock_req.RequestException = real_requests.RequestException
            mock_time.sleep = MagicMock()

            with pytest.raises(Exception, match="请求企业微信API失败"):
                client.send_message(
                    user_ids=["u1"],
                    message={"msgtype": "text", "text": {"content": "hi"}},
                    retry_times=2
                )

        # Called retry_times=2 times
        assert mock_req.post.call_count == 2

    def test_agentid_set_in_payload(self):
        """agentid from client is included in the payload."""
        import requests as real_requests
        client = _make_client()  # agent_id="1000001"

        with patch.object(client, "get_access_token", return_value="tok"), \
             patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.post.return_value = _mock_ok_response()
            mock_req.RequestException = real_requests.RequestException
            client.send_text_message(["u1"], "test")

        payload = mock_req.post.call_args[1]["json"]
        assert payload["agentid"] == "1000001"

    def test_access_token_in_url_params(self):
        """access_token is passed as a URL query parameter."""
        import requests as real_requests
        client = _make_client()

        with patch.object(client, "get_access_token", return_value="my_tok"), \
             patch("app.utils.wechat_client.requests") as mock_req:
            mock_req.post.return_value = _mock_ok_response()
            mock_req.RequestException = real_requests.RequestException
            client.send_text_message(["u1"], "hello")

        call_kwargs = mock_req.post.call_args[1]
        assert call_kwargs["params"]["access_token"] == "my_tok"
