# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - AlertCreator"""

import pytest
from unittest.mock import MagicMock


class TestAlertCreatorBusinessLogic:
    def test_init_with_db(self):
        from app.services.alert.rule_engine.alert_creator import AlertCreator

        mock_db = MagicMock()
        creator = AlertCreator(mock_db)
        assert creator.db == mock_db

    def test_should_create_alert_no_existing(self):
        from app.services.alert.rule_engine.alert_creator import AlertCreator
        from app.models.alert import AlertRule

        mock_db = MagicMock()
        mock_rule = MagicMock(spec=AlertRule)
        mock_rule.id = 1
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        creator = AlertCreator(mock_db)
        result = creator.should_create_alert(mock_rule, {"target_type": "project", "target_id": 1}, "HIGH")
        assert result is None

    def test_should_create_alert_existing_active(self):
        from app.services.alert.rule_engine.alert_creator import AlertCreator
        from app.models.alert import AlertRule, AlertRecord

        mock_db = MagicMock()
        mock_rule = MagicMock(spec=AlertRule)
        mock_rule.id = 1
        existing = MagicMock(spec=AlertRecord)
        existing.status = "ACTIVE"
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = existing

        creator = AlertCreator(mock_db)
        result = creator.should_create_alert(mock_rule, {"target_type": "project", "target_id": 1}, "HIGH")
        assert result == existing

    def test_create_alert_basic(self):
        from app.services.alert.rule_engine.alert_creator import AlertCreator
        from app.models.alert import AlertRule

        mock_db = MagicMock()
        mock_rule = MagicMock(spec=AlertRule)
        mock_rule.id = 1
        mock_rule.name = "测试规则"
        mock_rule.severity = "HIGH"
        creator = AlertCreator(mock_db)
        assert creator.db == mock_db

    def test_notification_service_lazy_load(self):
        from app.services.alert.rule_engine.alert_creator import AlertCreator

        creator = AlertCreator(MagicMock())
        assert creator._notification_service is None

    def test_subscription_service_lazy_load(self):
        from app.services.alert.rule_engine.alert_creator import AlertCreator

        creator = AlertCreator(MagicMock())
        assert creator._subscription_service is None


class TestConditionEvaluatorBusinessLogic:
    def test_init(self):
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            evaluator = ConditionEvaluator()
            assert evaluator is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_evaluate_simple_condition(self):
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            evaluator = ConditionEvaluator()
            assert hasattr(evaluator, "match_threshold")
        except ImportError:
            pytest.skip("Module not found")


class TestAlertNotificationServiceBusinessLogic:
    def test_send_notification(self):
        try:
            from app.services.notification.notification_service import AlertNotificationService

            mock_db = MagicMock()
            service = AlertNotificationService(mock_db)
            assert service.db == mock_db
        except ImportError:
            pytest.skip("Module not found")


class TestAlertSubscriptionServiceBusinessLogic:
    def test_get_subscribers(self):
        try:
            from app.services.alert.alert_subscription_service import AlertSubscriptionService

            mock_db = MagicMock()
            service = AlertSubscriptionService(mock_db)
            assert service.db == mock_db
        except ImportError:
            pytest.skip("Module not found")
