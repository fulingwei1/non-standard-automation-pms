# -*- coding: utf-8 -*-
"""
InformationGapAnalysisService 综合单元测试

测试覆盖:
- analyze_missing: 信息缺失分析
- analyze_impact: 信息把握不足的影响分析
- get_quality_score: 获取信息质量评分
- _analyze_lead_missing: 分析线索信息缺失
- _analyze_opportunity_missing: 分析商机信息缺失
- _analyze_quote_missing: 分析报价信息缺失
- _analyze_batch_missing: 批量分析信息缺失
- _get_quality_level: 获取质量等级
- _get_recommendations: 获取改进建议
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestAnalyzeMissing:
    """测试 analyze_missing 方法"""

    def test_analyzes_single_lead(self):
        """测试分析单个线索"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        mock_lead = MagicMock()
        mock_lead.customer_name = "测试客户"
        mock_lead.contact_name = "张三"
        mock_lead.contact_phone = "13800138000"
        mock_lead.demand_summary = "需要自动化设备"
        mock_lead.source = "网站"
        mock_lead.industry = "电子"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_lead

        service = InformationGapAnalysisService(mock_db)
        result = service.analyze_missing('LEAD', entity_id=1)

        assert result['entity_type'] == 'LEAD'
        assert result['entity_id'] == 1
        assert result['completeness_score'] == 100
        assert result['quality_level'] == 'HIGH'

    def test_analyzes_lead_with_missing_fields(self):
        """测试分析有缺失字段的线索"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        mock_lead = MagicMock()
        mock_lead.customer_name = "测试客户"
        mock_lead.contact_name = None  # 缺失
        mock_lead.contact_phone = ""  # 空字符串
        mock_lead.demand_summary = "需求"
        mock_lead.source = None  # 缺失
        mock_lead.industry = "电子"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_lead

        service = InformationGapAnalysisService(mock_db)
        result = service.analyze_missing('LEAD', entity_id=1)

        assert 'contact_name' in result['missing_fields']
        assert 'contact_phone' in result['missing_fields']
        assert 'source' in result['missing_fields']
        assert result['completeness_score'] < 100

    def test_analyzes_batch_leads(self):
        """测试批量分析线索"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()

        mock_lead1 = MagicMock()
        mock_lead1.customer_name = "客户1"
        mock_lead1.contact_name = "联系人1"
        mock_lead1.contact_phone = "123"
        mock_lead1.demand_summary = "需求1"
        mock_lead1.source = "来源1"
        mock_lead1.industry = "行业1"

        mock_lead2 = MagicMock()
        mock_lead2.customer_name = None
        mock_lead2.contact_name = None
        mock_lead2.contact_phone = None
        mock_lead2.demand_summary = None
        mock_lead2.source = None
        mock_lead2.industry = None

        mock_db.query.return_value.all.return_value = [mock_lead1, mock_lead2]

        service = InformationGapAnalysisService(mock_db)
        result = service.analyze_missing('LEAD')

        assert result['entity_type'] == 'LEAD'
        assert result['total'] == 2
        assert 'quality_distribution' in result

    def test_analyzes_single_opportunity(self):
        """测试分析单个商机"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        mock_opp = MagicMock()
        mock_opp.opp_name = "商机1"
        mock_opp.est_amount = Decimal("100000")
        mock_opp.budget_range = "10-20万"
        mock_opp.delivery_window = "Q2"
        mock_opp.decision_chain = "总经理"
        mock_opp.acceptance_basis = "性能测试"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_opp

        service = InformationGapAnalysisService(mock_db)
        result = service.analyze_missing('OPPORTUNITY', entity_id=1)

        assert result['entity_type'] == 'OPPORTUNITY'
        assert result['completeness_score'] == 100

    def test_analyzes_single_quote(self):
        """测试分析单个报价"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        mock_quote = MagicMock()
        mock_quote.items = [MagicMock()]
        mock_quote.total_amount = Decimal("50000")
        mock_quote.valid_until = date(2026, 12, 31)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_quote

        service = InformationGapAnalysisService(mock_db)
        result = service.analyze_missing('QUOTE', entity_id=1)

        assert result['entity_type'] == 'QUOTE'
        assert result['completeness_score'] == 100


