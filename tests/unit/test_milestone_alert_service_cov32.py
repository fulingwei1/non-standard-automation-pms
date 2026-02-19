# -*- coding: utf-8 -*-
"""
第三十二批覆盖率测试 - 里程碑告警服务
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date, timedelta

try:
    from app.services.alert.milestone_alert_service import MilestoneAlertService
    HAS_MAS = True
except Exception:
    HAS_MAS = False

pytestmark = pytest.mark.skipif(not HAS_MAS, reason="milestone_alert_service 导入失败")


def make_service():
    db = MagicMock()
    svc = MilestoneAlertService(db)
    return svc, db


class TestMilestoneAlertServiceInit:
    def test_init(self):
        db = MagicMock()
        svc = MilestoneAlertService(db)
        assert svc.db is db


class TestGetUpcomingMilestones:
    def test_get_upcoming_returns_list(self):
        """获取即将到期里程碑"""
        svc, db = make_service()
        mock_ms = [MagicMock(), MagicMock()]
        db.query.return_value.filter.return_value.all.return_value = mock_ms

        today = date.today()
        result = svc._get_upcoming_milestones(today)
        assert isinstance(result, list)


class TestGetOverdueMilestones:
    def test_get_overdue_returns_list(self):
        """获取已逾期里程碑"""
        svc, db = make_service()
        mock_ms = [MagicMock()]
        db.query.return_value.filter.return_value.all.return_value = mock_ms

        today = date.today()
        result = svc._get_overdue_milestones(today)
        assert isinstance(result, list)

    def test_overdue_empty(self):
        """无逾期里程碑时返回空列表"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.all.return_value = []

        result = svc._get_overdue_milestones(date.today())
        assert result == []


class TestGetOrCreateAlertRule:
    def test_get_existing_warning_rule(self):
        """已存在预警规则时直接返回"""
        svc, db = make_service()
        mock_rule = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_rule

        result = svc._get_or_create_warning_rule()
        assert result is mock_rule

    def test_create_warning_rule_if_not_exists(self):
        """不存在预警规则时创建"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.alert.milestone_alert_service.AlertRule") as MockRule:
            mock_rule = MagicMock()
            MockRule.return_value = mock_rule
            result = svc._get_or_create_warning_rule()
        db.add.assert_called_once()

    def test_get_existing_critical_rule(self):
        """已存在严重告警规则时直接返回"""
        svc, db = make_service()
        mock_rule = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_rule

        result = svc._get_or_create_critical_rule()
        assert result is mock_rule

    def test_create_critical_rule_if_not_exists(self):
        """不存在严重告警规则时创建"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.alert.milestone_alert_service.AlertRule") as MockRule:
            mock_rule = MagicMock()
            MockRule.return_value = mock_rule
            result = svc._get_or_create_critical_rule()
        db.add.assert_called_once()


class TestShouldCreateAlert:
    def test_should_create_when_no_existing(self):
        """无已有告警时应该创建"""
        svc, db = make_service()
        mock_ms = MagicMock()
        mock_ms.id = 1

        db.query.return_value.filter.return_value.first.return_value = None
        result = svc._should_create_alert(mock_ms, "milestone_upcoming")
        assert result is True

    def test_should_not_create_when_exists(self):
        """已有告警时不应重复创建"""
        svc, db = make_service()
        mock_ms = MagicMock()
        mock_ms.id = 1

        mock_existing_alert = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_existing_alert
        result = svc._should_create_alert(mock_ms, "milestone_upcoming")
        assert result is False


class TestCheckMilestoneAlerts:
    def test_check_no_milestones(self):
        """无里程碑时返回0"""
        svc, db = make_service()

        with patch.object(svc, "_get_upcoming_milestones", return_value=[]), \
             patch.object(svc, "_get_overdue_milestones", return_value=[]), \
             patch.object(svc, "_get_or_create_warning_rule", return_value=MagicMock()), \
             patch.object(svc, "_get_or_create_critical_rule", return_value=MagicMock()), \
             patch.object(svc, "_process_upcoming_milestones", return_value=0), \
             patch.object(svc, "_process_overdue_milestones", return_value=0):
            result = svc.check_milestone_alerts()

        assert result == 0

    def test_check_with_upcoming_milestones(self):
        """有即将到期里程碑时生成告警"""
        svc, db = make_service()
        mock_ms = MagicMock()

        with patch.object(svc, "_get_upcoming_milestones", return_value=[mock_ms]), \
             patch.object(svc, "_get_overdue_milestones", return_value=[]), \
             patch.object(svc, "_get_or_create_warning_rule", return_value=MagicMock()), \
             patch.object(svc, "_get_or_create_critical_rule", return_value=MagicMock()), \
             patch.object(svc, "_process_upcoming_milestones", return_value=1), \
             patch.object(svc, "_process_overdue_milestones", return_value=0):
            result = svc.check_milestone_alerts()

        assert result == 1

    def test_check_with_overdue_milestones(self):
        """有逾期里程碑时生成告警"""
        svc, db = make_service()
        mock_ms = MagicMock()

        with patch.object(svc, "_get_upcoming_milestones", return_value=[]), \
             patch.object(svc, "_get_overdue_milestones", return_value=[mock_ms]), \
             patch.object(svc, "_get_or_create_warning_rule", return_value=MagicMock()), \
             patch.object(svc, "_get_or_create_critical_rule", return_value=MagicMock()), \
             patch.object(svc, "_process_upcoming_milestones", return_value=0), \
             patch.object(svc, "_process_overdue_milestones", return_value=2):
            result = svc.check_milestone_alerts()

        assert result == 2

    def test_check_raises_on_error(self):
        """出现异常时重新抛出"""
        svc, db = make_service()

        with patch.object(svc, "_get_upcoming_milestones", side_effect=Exception("DB错误")):
            with pytest.raises(Exception, match="DB错误"):
                svc.check_milestone_alerts()
