# -*- coding: utf-8 -*-
"""
Tests for pipeline_break_analysis_service service
Covers: app/services/pipeline_break_analysis_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 139 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.services.pipeline_break_analysis_service import PipelineBreakAnalysisService



@pytest.fixture
def pipeline_break_analysis_service(db_session: Session):
    """创建 PipelineBreakAnalysisService 实例"""
    return PipelineBreakAnalysisService(db_session)


class TestPipelineBreakAnalysisService:
    """Test suite for PipelineBreakAnalysisService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = PipelineBreakAnalysisService(db_session)
        assert service is not None
        if hasattr(service, 'db'):
            assert service.db == db_session


    def test_analyze_pipeline_breaks(self, pipeline_break_analysis_service):
        """测试 analyze_pipeline_breaks 方法"""
        # TODO: 实现测试逻辑
        # 1. 准备测试数据
        # 2. 调用方法
        # 3. 验证结果
        pass


    def test_get_break_reasons(self, pipeline_break_analysis_service):
        """测试 get_break_reasons 方法"""
        # TODO: 实现测试逻辑
        # 1. 准备测试数据
        # 2. 调用方法
        # 3. 验证结果
        pass


    def test_get_break_patterns(self, pipeline_break_analysis_service):
        """测试 get_break_patterns 方法"""
        # TODO: 实现测试逻辑
        # 1. 准备测试数据
        # 2. 调用方法
        # 3. 验证结果
        pass


    def test_get_break_warnings(self, pipeline_break_analysis_service):
        """测试 get_break_warnings 方法"""
        # TODO: 实现测试逻辑
        # 1. 准备测试数据
        # 2. 调用方法
        # 3. 验证结果
        pass


    # TODO: 添加更多测试用例
    # - 正常流程测试 (Happy Path)
    # - 边界条件测试 (Edge Cases)
    # - 异常处理测试 (Error Handling)
    # - 数据验证测试 (Data Validation)


# ──────────────────────────────────────────────────────────────────────────────
# G4 补充测试（纯 MagicMock，不依赖真实数据库）
# ──────────────────────────────────────────────────────────────────────────────

from unittest.mock import MagicMock, patch
from datetime import date, timedelta
import pytest


