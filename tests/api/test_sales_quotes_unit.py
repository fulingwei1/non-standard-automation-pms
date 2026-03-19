# -*- coding: utf-8 -*-
"""
sales/quotes.py 端点单元测试

重点覆盖：
- 旧报价审批入口兼容 payload 映射
- 审批服务错误到 HTTP 状态码的转换
"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

redis_mock = MagicMock()
sys.modules.setdefault("redis", redis_mock)
sys.modules.setdefault("redis.exceptions", MagicMock())

import os

os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("ENABLE_SCHEDULER", "false")

import pytest
from fastapi import HTTPException


def _make_db():
    db = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


def _make_user(user_id=7):
    return SimpleNamespace(id=user_id, username="approver")


class TestApproveQuote:

    def test_approve_quote_legacy_payload_maps_to_approve(self):
        from app.api.v1.endpoints.sales.quotes import approve_quote

        db = _make_db()
        current_user = _make_user()

        with (
            patch("app.api.v1.endpoints.sales.quotes.get_or_404"),
            patch("app.api.v1.endpoints.sales.quotes.QuoteApprovalService") as MockService,
        ):
            MockService.return_value.perform_quote_action.return_value = {
                "task_id": 88,
                "action": "approve",
                "instance_status": "APPROVED",
            }

            result = approve_quote(
                quote_id=1,
                payload={"approved": True, "remark": "同意报价"},
                db=db,
                current_user=current_user,
            )

        MockService.return_value.perform_quote_action.assert_called_once_with(
            quote_id=1,
            action="approve",
            approver_id=7,
            comment="同意报价",
        )
        db.commit.assert_called_once()
        db.rollback.assert_not_called()
        assert result.code == 200
        assert result.message == "报价审批完成"

    def test_approve_quote_action_payload_maps_to_reject(self):
        from app.api.v1.endpoints.sales.quotes import approve_quote

        db = _make_db()
        current_user = _make_user(user_id=9)

        with (
            patch("app.api.v1.endpoints.sales.quotes.get_or_404"),
            patch("app.api.v1.endpoints.sales.quotes.QuoteApprovalService") as MockService,
        ):
            MockService.return_value.perform_quote_action.return_value = {
                "task_id": 99,
                "action": "reject",
                "instance_status": "REJECTED",
            }

            approve_quote(
                quote_id=2,
                payload={"action": "reject", "comment": "价格偏低"},
                db=db,
                current_user=current_user,
            )

        MockService.return_value.perform_quote_action.assert_called_once_with(
            quote_id=2,
            action="reject",
            approver_id=9,
            comment="价格偏低",
        )
        db.commit.assert_called_once()

    def test_approve_quote_without_pending_task_returns_400(self):
        from app.api.v1.endpoints.sales.quotes import approve_quote

        db = _make_db()
        current_user = _make_user()

        with (
            patch("app.api.v1.endpoints.sales.quotes.get_or_404"),
            patch("app.api.v1.endpoints.sales.quotes.QuoteApprovalService") as MockService,
        ):
            MockService.return_value.perform_quote_action.side_effect = ValueError(
                "当前用户没有该报价的待审批任务，请通过统一审批流程操作"
            )

            with pytest.raises(HTTPException) as exc_info:
                approve_quote(
                    quote_id=3,
                    payload={"approved": True},
                    db=db,
                    current_user=current_user,
                )

        assert exc_info.value.status_code == 400
        assert "待审批任务" in exc_info.value.detail
        db.rollback.assert_called_once()

    def test_approve_quote_not_found_returns_404(self):
        from app.api.v1.endpoints.sales.quotes import approve_quote

        db = _make_db()
        current_user = _make_user()

        with (
            patch("app.api.v1.endpoints.sales.quotes.get_or_404"),
            patch("app.api.v1.endpoints.sales.quotes.QuoteApprovalService") as MockService,
        ):
            MockService.return_value.perform_quote_action.side_effect = ValueError("报价不存在")

            with pytest.raises(HTTPException) as exc_info:
                approve_quote(
                    quote_id=404,
                    payload={"action": "approve"},
                    db=db,
                    current_user=current_user,
                )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "报价不存在"
        db.rollback.assert_called_once()


class TestQuoteStatistics:

    def test_get_quote_statistics_uses_statistics_service(self):
        from app.api.v1.endpoints.sales.quotes import get_quote_statistics

        db = _make_db()
        current_user = _make_user()

        statistics_payload = {
            "total": 4,
            "draft": 1,
            "inReview": 1,
            "approved": 1,
            "sent": 0,
            "expired": 0,
            "rejected": 0,
            "accepted": 0,
            "converted": 1,
            "totalAmount": 2000000.0,
            "avgAmount": 500000.0,
            "avgMargin": 22.5,
            "conversionRate": 25.0,
            "expiringSoon": 1,
        }

        with patch("app.api.v1.endpoints.sales.quotes.QuoteStatisticsService") as MockService:
            MockService.return_value.get_statistics.return_value = statistics_payload

            result = get_quote_statistics(db=db, current_user=current_user)

        MockService.return_value.get_statistics.assert_called_once_with(current_user=current_user)
        assert result.code == 200
        assert result.data == statistics_payload
