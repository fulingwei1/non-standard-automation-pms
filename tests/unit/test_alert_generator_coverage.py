# -*- coding: utf-8 -*-
"""alert_generator单元测试"""

from app.services.alert.rule_engine.alert_generator import AlertGenerator


class TestAlertGeneratorInit:
    def test_static_api_available(self):
        assert AlertGenerator is not None
        assert hasattr(AlertGenerator, "generate_alert_no")
        assert hasattr(AlertGenerator, "generate_alert_title")