class TestPipelineBreakAnalysisServiceG4:
    """G4 补充：PipelineBreakAnalysisService 深度覆盖"""

    def _make_service(self):
        from app.services.pipeline_break_analysis_service import PipelineBreakAnalysisService
        db = MagicMock()
        return PipelineBreakAnalysisService(db), db

    # ---- analyze_pipeline_breaks: 所有环节空数据 ----

    def test_analyze_pipeline_breaks_empty(self):
        """各环节均无数据时，break_rates 中所有环节断链率为0"""
        service, db = self._make_service()

        empty_stage = {"total": 0, "break_count": 0, "break_records": []}
        with patch.multiple(
            service,
            _detect_lead_to_opp_breaks=MagicMock(return_value=empty_stage),
            _detect_opp_to_quote_breaks=MagicMock(return_value=empty_stage),
            _detect_quote_to_contract_breaks=MagicMock(return_value=empty_stage),
            _detect_contract_to_project_breaks=MagicMock(return_value=empty_stage),
            _detect_project_to_invoice_breaks=MagicMock(return_value=empty_stage),
            _detect_invoice_to_payment_breaks=MagicMock(return_value=empty_stage),
        ):
            result = service.analyze_pipeline_breaks()

        assert "break_rates" in result
        for stage_data in result["break_rates"].values():
            assert stage_data["break_rate"] == 0

    # ---- analyze_pipeline_breaks: 有断链数据 ----

    def test_analyze_pipeline_breaks_with_data(self):
        """有断链数据时，break_rates 包含正确比率"""
        service, db = self._make_service()

        lead_stage = {"total": 10, "break_count": 3, "break_records": []}
        empty_stage = {"total": 5, "break_count": 0, "break_records": []}

        with patch.multiple(
            service,
            _detect_lead_to_opp_breaks=MagicMock(return_value=lead_stage),
            _detect_opp_to_quote_breaks=MagicMock(return_value=empty_stage),
            _detect_quote_to_contract_breaks=MagicMock(return_value=empty_stage),
            _detect_contract_to_project_breaks=MagicMock(return_value=empty_stage),
            _detect_project_to_invoice_breaks=MagicMock(return_value=empty_stage),
            _detect_invoice_to_payment_breaks=MagicMock(return_value=empty_stage),
        ):
            result = service.analyze_pipeline_breaks()

        assert result["break_rates"]["LEAD_TO_OPP"]["break_rate"] == 30.0
        assert result["break_rates"]["LEAD_TO_OPP"]["break_count"] == 3

    # ---- analyze_pipeline_breaks: top_break_stages 排序正确 ----

    def test_top_break_stages_sorted(self):
        """top_break_stages 按断链率降序排列"""
        service, db = self._make_service()

        high = {"total": 10, "break_count": 8, "break_records": []}
        mid = {"total": 10, "break_count": 5, "break_records": []}
        low = {"total": 10, "break_count": 1, "break_records": []}

        with patch.multiple(
            service,
            _detect_lead_to_opp_breaks=MagicMock(return_value=high),
            _detect_opp_to_quote_breaks=MagicMock(return_value=mid),
            _detect_quote_to_contract_breaks=MagicMock(return_value=low),
            _detect_contract_to_project_breaks=MagicMock(return_value=low),
            _detect_project_to_invoice_breaks=MagicMock(return_value=low),
            _detect_invoice_to_payment_breaks=MagicMock(return_value=low),
        ):
            result = service.analyze_pipeline_breaks()

        top = result["top_break_stages"]
        assert top[0]["break_rate"] >= top[1]["break_rate"]

    # ---- analyze_pipeline_breaks: 返回分析周期 ----

    def test_analysis_period_in_result(self):
        """结果中包含 analysis_period"""
        service, db = self._make_service()

        empty = {"total": 0, "break_count": 0, "break_records": []}
        with patch.multiple(
            service,
            _detect_lead_to_opp_breaks=MagicMock(return_value=empty),
            _detect_opp_to_quote_breaks=MagicMock(return_value=empty),
            _detect_quote_to_contract_breaks=MagicMock(return_value=empty),
            _detect_contract_to_project_breaks=MagicMock(return_value=empty),
            _detect_project_to_invoice_breaks=MagicMock(return_value=empty),
            _detect_invoice_to_payment_breaks=MagicMock(return_value=empty),
        ):
            start = date(2024, 1, 1)
            end = date(2024, 12, 31)
            result = service.analyze_pipeline_breaks(start_date=start, end_date=end)

        assert result["analysis_period"]["start_date"] == "2024-01-01"
        assert result["analysis_period"]["end_date"] == "2024-12-31"

    # ---- DEFAULT_BREAK_THRESHOLDS 常量正确 ----

    def test_default_break_thresholds_exist(self):
        """服务包含正确的默认阈值配置"""
        from app.services.pipeline_break_analysis_service import PipelineBreakAnalysisService
        thresholds = PipelineBreakAnalysisService.DEFAULT_BREAK_THRESHOLDS
        assert "LEAD_TO_OPP" in thresholds
        assert "OPP_TO_QUOTE" in thresholds
        assert "QUOTE_TO_CONTRACT" in thresholds
        assert thresholds["LEAD_TO_OPP"] == 30

    # ---- _detect_lead_to_opp_breaks: 空线索 ----

    def test_detect_lead_to_opp_breaks_empty_leads(self):
        """无线索时断链数为 0"""
        service, db = self._make_service()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = service._detect_lead_to_opp_breaks(date(2024, 1, 1), date(2024, 12, 31))
        assert result["break_count"] == 0
        assert result["total"] == 0
