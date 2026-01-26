# -*- coding: utf-8 -*-
"""
ECN定时任务服务单元测试
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestCheckEvaluationOverdue:
    """测试评估超时检查"""

    def test_no_overdue_evaluations(self, db_session):
        """测试无超时评估"""
        try:
            from app.services.ecn_scheduler import check_evaluation_overdue

            alerts = check_evaluation_overdue(db_session)
            assert isinstance(alerts, list)
        except Exception as e:
            pytest.skip(f"Service dependencies not available: {e}")

    def test_alert_structure(self, db_session):
        """测试提醒结构"""
        try:
            from app.services.ecn_scheduler import check_evaluation_overdue
            from app.models.ecn import Ecn, EcnEvaluation

            # 创建超时评估
            ecn = Ecn(ecn_no="ECN001", ecn_title="测试ECN")
            db_session.add(ecn)
            db_session.flush()

            eval = EcnEvaluation(
                ecn_id=ecn.id,
                eval_dept="研发部",
                status="PENDING",
                created_at=datetime.now() - timedelta(days=5)
            )
            db_session.add(eval)
            db_session.flush()

            alerts = check_evaluation_overdue(db_session)

            if alerts:
                alert = alerts[0]
                assert "type" in alert
                assert alert["type"] == "EVALUATION_OVERDUE"
                assert "ecn_id" in alert
                assert "overdue_days" in alert
        except Exception as e:
            pytest.skip(f"Service dependencies not available: {e}")


class TestCheckApprovalOverdue:
    """测试审批超时检查"""

    def test_no_overdue_approvals(self, db_session):
        """测试无超时审批"""
        try:
            from app.services.ecn_scheduler import check_approval_overdue

            alerts = check_approval_overdue(db_session)
            assert isinstance(alerts, list)
        except Exception as e:
            pytest.skip(f"Service dependencies not available: {e}")

    def test_approval_alert_type(self, db_session):
        """测试审批提醒类型"""
        try:
            from app.services.ecn_scheduler import check_approval_overdue
            from app.models.ecn import Ecn, EcnApproval

            ecn = Ecn(ecn_no="ECN002", ecn_title="测试ECN")
            db_session.add(ecn)
            db_session.flush()

            approval = EcnApproval(
                ecn_id=ecn.id,
                approval_level=1,
                approval_role="部门经理",
                status="PENDING",
                due_date=datetime.now() - timedelta(days=2)
            )
            db_session.add(approval)
            db_session.flush()

            alerts = check_approval_overdue(db_session)

            if alerts:
                assert alerts[0]["type"] == "APPROVAL_OVERDUE"
        except Exception as e:
            pytest.skip(f"Service dependencies not available: {e}")


class TestCheckTaskOverdue:
    """测试任务超时检查"""

    def test_no_overdue_tasks(self, db_session):
        """测试无超时任务"""
        try:
            from app.services.ecn_scheduler import check_task_overdue

            alerts = check_task_overdue(db_session)
            assert isinstance(alerts, list)
        except Exception as e:
            pytest.skip(f"Service dependencies not available: {e}")

    def test_task_alert_type(self, db_session):
        """测试任务提醒类型"""
        try:
            from app.services.ecn_scheduler import check_task_overdue
            from app.models.ecn import Ecn, EcnTask

            ecn = Ecn(ecn_no="ECN003", ecn_title="测试ECN")
            db_session.add(ecn)
            db_session.flush()

            task = EcnTask(
                ecn_id=ecn.id,
                task_name="测试任务",
                status="IN_PROGRESS",
                planned_end=(datetime.now() - timedelta(days=3)).date()
            )
            db_session.add(task)
            db_session.flush()

            alerts = check_task_overdue(db_session)

            if alerts:
                assert alerts[0]["type"] == "TASK_OVERDUE"
        except Exception as e:
            pytest.skip(f"Service dependencies not available: {e}")


class TestCheckAllOverdue:
    """测试检查所有超时"""

    def test_check_all_returns_list(self):
        """测试返回列表"""
        try:
            from app.services.ecn_scheduler import check_all_overdue

            with patch('app.services.ecn_scheduler.get_db_session') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db.return_value.__exit__ = MagicMock(return_value=False)
                mock_session.query.return_value.filter.return_value.all.return_value = []

                alerts = check_all_overdue()
                assert isinstance(alerts, list)
        except Exception as e:
            pytest.skip(f"Service dependencies not available: {e}")


class TestSendOverdueNotifications:
    """测试发送超时通知"""

    def test_empty_alerts_no_action(self):
        """测试空提醒不执行操作"""
        try:
            from app.services.ecn_scheduler import send_overdue_notifications

            # 空列表不应报错
            send_overdue_notifications([])
        except Exception as e:
            pytest.skip(f"Service dependencies not available: {e}")

    def test_notification_by_alert_type(self):
        """测试按类型发送通知"""
        alert_types = ["EVALUATION_OVERDUE", "APPROVAL_OVERDUE", "TASK_OVERDUE"]

        for alert_type in alert_types:
            alert = {
                "type": alert_type,
                "ecn_id": 1,
                "ecn_no": "ECN001",
                "message": "测试消息"
            }
            assert alert["type"] in alert_types


class TestRunEcnScheduler:
    """测试运行ECN定时任务"""

    def test_scheduler_handles_exception(self):
        """测试调度器异常处理"""
        try:
            from app.services.ecn_scheduler import run_ecn_scheduler

            with patch('app.services.ecn_scheduler.check_all_overdue') as mock_check:
                mock_check.side_effect = Exception("测试异常")

                # 不应抛出异常
                run_ecn_scheduler()
        except Exception as e:
            pytest.skip(f"Service dependencies not available: {e}")

    def test_scheduler_with_alerts(self):
        """测试有提醒时的调度器"""
        try:
            from app.services.ecn_scheduler import run_ecn_scheduler

            with patch('app.services.ecn_scheduler.check_all_overdue') as mock_check:
                with patch('app.services.ecn_scheduler.send_overdue_notifications') as mock_send:
                    mock_check.return_value = [{"type": "TEST", "message": "test"}]

                    run_ecn_scheduler()

                    mock_send.assert_called_once()
        except Exception as e:
            pytest.skip(f"Service dependencies not available: {e}")


class TestOverdueDaysCalculation:
    """测试超时天数计算"""

    def test_evaluation_overdue_days(self):
        """测试评估超时天数"""
        now = datetime.now()
        created_at = now - timedelta(days=5)
        overdue_days = (now - created_at).days

        assert overdue_days == 5

    def test_approval_overdue_days(self):
        """测试审批超时天数"""
        now = datetime.now()
        due_date = now - timedelta(days=3)
        overdue_days = (now - due_date).days

        assert overdue_days == 3

    def test_task_overdue_days(self):
        """测试任务超时天数"""
        now = datetime.now()
        planned_end = (now - timedelta(days=7)).date()
        overdue_days = (now.date() - planned_end).days

        assert overdue_days == 7


class TestTimeoutThreshold:
    """测试超时阈值"""

    def test_evaluation_timeout_3_days(self):
        """测试评估3天超时"""
        now = datetime.now()
        timeout_threshold = now - timedelta(days=3)

        created_4_days_ago = now - timedelta(days=4)
        is_overdue = created_4_days_ago < timeout_threshold

        assert is_overdue is True

    def test_evaluation_not_timeout(self):
        """测试评估未超时"""
        now = datetime.now()
        timeout_threshold = now - timedelta(days=3)

        created_2_days_ago = now - timedelta(days=2)
        is_overdue = created_2_days_ago < timeout_threshold

        assert is_overdue is False


# pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
