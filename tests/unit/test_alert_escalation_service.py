# -*- coding: utf-8 -*-
"""
预警升级服务单元测试

测试覆盖:
- AlertEscalationService: 预警升级服务
- check_and_escalate: 批量检查和升级
- _should_escalate: 超时判断逻辑
- _escalate_alert: 执行升级操作
- _send_escalation_notification: 发送升级通知
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.alert_escalation_service import AlertEscalationService


@pytest.mark.unit
class TestAlertEscalationServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self, db_session: Session):
        """测试使用数据库会话初始化"""
        service = AlertEscalationService(db=db_session)
        assert service.db == db_session

    def test_escalation_path_defined(self):
        """测试升级路径已定义"""
        assert AlertEscalationService.ESCALATION_PATH is not None
        assert 'INFO' in AlertEscalationService.ESCALATION_PATH
        assert 'WARN' in AlertEscalationService.ESCALATION_PATH
        assert 'HIGH' in AlertEscalationService.ESCALATION_PATH
        assert AlertEscalationService.ESCALATION_PATH['INFO'] == 'WARN'
        assert AlertEscalationService.ESCALATION_PATH['WARN'] == 'HIGH'
        assert AlertEscalationService.ESCALATION_PATH['HIGH'] == 'CRITICAL'

    def test_escalation_timeout_defined(self):
        """测试超时时间已定义"""
        assert AlertEscalationService.ESCALATION_TIMEOUT is not None
        assert AlertEscalationService.ESCALATION_TIMEOUT['INFO'] == 48
        assert AlertEscalationService.ESCALATION_TIMEOUT['WARN'] == 24
        assert AlertEscalationService.ESCALATION_TIMEOUT['HIGH'] == 12
        assert AlertEscalationService.ESCALATION_TIMEOUT['CRITICAL'] == 6


@pytest.mark.unit
class TestShouldEscalate:
    """测试 _should_escalate 方法"""

    def test_no_triggered_at_returns_false(self, db_session: Session):
        """没有触发时间返回 False"""
        service = AlertEscalationService(db=db_session)

        mock_alert = MagicMock()
        mock_alert.triggered_at = None
        mock_alert.alert_level = 'WARN'

        result = service._should_escalate(mock_alert)
        assert result is False

    def test_not_expired_returns_false(self, db_session: Session):
        """未超时返回 False"""
        service = AlertEscalationService(db=db_session)

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime.now() - timedelta(hours=1)  # 1小时前
        mock_alert.alert_level = 'WARN'  # 24小时超时

        result = service._should_escalate(mock_alert)
        assert result is False

    def test_expired_info_level_returns_true(self, db_session: Session):
        """INFO级别超时返回 True"""
        service = AlertEscalationService(db=db_session)

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime.now() - timedelta(hours=50)  # 50小时前
        mock_alert.alert_level = 'INFO'  # 48小时超时

        result = service._should_escalate(mock_alert)
        assert result is True

    def test_expired_warn_level_returns_true(self, db_session: Session):
        """WARN级别超时返回 True"""
        service = AlertEscalationService(db=db_session)

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime.now() - timedelta(hours=25)  # 25小时前
        mock_alert.alert_level = 'WARN'  # 24小时超时

        result = service._should_escalate(mock_alert)
        assert result is True

    def test_expired_high_level_returns_true(self, db_session: Session):
        """HIGH级别超时返回 True"""
        service = AlertEscalationService(db=db_session)

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime.now() - timedelta(hours=13)  # 13小时前
        mock_alert.alert_level = 'HIGH'  # 12小时超时

        result = service._should_escalate(mock_alert)
        assert result is True

    def test_default_timeout_for_unknown_level(self, db_session: Session):
        """未知级别使用默认超时（24小时）"""
        service = AlertEscalationService(db=db_session)

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime.now() - timedelta(hours=25)  # 25小时前
        mock_alert.alert_level = 'UNKNOWN'  # 未知级别，默认24小时

        result = service._should_escalate(mock_alert)
        assert result is True

    def test_none_alert_level_uses_medium_default(self, db_session: Session):
        """空级别使用 MEDIUM 默认值"""
        service = AlertEscalationService(db=db_session)

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime.now() - timedelta(hours=25)
        mock_alert.alert_level = None  # 默认使用 MEDIUM (24小时)

        result = service._should_escalate(mock_alert)
        assert result is True


@pytest.mark.unit
class TestEscalateAlert:
    """测试 _escalate_alert 方法"""

    def test_escalate_info_to_warn(self):
        """INFO 升级到 WARN"""
        mock_session = MagicMock(spec=Session)
        service = AlertEscalationService(db=mock_session)

        # 创建一个简单的类来模拟 alert
        class MockAlert:
            def __init__(self):
                self.alert_level = 'INFO'
                self.alert_no = 'ALT-001'
                self.alert_title = '测试预警'
                self.alert_content = '测试内容'
                self.alert_data = None
                self.id = 1

        mock_alert = MockAlert()

        with patch.object(service, '_send_escalation_notification'):
            service._escalate_alert(mock_alert)

        assert mock_alert.alert_level == 'WARN'

    def test_escalate_warn_to_high(self):
        """WARN 升级到 HIGH"""
        mock_session = MagicMock(spec=Session)
        service = AlertEscalationService(db=mock_session)

        class MockAlert:
            def __init__(self):
                self.alert_level = 'WARN'
                self.alert_no = 'ALT-002'
                self.alert_title = '测试预警'
                self.alert_content = '测试内容'
                self.alert_data = None
                self.id = 2

        mock_alert = MockAlert()

        with patch.object(service, '_send_escalation_notification'):
            service._escalate_alert(mock_alert)

        assert mock_alert.alert_level == 'HIGH'

    def test_escalate_high_to_critical(self):
        """HIGH 升级到 CRITICAL"""
        mock_session = MagicMock(spec=Session)
        service = AlertEscalationService(db=mock_session)

        class MockAlert:
            def __init__(self):
                self.alert_level = 'HIGH'
                self.alert_no = 'ALT-003'
                self.alert_title = '测试预警'
                self.alert_content = '测试内容'
                self.alert_data = None
                self.id = 3

        mock_alert = MockAlert()

        with patch.object(service, '_send_escalation_notification'):
            service._escalate_alert(mock_alert)

        assert mock_alert.alert_level == 'CRITICAL'

    def test_no_escalation_for_unknown_level(self):
        """未知级别不升级"""
        mock_session = MagicMock(spec=Session)
        service = AlertEscalationService(db=mock_session)

        class MockAlert:
            def __init__(self):
                self.alert_level = 'UNKNOWN_LEVEL'
                self.alert_no = 'ALT-004'
                self.alert_data = None

        mock_alert = MockAlert()

        with patch.object(service, '_send_escalation_notification') as mock_notify:
            service._escalate_alert(mock_alert)
            mock_notify.assert_not_called()

        # 级别应保持不变
        assert mock_alert.alert_level == 'UNKNOWN_LEVEL'

    def test_escalation_history_added(self):
        """升级历史记录被添加"""
        mock_session = MagicMock(spec=Session)
        service = AlertEscalationService(db=mock_session)

        class MockAlert:
            def __init__(self):
                self.alert_level = 'INFO'
                self.alert_no = 'ALT-005'
                self.alert_title = '测试预警'
                self.alert_content = '测试内容'
                self.alert_data = None
                self.id = 5

        mock_alert = MockAlert()

        with patch.object(service, '_send_escalation_notification'):
            service._escalate_alert(mock_alert)

        # 检查 alert_data 被设置
        assert mock_alert.alert_data is not None
        alert_data = json.loads(mock_alert.alert_data)
        assert 'escalation_history' in alert_data
        assert len(alert_data['escalation_history']) == 1
        assert alert_data['escalation_history'][0]['from_level'] == 'INFO'
        assert alert_data['escalation_history'][0]['to_level'] == 'WARN'
        assert alert_data['escalation_history'][0]['reason'] == '超时自动升级'

    def test_existing_alert_data_preserved(self):
        """现有 alert_data 被保留"""
        mock_session = MagicMock(spec=Session)
        service = AlertEscalationService(db=mock_session)

        existing_data = {'custom_field': 'custom_value'}

        class MockAlert:
            def __init__(self):
                self.alert_level = 'WARN'
                self.alert_no = 'ALT-006'
                self.alert_title = '测试预警'
                self.alert_content = '测试内容'
                self.alert_data = json.dumps(existing_data)
                self.id = 6

        mock_alert = MockAlert()

        with patch.object(service, '_send_escalation_notification'):
            service._escalate_alert(mock_alert)

        alert_data = json.loads(mock_alert.alert_data)
        assert alert_data['custom_field'] == 'custom_value'
        assert 'escalation_history' in alert_data

    def test_multiple_escalations_tracked(self):
        """多次升级被追踪"""
        mock_session = MagicMock(spec=Session)
        service = AlertEscalationService(db=mock_session)

        existing_history = {
            'escalation_history': [
                {'from_level': 'LOW', 'to_level': 'MEDIUM', 'escalated_at': '2025-01-01T00:00:00'}
            ]
        }

        class MockAlert:
            def __init__(self):
                self.alert_level = 'MEDIUM'
                self.alert_no = 'ALT-007'
                self.alert_title = '测试预警'
                self.alert_content = '测试内容'
                self.alert_data = json.dumps(existing_history)
                self.id = 7

        mock_alert = MockAlert()

        with patch.object(service, '_send_escalation_notification'):
            service._escalate_alert(mock_alert)

        alert_data = json.loads(mock_alert.alert_data)
        assert len(alert_data['escalation_history']) == 2


@pytest.mark.unit
class TestSendEscalationNotification:
    """测试 _send_escalation_notification 方法"""

    def test_notification_created(self):
        """通知被创建"""
        mock_session = MagicMock(spec=Session)
        service = AlertEscalationService(db=mock_session)

        mock_alert = MagicMock()
        mock_alert.alert_title = '测试预警标题'
        mock_alert.alert_content = '这是测试预警内容' * 20  # 长内容
        mock_alert.id = 1

        service._send_escalation_notification(mock_alert, 'WARN', 'HIGH')

        # 检查 db.add 被调用
        mock_session.add.assert_called()

    def test_critical_priority_notification(self):
        """CRITICAL级别创建高优先级通知"""
        mock_session = MagicMock(spec=Session)
        service = AlertEscalationService(db=mock_session)

        mock_alert = MagicMock()
        mock_alert.alert_title = '紧急预警'
        mock_alert.alert_content = '紧急内容'
        mock_alert.id = 2

        service._send_escalation_notification(mock_alert, 'HIGH', 'CRITICAL')

        # 验证 add 被调用
        call_args = mock_session.add.call_args
        notification = call_args[0][0]
        assert notification.priority == 'high'

    def test_normal_priority_notification(self):
        """非CRITICAL级别创建普通优先级通知"""
        mock_session = MagicMock(spec=Session)
        service = AlertEscalationService(db=mock_session)

        mock_alert = MagicMock()
        mock_alert.alert_title = '普通预警'
        mock_alert.alert_content = '普通内容'
        mock_alert.id = 3

        service._send_escalation_notification(mock_alert, 'INFO', 'WARN')

        call_args = mock_session.add.call_args
        notification = call_args[0][0]
        assert notification.priority == 'normal'

    def test_notification_error_handled(self):
        """通知创建错误被处理"""
        mock_session = MagicMock(spec=Session)
        mock_session.add.side_effect = Exception("DB Error")
        service = AlertEscalationService(db=mock_session)

        mock_alert = MagicMock()
        mock_alert.alert_title = '测试预警'
        mock_alert.alert_content = '测试内容'
        mock_alert.id = 4

        # 不应抛出异常
        service._send_escalation_notification(mock_alert, 'INFO', 'WARN')


@pytest.mark.unit
class TestCheckAndEscalate:
    """测试 check_and_escalate 方法"""

    def test_no_pending_alerts(self, db_session: Session):
        """没有待处理预警"""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        service = AlertEscalationService(db=mock_session)
        result = service.check_and_escalate()

        assert result['checked'] == 0
        assert result['escalated'] == 0
        assert result['errors'] == []

    def test_alerts_checked_but_not_escalated(self, db_session: Session):
        """预警被检查但未升级（未超时）"""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime.now()  # 刚触发，未超时
        mock_alert.alert_level = 'INFO'
        mock_alert.id = 1

        mock_query.all.return_value = [mock_alert]

        service = AlertEscalationService(db=mock_session)
        result = service.check_and_escalate()

        assert result['checked'] == 1
        assert result['escalated'] == 0
        assert result['errors'] == []

    def test_alerts_escalated(self, db_session: Session):
        """预警被升级"""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime.now() - timedelta(hours=50)  # 超时
        mock_alert.alert_level = 'INFO'
        mock_alert.alert_no = 'ALT-001'
        mock_alert.alert_title = '测试'
        mock_alert.alert_content = '测试内容'
        mock_alert.alert_data = None
        mock_alert.id = 1

        mock_query.all.return_value = [mock_alert]

        service = AlertEscalationService(db=mock_session)
        result = service.check_and_escalate()

        assert result['checked'] == 1
        assert result['escalated'] == 1
        assert result['errors'] == []
        mock_session.commit.assert_called_once()

    def test_multiple_alerts_partial_escalation(self, db_session: Session):
        """多个预警部分升级"""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # 一个超时，一个未超时
        mock_alert1 = MagicMock()
        mock_alert1.triggered_at = datetime.now() - timedelta(hours=50)
        mock_alert1.alert_level = 'INFO'
        mock_alert1.alert_no = 'ALT-001'
        mock_alert1.alert_title = '测试1'
        mock_alert1.alert_content = '测试内容1'
        mock_alert1.alert_data = None
        mock_alert1.id = 1

        mock_alert2 = MagicMock()
        mock_alert2.triggered_at = datetime.now()  # 未超时
        mock_alert2.alert_level = 'WARN'
        mock_alert2.id = 2

        mock_query.all.return_value = [mock_alert1, mock_alert2]

        service = AlertEscalationService(db=mock_session)
        result = service.check_and_escalate()

        assert result['checked'] == 2
        assert result['escalated'] == 1
        assert result['errors'] == []

    def test_escalation_error_captured(self, db_session: Session):
        """升级错误被捕获"""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime.now() - timedelta(hours=50)
        mock_alert.alert_level = 'INFO'
        mock_alert.id = 1
        # 使 alert_data 访问抛出异常
        type(mock_alert).alert_data = property(
            lambda self: (_ for _ in ()).throw(Exception("Test error"))
        )

        mock_query.all.return_value = [mock_alert]

        service = AlertEscalationService(db=mock_session)
        result = service.check_and_escalate()

        assert result['checked'] == 1
        assert result['escalated'] == 0
        assert len(result['errors']) == 1
        assert result['errors'][0]['alert_id'] == 1

    def test_query_error_handled(self, db_session: Session):
        """查询错误被处理"""
        mock_session = MagicMock(spec=Session)
        mock_session.query.side_effect = Exception("DB Query Error")

        service = AlertEscalationService(db=mock_session)
        result = service.check_and_escalate()

        assert result['checked'] == 0
        assert result['escalated'] == 0
        assert len(result['errors']) == 1
        assert 'DB Query Error' in result['errors'][0]['error']
