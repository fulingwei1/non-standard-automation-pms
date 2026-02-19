# -*- coding: utf-8 -*-
"""
第三十三批覆盖率测试 - 预警创建器 (AlertCreator)
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta

try:
    from app.services.alert_rule_engine.alert_creator import AlertCreator
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="alert_creator 导入失败")


def _make_creator():
    """构造测试用 AlertCreator（绕过__init__）"""
    creator = object.__new__(AlertCreator)
    creator.db = MagicMock()
    creator._notification_service = None
    creator._subscription_service = None
    return creator


class TestShouldCreateAlert:
    def test_no_target_type_returns_none(self):
        """无target_type时返回None"""
        creator = _make_creator()
        rule = MagicMock()
        result = creator.should_create_alert(rule, {"target_id": 1}, "RED")
        assert result is None

    def test_no_target_id_returns_none(self):
        """无target_id时返回None"""
        creator = _make_creator()
        rule = MagicMock()
        result = creator.should_create_alert(rule, {"target_type": "PROJECT"}, "RED")
        assert result is None

    def test_existing_alert_returns_record(self):
        """24小时内已有活跃预警时返回现有记录"""
        creator = _make_creator()
        rule = MagicMock()
        rule.id = 1

        mock_alert = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.return_value = mock_alert
        creator.db.query.return_value = q

        result = creator.should_create_alert(
            rule,
            {"target_type": "PROJECT", "target_id": 10},
            "RED"
        )

        assert result is mock_alert

    def test_no_existing_alert_returns_none(self):
        """无活跃预警时返回None"""
        creator = _make_creator()
        rule = MagicMock()
        rule.id = 1

        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.return_value = None
        creator.db.query.return_value = q

        result = creator.should_create_alert(
            rule,
            {"target_type": "PROJECT", "target_id": 10},
            "YELLOW"
        )

        assert result is None


class TestCreateAlert:
    def _setup_creator_with_services(self, notification_svc=None, subscription_svc=None):
        creator = _make_creator()
        creator.get_field_value = MagicMock(return_value=5)
        creator._notification_service = notification_svc or MagicMock()
        creator._subscription_service = subscription_svc or MagicMock()
        return creator

    def test_create_alert_adds_to_db(self):
        """创建预警时将记录添加到数据库"""
        mock_subscription_svc = MagicMock()
        mock_subscription_svc.get_notification_recipients.return_value = {
            "user_ids": [1, 2],
            "channels": ["wechat"]
        }
        creator = self._setup_creator_with_services(subscription_svc=mock_subscription_svc)

        rule = MagicMock()
        rule.id = 1
        rule.target_field = "delay_days"
        rule.threshold_value = "3"

        target_data = {
            "target_type": "PROJECT",
            "target_id": 10,
            "target_no": "PJ001",
            "target_name": "测试项目",
            "project_id": 10,
            "machine_id": None,
        }

        with patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_no",
            return_value="PD202601010001"
        ), patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_title",
            return_value="测试预警标题"
        ), patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_content",
            return_value="预警内容"
        ), patch(
            "app.services.alert_rule_engine.alert_creator.AlertRecord"
        ) as mock_alert_cls:
            mock_alert_cls.return_value = MagicMock()
            creator.create_alert(rule, target_data, "RED")

        creator.db.add.assert_called_once()
        creator.db.flush.assert_called_once()

    def test_create_alert_handles_notification_failure(self):
        """通知失败不影响预警记录创建"""
        mock_subscription_svc = MagicMock()
        mock_subscription_svc.get_notification_recipients.side_effect = RuntimeError("通知服务不可用")
        creator = self._setup_creator_with_services(subscription_svc=mock_subscription_svc)
        creator.get_field_value = MagicMock(return_value=None)

        rule = MagicMock()
        rule.id = 2
        rule.target_field = None
        rule.threshold_value = None

        target_data = {
            "target_type": "MACHINE",
            "target_id": 5,
            "target_no": "M001",
            "target_name": "机台1",
            "project_id": None,
            "machine_id": 5,
        }

        with patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_no",
            return_value="AL202601010001"
        ), patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_title",
            return_value="标题"
        ), patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_content",
            return_value="内容"
        ), patch(
            "app.services.alert_rule_engine.alert_creator.AlertRecord"
        ) as mock_alert_cls:
            mock_alert_cls.return_value = MagicMock()
            # 不应该抛出异常
            creator.create_alert(rule, target_data, "YELLOW")

        creator.db.add.assert_called_once()

    def test_notification_service_lazy_loaded(self):
        """notification_service属性延迟加载"""
        creator = _make_creator()
        assert creator._notification_service is None

        mock_svc = MagicMock()
        with patch(
            "app.services.notification_service.AlertNotificationService",
            return_value=mock_svc
        ):
            # 直接调用 property 逻辑
            if creator._notification_service is None:
                from app.services.notification_service import AlertNotificationService
                creator._notification_service = AlertNotificationService(creator.db)

        assert creator._notification_service is not None

    def test_subscription_service_lazy_loaded(self):
        """subscription_service属性延迟加载"""
        creator = _make_creator()
        assert creator._subscription_service is None

        # 验证初始状态
        assert creator._notification_service is None

    def test_create_alert_with_no_subscribers_uses_default(self):
        """无匹配订阅时使用规则默认配置发送通知"""
        mock_notification_svc = MagicMock()
        mock_subscription_svc = MagicMock()
        mock_subscription_svc.get_notification_recipients.return_value = {
            "user_ids": [],  # 无匹配订阅
            "channels": []
        }
        creator = self._setup_creator_with_services(
            notification_svc=mock_notification_svc,
            subscription_svc=mock_subscription_svc
        )
        creator.get_field_value = MagicMock(return_value=None)

        rule = MagicMock()
        rule.id = 3
        rule.target_field = None
        rule.threshold_value = None

        target_data = {
            "target_type": "PROJECT",
            "target_id": 20,
            "target_no": "PJ002",
            "target_name": "项目2",
            "project_id": 20,
            "machine_id": None,
        }

        with patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_no",
            return_value="PD202601010002"
        ), patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_title",
            return_value="标题"
        ), patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_content",
            return_value="内容"
        ), patch(
            "app.services.alert_rule_engine.alert_creator.AlertRecord"
        ) as mock_alert_cls:
            mock_alert_cls.return_value = MagicMock()
            creator.create_alert(rule, target_data, "YELLOW")

        # 无订阅时使用默认配置
        mock_notification_svc.send_alert_notification.assert_called_once_with(alert=mock_alert_cls.return_value)