class TestAnalyzeImpact:
    """测试 analyze_impact 方法"""

    def test_returns_impact_analysis(self):
        """测试返回影响分析"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()

        # 高质量线索(已转化)
        mock_lead1 = MagicMock()
        mock_lead1.customer_name = "客户1"
        mock_lead1.contact_name = "联系人1"
        mock_lead1.contact_phone = "123"
        mock_lead1.demand_summary = "需求1"
        mock_lead1.source = "来源1"
        mock_lead1.industry = "行业1"
        mock_lead1.status = "CONVERTED"

        # 低质量线索(未转化)
        mock_lead2 = MagicMock()
        mock_lead2.customer_name = None
        mock_lead2.contact_name = None
        mock_lead2.contact_phone = None
        mock_lead2.demand_summary = None
        mock_lead2.source = None
        mock_lead2.industry = None
        mock_lead2.status = "NEW"

        # 高质量报价
        mock_quote = MagicMock()
        mock_quote.items = [MagicMock()]
        mock_quote.total_amount = Decimal("50000")
        mock_quote.valid_until = date(2026, 12, 31)

        # Setup query chain
        call_count = [0]
        def query_side_effect(model):
            query_mock = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                # Leads query
                query_mock.all.return_value = [mock_lead1, mock_lead2]
            else:
                # Quotes query
                query_mock.all.return_value = [mock_quote]
            return query_mock

        mock_db.query.side_effect = query_side_effect

        service = InformationGapAnalysisService(mock_db)
        result = service.analyze_impact()

        assert 'lead_quality_impact' in result
        assert 'quote_quality_impact' in result
        assert result['lead_quality_impact']['high_quality_count'] == 1
        assert result['lead_quality_impact']['low_quality_count'] == 1

    def test_handles_date_range(self):
        """测试处理日期范围"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        service = InformationGapAnalysisService(mock_db)
        result = service.analyze_impact(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )

        assert result['analysis_period']['start_date'] == '2026-01-01'
        assert result['analysis_period']['end_date'] == '2026-12-31'


class TestGetQualityScore:
    """测试 get_quality_score 方法"""

    def test_returns_quality_score_with_recommendations(self):
        """测试返回质量评分和建议"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        mock_lead = MagicMock()
        mock_lead.customer_name = "客户"
        mock_lead.contact_name = None  # 缺失
        mock_lead.contact_phone = "123"
        mock_lead.demand_summary = None  # 缺失
        mock_lead.source = "网站"
        mock_lead.industry = "电子"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_lead

        service = InformationGapAnalysisService(mock_db)
        result = service.get_quality_score('LEAD', 1)

        assert 'quality_score' in result
        assert 'quality_level' in result
        assert 'recommendations' in result
        assert len(result['recommendations']) > 0


class TestAnalyzeLeadMissing:
    """测试 _analyze_lead_missing 方法"""

    def test_returns_full_score_for_complete_lead(self):
        """测试完整线索返回满分"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        service = InformationGapAnalysisService(mock_db)

        mock_lead = MagicMock()
        mock_lead.customer_name = "客户"
        mock_lead.contact_name = "联系人"
        mock_lead.contact_phone = "123"
        mock_lead.demand_summary = "需求"
        mock_lead.source = "来源"
        mock_lead.industry = "行业"

        missing, score = service._analyze_lead_missing(mock_lead)

        assert missing == []
        assert score == 100

    def test_deducts_score_for_missing_fields(self):
        """测试缺失字段扣分"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        service = InformationGapAnalysisService(mock_db)

        mock_lead = MagicMock()
        mock_lead.customer_name = None  # -10
        mock_lead.contact_name = None  # -10
        mock_lead.contact_phone = "123"
        mock_lead.demand_summary = "需求"
        mock_lead.source = "来源"
        mock_lead.industry = "行业"

        missing, score = service._analyze_lead_missing(mock_lead)

        assert 'customer_name' in missing
        assert 'contact_name' in missing
        assert score == 80

    def test_handles_empty_string_as_missing(self):
        """测试空字符串视为缺失"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        service = InformationGapAnalysisService(mock_db)

        mock_lead = MagicMock()
        mock_lead.customer_name = "   "  # 空白字符串
        mock_lead.contact_name = "联系人"
        mock_lead.contact_phone = ""  # 空字符串
        mock_lead.demand_summary = "需求"
        mock_lead.source = "来源"
        mock_lead.industry = "行业"

        missing, score = service._analyze_lead_missing(mock_lead)

        assert 'customer_name' in missing
        assert 'contact_phone' in missing


