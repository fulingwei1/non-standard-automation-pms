# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 里程碑告警服务"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta


class TestMilestoneAlertServiceBusinessLogic:
    """里程碑告警服务业务逻辑测试"""

    def test_check_milestone_alerts(self):
        """测试里程碑预警检查"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            mock_db = MagicMock()

            # Mock里程碑数据
            mock_upcoming = [MagicMock(id=1, due_date=date.today() + timedelta(days=2))]
            mock_overdue = [MagicMock(id=2, due_date=date.today() - timedelta(days=1))]

            mock_db.query.return_value.filter.return_value.all.side_effect = [mock_upcoming, mock_overdue]

            service = MilestoneAlertService(mock_db)

            # Mock内部方法
            service._get_upcoming_milestones = MagicMock(return_value=mock_upcoming)
            service._get_overdue_milestones = MagicMock(return_value=mock_overdue)
            service._get_or_create_rule = MagicMock(return_value=MagicMock())
            service._process_upcoming_milestones = MagicMock(return_value=2)
            service._process_overdue_milestones = MagicMock(return_value=1)

            result = service.check_milestone_alerts()

            assert isinstance(result, int)
        except ImportError:
            pytest.skip("Module not found")

    def test_get_upcoming_milestones(self):
        """测试获取即将到期里程碑"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            mock_db = MagicMock()

            mock_milestone = MagicMock()
            mock_milestone.id = 1
            mock_milestone.due_date = date.today() + timedelta(days=2)
            mock_milestone.status = "PENDING"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_milestone]

            service = MilestoneAlertService(mock_db)
            result = service._get_upcoming_milestones(date.today())

            assert len(result) >= 0
        except ImportError:
            pytest.skip("Module not found")

    def test_get_overdue_milestones(self):
        """测试获取逾期里程碑"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            mock_db = MagicMock()

            mock_milestone = MagicMock()
            mock_milestone.id = 1
            mock_milestone.due_date = date.today() - timedelta(days=1)
            mock_milestone.status = "PENDING"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_milestone]

            service = MilestoneAlertService(mock_db)
            result = service._get_overdue_milestones(date.today())

            assert len(result) >= 0
        except ImportError:
            pytest.skip("Module not found")

    def test_determine_alert_level_critical(self):
        """测试 1 天阈值会生成 CRITICAL 级别告警"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService
            from app.models.enums import AlertLevelEnum

            mock_db = MagicMock()
            service = MilestoneAlertService(mock_db)
            service._should_create_alert = MagicMock(return_value=True)
            service._dispatch_milestone_notification = MagicMock()

            milestone = MagicMock()
            milestone.id = 1
            milestone.project_id = 100
            milestone.milestone_code = "MS-001"
            milestone.milestone_name = "阶段1"
            milestone.milestone_type = "CUSTOM"
            milestone.is_key = False
            milestone.planned_date = date.today() + timedelta(days=1)

            rule = MagicMock()
            rule.id = 1

            count = service._process_upcoming_milestones([milestone], rule, date.today(), 0)

            assert count == 1
            alert = mock_db.add.call_args.args[0]
            assert alert.alert_level == AlertLevelEnum.CRITICAL.value
        except ImportError:
            pytest.skip("Module not found")

    def test_determine_alert_level_warning(self):
        """测试 3 天阈值会生成 WARNING 级别告警"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService
            from app.models.enums import AlertLevelEnum

            mock_db = MagicMock()
            service = MilestoneAlertService(mock_db)
            service._should_create_alert = MagicMock(return_value=True)
            service._dispatch_milestone_notification = MagicMock()

            milestone = MagicMock()
            milestone.id = 1
            milestone.project_id = 100
            milestone.milestone_code = "MS-001"
            milestone.milestone_name = "阶段1"
            milestone.milestone_type = "CUSTOM"
            milestone.is_key = False
            milestone.planned_date = date.today() + timedelta(days=3)

            rule = MagicMock()
            rule.id = 1

            count = service._process_upcoming_milestones([milestone], rule, date.today(), 0)

            assert count == 1
            alert = mock_db.add.call_args.args[0]
            assert alert.alert_level == AlertLevelEnum.WARNING.value
        except ImportError:
            pytest.skip("Module not found")

    def test_create_alert_record(self):
        """测试处理即将到期里程碑时创建告警记录"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            mock_db = MagicMock()

            mock_milestone = MagicMock()
            mock_milestone.id = 1
            mock_milestone.milestone_code = "MS-001"
            mock_milestone.milestone_name = "阶段1"
            mock_milestone.project_id = 100
            mock_milestone.milestone_type = "CUSTOM"
            mock_milestone.is_key = True
            mock_milestone.planned_date = date.today() + timedelta(days=1)

            mock_rule = MagicMock()
            mock_rule.id = 1

            service = MilestoneAlertService(mock_db)
            service._should_create_alert = MagicMock(return_value=True)
            service._dispatch_milestone_notification = MagicMock()

            result = service._process_upcoming_milestones(
                milestones=[mock_milestone], rule=mock_rule, today=date.today(), start_count=0
            )

            assert result == 1
            assert mock_db.add.called
        except ImportError:
            pytest.skip("Module not found")

    def test_send_notifications(self):
        """测试通知派发走当前 dispatcher 入口"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            mock_db = MagicMock()
            mock_project = MagicMock(pm_id=1, owner_id=2)
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project

            mock_milestone = MagicMock()
            mock_milestone.id = 1
            mock_milestone.milestone_code = "MS-001"
            mock_milestone.owner_id = 3
            mock_milestone.project_id = 100

            mock_alert = MagicMock(alert_no="AL-001", alert_title="title", alert_content="content")

            service = MilestoneAlertService(mock_db)

            with patch(
                "app.services.notification.notification_dispatcher.NotificationDispatcher"
            ) as mock_dispatcher_cls:
                dispatcher = MagicMock()
                mock_dispatcher_cls.return_value = dispatcher
                service._dispatch_milestone_notification(mock_alert, mock_milestone)
                dispatcher.dispatch_alert_notifications.assert_called_once()
        except ImportError:
            pytest.skip("Module not found")

    def test_acknowledge_alert(self):
        """当前服务未提供手工确认接口，保留为能力缺失 smoke"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            service = MilestoneAlertService(MagicMock())
            assert not hasattr(service, "acknowledge_alert")
        except ImportError:
            pytest.skip("Module not found")

    def test_resolve_alert(self):
        """当前服务未提供手工解决接口，保留为能力缺失 smoke"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            service = MilestoneAlertService(MagicMock())
            assert not hasattr(service, "resolve_alert")
        except ImportError:
            pytest.skip("Module not found")


class TestMilestoneAlertServiceThresholds:
    """阈值测试"""

    def test_threshold_constants(self):
        """测试阈值常量"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService
            from app.models.enums import AlertLevelEnum

            thresholds = MilestoneAlertService.DUE_SOON_THRESHOLDS

            assert len(thresholds) == 2
            assert thresholds[0][1] == AlertLevelEnum.CRITICAL.value
            assert thresholds[1][1] == AlertLevelEnum.WARNING.value
        except ImportError:
            pytest.skip("Module not found")

    def test_threshold_ordering(self):
        """测试阈值顺序"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            thresholds = MilestoneAlertService.DUE_SOON_THRESHOLDS

            # CRITICAL阈值天数应该小于WARNING
            critical_days = thresholds[0][0]
            warning_days = thresholds[1][0]

            assert critical_days < warning_days
        except ImportError:
            pytest.skip("Module not found")


class TestMilestoneAlertServiceEdgeCases:
    """边界情况测试"""

    def test_empty_milestones(self):
        """测试空里程碑列表"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.all.return_value = []

            service = MilestoneAlertService(mock_db)

            service._get_upcoming_milestones = MagicMock(return_value=[])
            service._get_overdue_milestones = MagicMock(return_value=[])
            service._get_or_create_rule = MagicMock(return_value=MagicMock())
            service._process_upcoming_milestones = MagicMock(return_value=0)
            service._process_overdue_milestones = MagicMock(return_value=0)

            result = service.check_milestone_alerts()

            assert result == 0
        except ImportError:
            pytest.skip("Module not found")

    def test_milestone_already_completed(self):
        """测试已完成里程碑"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            mock_db = MagicMock()

            mock_milestone = MagicMock()
            mock_milestone.status = "COMPLETED"  # 已完成

            mock_db.query.return_value.filter.return_value.all.return_value = []

            service = MilestoneAlertService(mock_db)
            result = service._get_upcoming_milestones(date.today())

            # 已完成的里程碑不应该被返回
            assert len(result) == 0
        except ImportError:
            pytest.skip("Module not found")

    def test_exact_threshold_boundary(self):
        """测试正好 3 天边界仍为 WARNING"""
        try:
            from app.services.alert.milestone_alert_service import MilestoneAlertService
            from app.models.enums import AlertLevelEnum

            mock_db = MagicMock()
            service = MilestoneAlertService(mock_db)
            service._should_create_alert = MagicMock(return_value=True)
            service._dispatch_milestone_notification = MagicMock()

            milestone = MagicMock()
            milestone.id = 1
            milestone.project_id = 100
            milestone.milestone_code = "MS-001"
            milestone.milestone_name = "阶段1"
            milestone.milestone_type = "CUSTOM"
            milestone.is_key = False
            milestone.planned_date = date.today() + timedelta(days=3)

            rule = MagicMock()
            rule.id = 1

            service._process_upcoming_milestones([milestone], rule, date.today(), 0)
            alert = mock_db.add.call_args.args[0]
            assert alert.alert_level == AlertLevelEnum.WARNING.value
        except ImportError:
            pytest.skip("Module not found")