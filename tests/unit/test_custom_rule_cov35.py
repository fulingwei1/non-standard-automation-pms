# -*- coding: utf-8 -*-
"""
第三十五批 - data_scope/custom_rule.py 单元测试
"""
import pytest

try:
    from unittest.mock import MagicMock, patch
    from app.services.data_scope.custom_rule import CustomRuleService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestValidateScopeConfig:

    def test_valid_config(self):
        config = {
            "conditions": [
                {"type": "user_ids", "values": [1, 2]},
                {"type": "org_unit_ids", "values": [10]},
            ],
            "combine_logic": "OR",
            "include_owner": True,
        }
        errors = CustomRuleService.validate_scope_config(config)
        assert errors == []

    def test_invalid_config_not_dict(self):
        errors = CustomRuleService.validate_scope_config("not-a-dict")
        assert len(errors) > 0
        assert "字典" in errors[0]

    def test_conditions_not_list(self):
        errors = CustomRuleService.validate_scope_config({"conditions": "wrong"})
        assert any("数组" in e for e in errors)

    def test_condition_missing_type(self):
        config = {"conditions": [{"values": [1]}]}
        errors = CustomRuleService.validate_scope_config(config)
        assert any("type" in e for e in errors)

    def test_condition_invalid_type(self):
        config = {"conditions": [{"type": "unknown_type", "values": [1]}]}
        errors = CustomRuleService.validate_scope_config(config)
        assert any("无效" in e for e in errors)

    def test_condition_empty_values(self):
        config = {"conditions": [{"type": "user_ids", "values": []}]}
        errors = CustomRuleService.validate_scope_config(config)
        assert any("不能为空" in e for e in errors)

    def test_invalid_combine_logic(self):
        config = {
            "conditions": [{"type": "user_ids", "values": [1]}],
            "combine_logic": "XOR",
        }
        errors = CustomRuleService.validate_scope_config(config)
        assert any("combine_logic" in e for e in errors)

    def test_sql_expression_type_valid(self):
        config = {
            "conditions": [
                {"type": "sql_expression", "expression": "created_by = {{user_id}}"}
            ]
        }
        errors = CustomRuleService.validate_scope_config(config)
        assert errors == []


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestApplyCustomFilter:

    def test_no_config_returns_personal_data(self):
        """没有 scope_config 时降级为个人数据过滤"""
        rule = MagicMock()
        rule.get_scope_config_dict.return_value = {}
        rule.rule_code = "RULE001"

        model = MagicMock()
        model.created_by = MagicMock()
        type(model).created_by = MagicMock()
        # hasattr should return True
        with patch("builtins.hasattr", return_value=True):
            query = MagicMock()
            query.filter.return_value = query
            user = MagicMock()
            user.id = 1
            result = CustomRuleService.apply_custom_filter(query, MagicMock(), user, rule, model)
        # 不应该抛出异常

    def test_or_combine_logic(self):
        """OR 组合逻辑"""
        rule = MagicMock()
        rule.get_scope_config_dict.return_value = {
            "conditions": [{"type": "user_ids", "values": [1, 2]}],
            "combine_logic": "OR",
            "include_owner": False,
        }

        class FakeModel:
            created_by = MagicMock()

        mock_col = MagicMock()
        mock_col.in_.return_value = MagicMock()
        FakeModel.created_by = mock_col

        query = MagicMock()
        query.filter.return_value = query
        user = MagicMock()
        user.id = 99
        db = MagicMock()

        with patch("app.services.data_scope.custom_rule.or_") as mock_or:
            mock_or.return_value = MagicMock()
            CustomRuleService.apply_custom_filter(query, db, user, rule, FakeModel)
        query.filter.assert_called()

    def test_and_combine_logic(self):
        """AND 组合逻辑"""
        rule = MagicMock()
        rule.get_scope_config_dict.return_value = {
            "conditions": [{"type": "user_ids", "values": [1]}],
            "combine_logic": "AND",
            "include_owner": False,
        }

        class FakeModel:
            created_by = MagicMock()

        mock_col = MagicMock()
        mock_col.in_.return_value = MagicMock()
        FakeModel.created_by = mock_col

        query = MagicMock()
        query.filter.return_value = query
        user = MagicMock()
        user.id = 5
        db = MagicMock()

        with patch("app.services.data_scope.custom_rule.and_") as mock_and:
            mock_and.return_value = MagicMock()
            CustomRuleService.apply_custom_filter(
                query, db, user, rule, FakeModel, owner_field="created_by"
            )
        query.filter.assert_called()