class TestAnalyzeOpportunityMissing:
    """测试 _analyze_opportunity_missing 方法"""

    def test_returns_full_score_for_complete_opportunity(self):
        """测试完整商机返回满分"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        service = InformationGapAnalysisService(mock_db)

        mock_opp = MagicMock()
        mock_opp.opp_name = "商机"
        mock_opp.est_amount = Decimal("100000")
        mock_opp.budget_range = "10-20万"
        mock_opp.delivery_window = "Q2"
        mock_opp.decision_chain = "总经理"
        mock_opp.acceptance_basis = "性能测试"

        missing, score = service._analyze_opportunity_missing(mock_opp)

        assert missing == []
        assert score == 100

    def test_deducts_score_for_missing_amount(self):
        """测试缺失金额扣分"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        service = InformationGapAnalysisService(mock_db)

        mock_opp = MagicMock()
        mock_opp.opp_name = "商机"
        mock_opp.est_amount = None  # -15
        mock_opp.budget_range = "10-20万"
        mock_opp.delivery_window = "Q2"
        mock_opp.decision_chain = "总经理"
        mock_opp.acceptance_basis = "性能测试"

        missing, score = service._analyze_opportunity_missing(mock_opp)

        assert 'est_amount' in missing
        assert score == 85


class TestAnalyzeQuoteMissing:
    """测试 _analyze_quote_missing 方法"""

    def test_returns_full_score_for_complete_quote(self):
        """测试完整报价返回满分"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        service = InformationGapAnalysisService(mock_db)

        mock_quote = MagicMock()
        mock_quote.items = [MagicMock()]
        mock_quote.total_amount = Decimal("50000")
        mock_quote.valid_until = date(2026, 12, 31)

        missing, score = service._analyze_quote_missing(mock_quote)

        assert missing == []
        assert score == 100

    def test_deducts_score_for_missing_items(self):
        """测试缺失明细扣分"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        service = InformationGapAnalysisService(mock_db)

        mock_quote = MagicMock()
        mock_quote.items = []  # -20
        mock_quote.total_amount = Decimal("50000")
        mock_quote.valid_until = date(2026, 12, 31)

        missing, score = service._analyze_quote_missing(mock_quote)

        assert 'quote_items' in missing
        assert score == 80


class TestGetQualityLevel:
    """测试 _get_quality_level 方法"""

    def test_returns_high_for_score_80_plus(self):
        """测试80分以上返回HIGH"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        service = InformationGapAnalysisService(mock_db)

        assert service._get_quality_level(100) == 'HIGH'
        assert service._get_quality_level(80) == 'HIGH'

    def test_returns_medium_for_score_60_to_79(self):
        """测试60-79分返回MEDIUM"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        service = InformationGapAnalysisService(mock_db)

        assert service._get_quality_level(79) == 'MEDIUM'
        assert service._get_quality_level(60) == 'MEDIUM'

    def test_returns_low_for_score_below_60(self):
        """测试60分以下返回LOW"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        service = InformationGapAnalysisService(mock_db)

        assert service._get_quality_level(59) == 'LOW'
        assert service._get_quality_level(0) == 'LOW'


class TestGetRecommendations:
    """测试 _get_recommendations 方法"""

    def test_returns_recommendations_for_missing_fields(self):
        """测试返回缺失字段的建议"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        service = InformationGapAnalysisService(mock_db)

        recommendations = service._get_recommendations(['customer_name', 'contact_phone'])

        assert len(recommendations) == 2
        assert any('客户名称' in r for r in recommendations)
        assert any('联系电话' in r for r in recommendations)

    def test_returns_empty_for_no_missing_fields(self):
        """测试无缺失字段返回空"""
        from app.services.information_gap_analysis_service import InformationGapAnalysisService

        mock_db = MagicMock()
        service = InformationGapAnalysisService(mock_db)

        recommendations = service._get_recommendations([])

        assert recommendations == []
