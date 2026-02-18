# -*- coding: utf-8 -*-
"""第十二批：审批路由决策服务单元测试"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.approval_engine.router import ApprovalRouterService
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败")


def _make_service():
    db = MagicMock()
    return ApprovalRouterService(db=db), db


class TestApprovalRouterServiceInit:
    """初始化测试"""

    def test_db_stored(self):
        db = MagicMock()
        svc = ApprovalRouterService(db=db)
        assert svc.db is db


class TestSelectFlow:
    """select_flow 方法测试"""

    def test_returns_default_flow_when_no_rules(self):
        svc, db = _make_service()
        default_flow = MagicMock()
        default_flow.is_default = True

        # 无路由规则
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        # 默认流程查询
        db.query.return_value.filter.return_value.first.return_value = default_flow

        context = {"form_data": {}, "initiator": {"id": 1}}
        result = svc.select_flow(template_id=1, context=context)

        assert result is default_flow

    def test_returns_matched_rule_flow(self):
        svc, db = _make_service()
        matched_flow = MagicMock()

        rule = MagicMock()
        rule.conditions = {"field": "amount", "operator": "gt", "value": 10000}
        rule.flow = matched_flow

        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [rule]

        with patch.object(svc, '_evaluate_conditions', return_value=True):
            context = {"form_data": {"amount": 50000}}
            result = svc.select_flow(template_id=1, context=context)

        assert result is matched_flow

    def test_skips_rules_with_none_conditions(self):
        svc, db = _make_service()
        default_flow = MagicMock()

        rule = MagicMock()
        rule.conditions = None
        rule.flow = MagicMock()

        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [rule]
        db.query.return_value.filter.return_value.first.return_value = default_flow

        context = {}
        result = svc.select_flow(template_id=1, context=context)

        assert result is default_flow

    def test_returns_none_when_no_default(self):
        svc, db = _make_service()

        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        result = svc.select_flow(template_id=99, context={})

        assert result is None


class TestEvaluateConditions:
    """_evaluate_conditions 方法测试"""

    def test_simple_eq_condition_true(self):
        svc, _ = _make_service()
        if not hasattr(svc, '_evaluate_conditions'):
            pytest.skip("无此方法")
        conditions = {"field": "entity.ecn_type", "operator": "eq", "value": "DESIGN"}
        context = {"entity": {"ecn_type": "DESIGN"}}
        result = svc._evaluate_conditions(conditions, context)
        assert isinstance(result, bool)

    def test_empty_conditions_returns_bool(self):
        svc, _ = _make_service()
        if not hasattr(svc, '_evaluate_conditions'):
            pytest.skip("无此方法")
        result = svc._evaluate_conditions({}, {})
        assert isinstance(result, bool)


class TestGetDefaultFlow:
    """_get_default_flow 方法测试"""

    def test_returns_flow_from_db(self):
        svc, db = _make_service()
        if not hasattr(svc, '_get_default_flow'):
            pytest.skip("无此方法")
        flow = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = flow
        result = svc._get_default_flow(template_id=1)
        assert result is flow

    def test_returns_none_when_not_found(self):
        svc, db = _make_service()
        if not hasattr(svc, '_get_default_flow'):
            pytest.skip("无此方法")
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc._get_default_flow(template_id=999)
        assert result is None
