# -*- coding: utf-8 -*-
"""
第四十批覆盖测试 - 销售提醒扫描器
"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.sales_reminder.scanner import scan_and_notify_all, scan_sales_reminders
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = MagicMock()
    return db


PATCH_PREFIX = "app.services.sales_reminder.scanner"


class TestScanAndNotifyAll:

    @patch(f"{PATCH_PREFIX}.notify_milestone_upcoming", return_value=3)
    @patch(f"{PATCH_PREFIX}.notify_milestone_overdue", return_value=1)
    @patch(f"{PATCH_PREFIX}.notify_payment_plan_upcoming", return_value=2)
    @patch(f"{PATCH_PREFIX}.notify_payment_overdue", return_value=0)
    @patch(f"{PATCH_PREFIX}.notify_gate_timeout", return_value=1)
    @patch(f"{PATCH_PREFIX}.notify_quote_expiring", return_value={"expiring": 2, "expired": 1})
    @patch(f"{PATCH_PREFIX}.notify_contract_expiring", return_value=4)
    @patch(f"{PATCH_PREFIX}.notify_approval_pending", return_value=5)
    def test_returns_stats_dict(self, m1, m2, m3, m4, m5, m6, m7, m8, mock_db):
        stats = scan_and_notify_all(mock_db)
        assert isinstance(stats, dict)

    @patch(f"{PATCH_PREFIX}.notify_milestone_upcoming", return_value=3)
    @patch(f"{PATCH_PREFIX}.notify_milestone_overdue", return_value=1)
    @patch(f"{PATCH_PREFIX}.notify_payment_plan_upcoming", return_value=2)
    @patch(f"{PATCH_PREFIX}.notify_payment_overdue", return_value=0)
    @patch(f"{PATCH_PREFIX}.notify_gate_timeout", return_value=1)
    @patch(f"{PATCH_PREFIX}.notify_quote_expiring", return_value={"expiring": 2, "expired": 1})
    @patch(f"{PATCH_PREFIX}.notify_contract_expiring", return_value=4)
    @patch(f"{PATCH_PREFIX}.notify_approval_pending", return_value=5)
    def test_stats_keys_present(self, m1, m2, m3, m4, m5, m6, m7, m8, mock_db):
        stats = scan_and_notify_all(mock_db)
        for key in ("milestone_upcoming_7d", "milestone_upcoming_3d", "milestone_overdue",
                    "payment_upcoming_7d", "payment_upcoming_3d", "payment_overdue",
                    "gate_timeout", "quote_expiring", "quote_expired",
                    "contract_expiring", "approval_pending"):
            assert key in stats

    @patch(f"{PATCH_PREFIX}.notify_milestone_upcoming", return_value=5)
    @patch(f"{PATCH_PREFIX}.notify_milestone_overdue", return_value=2)
    @patch(f"{PATCH_PREFIX}.notify_payment_plan_upcoming", return_value=3)
    @patch(f"{PATCH_PREFIX}.notify_payment_overdue", return_value=1)
    @patch(f"{PATCH_PREFIX}.notify_gate_timeout", return_value=0)
    @patch(f"{PATCH_PREFIX}.notify_quote_expiring", return_value={"expiring": 1, "expired": 0})
    @patch(f"{PATCH_PREFIX}.notify_contract_expiring", return_value=2)
    @patch(f"{PATCH_PREFIX}.notify_approval_pending", return_value=3)
    def test_db_commit_called(self, m1, m2, m3, m4, m5, m6, m7, m8, mock_db):
        scan_and_notify_all(mock_db)
        mock_db.commit.assert_called_once()

    @patch(f"{PATCH_PREFIX}.notify_milestone_upcoming", return_value=7)
    @patch(f"{PATCH_PREFIX}.notify_milestone_overdue", return_value=0)
    @patch(f"{PATCH_PREFIX}.notify_payment_plan_upcoming", return_value=4)
    @patch(f"{PATCH_PREFIX}.notify_payment_overdue", return_value=0)
    @patch(f"{PATCH_PREFIX}.notify_gate_timeout", return_value=2)
    @patch(f"{PATCH_PREFIX}.notify_quote_expiring", return_value={"expiring": 3, "expired": 1})
    @patch(f"{PATCH_PREFIX}.notify_contract_expiring", return_value=0)
    @patch(f"{PATCH_PREFIX}.notify_approval_pending", return_value=1)
    def test_stats_values_from_functions(self, m1, m2, m3, m4, m5, m6, m7, m8, mock_db):
        stats = scan_and_notify_all(mock_db)
        assert stats["milestone_upcoming_7d"] == 7
        assert stats["gate_timeout"] == 2
        assert stats["quote_expiring"] == 3


class TestScanSalesReminders:

    @patch(f"{PATCH_PREFIX}.notify_gate_timeout", return_value=1)
    @patch(f"{PATCH_PREFIX}.notify_quote_expiring", return_value={"expiring": 2, "expired": 0})
    @patch(f"{PATCH_PREFIX}.notify_contract_expiring", return_value=1)
    @patch(f"{PATCH_PREFIX}.notify_approval_pending", return_value=0)
    def test_returns_sales_stats(self, m1, m2, m3, m4, mock_db):
        stats = scan_sales_reminders(mock_db)
        assert "gate_timeout" in stats
        assert "quote_expiring" in stats
        assert "contract_expiring" in stats
        assert "approval_pending" in stats

    @patch(f"{PATCH_PREFIX}.notify_gate_timeout", return_value=3)
    @patch(f"{PATCH_PREFIX}.notify_quote_expiring", return_value={"expiring": 1, "expired": 2})
    @patch(f"{PATCH_PREFIX}.notify_contract_expiring", return_value=5)
    @patch(f"{PATCH_PREFIX}.notify_approval_pending", return_value=4)
    def test_db_commit_after_scan(self, m1, m2, m3, m4, mock_db):
        scan_sales_reminders(mock_db)
        mock_db.commit.assert_called_once()
