# -*- coding: utf-8 -*-
"""第十七批 - 变更应对方案生成服务单元测试"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from decimal import Decimal

pytest.importorskip("app.services.change_response_suggestion_service")


def _make_service(db=None):
    from app.services.change_response_suggestion_service import ChangeResponseSuggestionService
    return ChangeResponseSuggestionService(db or MagicMock())


def _mock_change(code="ECN-001"):
    c = MagicMock()
    c.id = 1
    c.change_code = code
    return c


def _mock_analysis(risk="LOW", cost=Decimal("1000"), delay=5):
    a = MagicMock()
    a.id = 1
    a.overall_risk_level = risk
    a.cost_impact_amount = cost
    a.schedule_delay_days = delay
    return a


class TestCreateApproveSuggestion:

    def test_approve_suggestion_low_risk(self):
        """LOW 风险时 _create_approve_suggestion 生成正确字段"""
        svc = _make_service()
        change = _mock_change()
        analysis = _mock_analysis(risk="LOW")

        result = svc._create_approve_suggestion(change, analysis, user_id=1)

        assert result.suggestion_type == "APPROVE"
        assert result.suggestion_code == "SUG-ECN-001-01"
        assert result.technical_feasibility == "HIGH"

    def test_modify_suggestion_fields(self):
        """_create_modify_suggestion 返回 MODIFY 类型"""
        svc = _make_service()
        change = _mock_change()
        analysis = _mock_analysis(risk="MEDIUM", cost=Decimal("2000"), delay=10)

        result = svc._create_modify_suggestion(change, analysis, user_id=2)

        assert result.suggestion_type == "MODIFY"
        assert result.suggestion_code == "SUG-ECN-001-02"
        # 成本应为 2000 * 0.7
        assert result.estimated_cost == Decimal("2000") * Decimal("0.7")

    def test_mitigate_suggestion_high_risk(self):
        """HIGH 风险时 _create_mitigate_suggestion 生成 MITIGATE 类型"""
        svc = _make_service()
        change = _mock_change()
        analysis = _mock_analysis(risk="HIGH", cost=Decimal("5000"), delay=20)

        result = svc._create_mitigate_suggestion(change, analysis, user_id=3)

        assert result.suggestion_type == "MITIGATE"
        assert result.suggestion_priority == 9
        # 成本应更高
        assert result.estimated_cost == Decimal("5000") * Decimal("1.3")

    def test_generate_suggestions_analysis_not_found(self):
        """影响分析不存在时抛 ValueError"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = _make_service(db)

        import asyncio
        with pytest.raises(ValueError, match="影响分析.*不存在"):
            asyncio.get_event_loop().run_until_complete(
                svc.generate_suggestions(1, 999, 1)
            )

    def test_generate_suggestions_change_not_found(self):
        """变更请求不存在时抛 ValueError"""
        db = MagicMock()
        analysis = _mock_analysis()
        # 第一次 query 返回 analysis，第二次返回 None
        db.query.return_value.filter.return_value.first.side_effect = [analysis, None]
        svc = _make_service(db)

        import asyncio
        with pytest.raises(ValueError, match="变更请求.*不存在"):
            asyncio.get_event_loop().run_until_complete(
                svc.generate_suggestions(999, 1, 1)
            )

    def test_generate_suggestions_low_risk_produces_approve_and_modify(self):
        """LOW 风险时生成 APPROVE + MODIFY 两个方案"""
        db = MagicMock()
        analysis = _mock_analysis(risk="LOW")
        change = _mock_change()
        db.query.return_value.filter.return_value.first.side_effect = [analysis, change]
        svc = _make_service(db)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            svc.generate_suggestions(1, 1, 1)
        )
        types = [s.suggestion_type for s in result]
        assert "APPROVE" in types
        assert "MODIFY" in types

    def test_generate_suggestions_high_risk_produces_mitigate(self):
        """HIGH 风险时生成包含 MITIGATE 的方案"""
        db = MagicMock()
        analysis = _mock_analysis(risk="HIGH")
        change = _mock_change()
        db.query.return_value.filter.return_value.first.side_effect = [analysis, change]
        svc = _make_service(db)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            svc.generate_suggestions(1, 1, 1)
        )
        types = [s.suggestion_type for s in result]
        assert "MITIGATE" in types
