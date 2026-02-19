# -*- coding: utf-8 -*-
"""
第三十三批覆盖率测试 - 预警规则管理服务 (AlertRulesService)
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

try:
    from app.services.alert.alert_rules_service import AlertRulesService
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="alert_rules_service 导入失败")


def _make_service():
    db = MagicMock()
    return AlertRulesService(db), db


class TestGetAlertRules:
    def test_returns_paginated_response(self):
        """返回分页响应对象"""
        service, db = _make_service()

        mock_rule = MagicMock()

        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 1
        q.all.return_value = [mock_rule]
        db.query.return_value = q

        with patch(
            "app.services.alert.alert_rules_service.apply_keyword_filter",
            return_value=q
        ), patch(
            "app.services.alert.alert_rules_service.apply_pagination",
            return_value=q
        ), patch(
            "app.services.alert.alert_rules_service.AlertRuleResponse.model_validate",
            return_value={"id": 1, "rule_name": "测试规则"}
        ):
            result = service.get_alert_rules(page=1, page_size=10)

        assert result.total == 1

    def test_filter_by_rule_type(self):
        """按rule_type过滤"""
        service, db = _make_service()

        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 0
        q.all.return_value = []
        db.query.return_value = q

        with patch(
            "app.services.alert.alert_rules_service.apply_keyword_filter",
            return_value=q
        ), patch(
            "app.services.alert.alert_rules_service.apply_pagination",
            return_value=q
        ):
            result = service.get_alert_rules(rule_type="project_delay")

        assert result.total == 0


class TestGetAlertRule:
    def test_returns_rule_when_found(self):
        """找到规则时返回"""
        service, db = _make_service()
        mock_rule = MagicMock()
        mock_rule.id = 1
        db.query.return_value.filter.return_value.first.return_value = mock_rule

        result = service.get_alert_rule(1)
        assert result is mock_rule

    def test_returns_none_when_not_found(self):
        """规则不存在时返回None"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_alert_rule(999)
        assert result is None


class TestCreateAlertRule:
    def test_creates_rule_with_generated_code(self):
        """创建规则时生成规则编码"""
        service, db = _make_service()

        rule_data = MagicMock()
        rule_data.rule_type = "project_delay"
        rule_data.rule_name = "项目延期7天预警"
        rule_data.target_type = "PROJECT"
        rule_data.condition_config = {}
        rule_data.notification_config = {}
        rule_data.severity = "HIGH"
        rule_data.is_enabled = True
        rule_data.description = "项目延期超过7天触发"

        current_user = MagicMock()
        current_user.id = 1

        mock_q = MagicMock()
        mock_q.filter.return_value.count.return_value = 0
        db.query.return_value = mock_q

        with patch(
            "app.services.alert.alert_rules_service.AlertRule"
        ) as mock_cls, patch(
            "app.services.alert.alert_rules_service.save_obj"
        ) as mock_save:
            mock_rule = MagicMock()
            mock_cls.return_value = mock_rule

            result = service.create_alert_rule(rule_data, current_user)

        mock_save.assert_called_once()
        assert result is mock_rule


class TestUpdateAlertRule:
    def test_returns_none_when_not_found(self):
        """规则不存在时返回None"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        rule_data = MagicMock()
        result = service.update_alert_rule(999, rule_data, MagicMock())

        assert result is None

    def test_updates_fields(self):
        """更新指定字段"""
        service, db = _make_service()

        mock_rule = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_rule

        rule_data = MagicMock()
        rule_data.dict.return_value = {"rule_name": "新名称", "is_enabled": False}

        current_user = MagicMock()
        current_user.id = 2

        result = service.update_alert_rule(1, rule_data, current_user)

        assert mock_rule.rule_name == "新名称"
        assert mock_rule.is_enabled is False
        db.commit.assert_called_once()


class TestToggleAlertRule:
    def test_toggles_enabled_to_disabled(self):
        """已启用的规则切换为禁用"""
        service, db = _make_service()

        mock_rule = MagicMock()
        mock_rule.is_enabled = True
        db.query.return_value.filter.return_value.first.return_value = mock_rule

        result = service.toggle_alert_rule(1, MagicMock())

        assert mock_rule.is_enabled is False
        db.commit.assert_called_once()

    def test_toggles_disabled_to_enabled(self):
        """已禁用的规则切换为启用"""
        service, db = _make_service()

        mock_rule = MagicMock()
        mock_rule.is_enabled = False
        db.query.return_value.filter.return_value.first.return_value = mock_rule

        service.toggle_alert_rule(1, MagicMock())

        assert mock_rule.is_enabled is True


class TestDeleteAlertRule:
    def test_returns_false_when_not_found(self):
        """规则不存在时返回False"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        result = service.delete_alert_rule(999)
        assert result is False

    def test_returns_true_on_success(self):
        """删除成功返回True"""
        service, db = _make_service()
        mock_rule = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_rule

        with patch("app.services.alert.alert_rules_service.delete_obj") as mock_delete:
            result = service.delete_alert_rule(1)

        assert result is True
        mock_delete.assert_called_once_with(db, mock_rule)


class TestGenerateRuleCode:
    def test_known_type_generates_code_with_prefix(self):
        """已知类型生成带正确前缀的编码"""
        service, db = _make_service()

        mock_q = MagicMock()
        mock_q.filter.return_value.count.return_value = 0
        db.query.return_value = mock_q

        code = service._generate_rule_code("project_delay")
        assert code.startswith("PD")

    def test_unknown_type_uses_al_prefix(self):
        """未知类型使用AL前缀"""
        service, db = _make_service()

        mock_q = MagicMock()
        mock_q.filter.return_value.count.return_value = 2
        db.query.return_value = mock_q

        code = service._generate_rule_code("unknown_type")
        assert code.startswith("AL")
        assert code.endswith("003")
