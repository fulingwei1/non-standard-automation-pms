# -*- coding: utf-8 -*-
"""
Tests for information_gap_analysis_service service
Covers: app/services/information_gap_analysis_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 125 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.information_gap_analysis_service import InformationGapAnalysisService
from app.models.sales import Lead, Opportunity, Quote


@pytest.fixture
def information_gap_analysis_service(db_session: Session):
    """创建 InformationGapAnalysisService 实例"""
    return InformationGapAnalysisService(db_session)


@pytest.fixture
def test_lead_complete(db_session: Session):
    """创建完整信息的线索"""
    lead = Lead(
        customer_name="测试客户",
        contact_name="联系人",
        contact_phone="13800138000",
        demand_summary="需求摘要",
        source="WEB",
        industry="制造业"
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead


@pytest.fixture
def test_lead_incomplete(db_session: Session):
    """创建不完整信息的线索"""
    lead = Lead(
        customer_name="测试客户",
        contact_name=None,
        contact_phone=None,
        demand_summary=None
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead


@pytest.fixture
def test_quote_complete(db_session: Session):
    """创建完整信息的报价"""
    quote = Quote(
        total_amount=Decimal("100000.00"),
        valid_until=date.today() + timedelta(days=30)
    )
    db_session.add(quote)
    db_session.commit()
    db_session.refresh(quote)
    return quote


@pytest.fixture
def test_quote_incomplete(db_session: Session):
    """创建不完整信息的报价"""
    quote = Quote(
        total_amount=None,
        valid_until=None
    )
    db_session.add(quote)
    db_session.commit()
    db_session.refresh(quote)
    return quote


class TestInformationGapAnalysisService:
    """Test suite for InformationGapAnalysisService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = InformationGapAnalysisService(db_session)
        assert service is not None
        assert service.db == db_session

    def test_analyze_missing_lead_complete(self, information_gap_analysis_service, test_lead_complete):
        """测试分析线索信息缺失 - 完整信息"""
        result = information_gap_analysis_service.analyze_missing('LEAD', test_lead_complete.id)
        
        assert result is not None
        assert result['entity_type'] == 'LEAD'
        assert result['entity_id'] == test_lead_complete.id
        assert len(result['missing_fields']) == 0
        assert result['completeness_score'] >= 80
        assert result['quality_level'] == 'HIGH'

    def test_analyze_missing_lead_incomplete(self, information_gap_analysis_service, test_lead_incomplete):
        """测试分析线索信息缺失 - 不完整信息"""
        result = information_gap_analysis_service.analyze_missing('LEAD', test_lead_incomplete.id)
        
        assert result is not None
        assert len(result['missing_fields']) > 0
        assert result['completeness_score'] < 80
        assert result['quality_level'] in ['MEDIUM', 'LOW']

    def test_analyze_missing_lead_not_found(self, information_gap_analysis_service):
        """测试分析线索信息缺失 - 线索不存在"""
        result = information_gap_analysis_service.analyze_missing('LEAD', 99999)
        
        assert result is not None
        assert result['entity_id'] == 99999
        assert result['completeness_score'] == 100  # 默认值

    def test_analyze_missing_lead_batch(self, information_gap_analysis_service, db_session):
        """测试批量分析线索信息缺失"""
        # 创建多个线索
        for i in range(3):
            lead = Lead(
            customer_name=f"客户{i}",
            contact_name="联系人" if i % 2 == 0 else None
            )
            db_session.add(lead)
            db_session.commit()
        
            result = information_gap_analysis_service.analyze_missing('LEAD')
        
            assert result is not None
            assert result['entity_type'] == 'LEAD'
            assert 'total' in result
            assert 'quality_distribution' in result
            assert 'common_missing_fields' in result

    def test_analyze_missing_quote_complete(self, information_gap_analysis_service, test_quote_complete):
        """测试分析报价信息缺失 - 完整信息"""
        result = information_gap_analysis_service.analyze_missing('QUOTE', test_quote_complete.id)
        
        assert result is not None
        assert result['entity_type'] == 'QUOTE'
        assert result['entity_id'] == test_quote_complete.id

    def test_analyze_missing_quote_incomplete(self, information_gap_analysis_service, test_quote_incomplete):
        """测试分析报价信息缺失 - 不完整信息"""
        result = information_gap_analysis_service.analyze_missing('QUOTE', test_quote_incomplete.id)
        
        assert result is not None
        assert len(result['missing_fields']) > 0
        assert result['completeness_score'] < 100

    def test_analyze_impact_no_data(self, information_gap_analysis_service):
        """测试分析影响 - 无数据"""
        result = information_gap_analysis_service.analyze_impact()
        
        assert result is not None
        assert 'analysis_period' in result
        assert 'lead_quality_impact' in result
        assert 'quote_quality_impact' in result

    def test_analyze_impact_with_date_range(self, information_gap_analysis_service):
        """测试分析影响 - 带日期范围"""
        start_date = date.today() - timedelta(days=90)
        end_date = date.today()
        
        result = information_gap_analysis_service.analyze_impact(
        start_date=start_date,
        end_date=end_date
        )
        
        assert result is not None
        assert result['analysis_period']['start_date'] == start_date.isoformat()
        assert result['analysis_period']['end_date'] == end_date.isoformat()

    def test_analyze_impact_with_leads(self, information_gap_analysis_service, test_lead_complete, test_lead_incomplete):
        """测试分析影响 - 有线索数据"""
        result = information_gap_analysis_service.analyze_impact()
        
        assert result is not None
        assert 'lead_quality_impact' in result
        assert 'high_quality_count' in result['lead_quality_impact']
        assert 'low_quality_count' in result['lead_quality_impact']

    def test_get_quality_score_lead(self, information_gap_analysis_service, test_lead_complete):
        """测试获取质量评分 - 线索"""
        result = information_gap_analysis_service.get_quality_score('LEAD', test_lead_complete.id)
        
        assert result is not None
        assert result['entity_type'] == 'LEAD'
        assert result['entity_id'] == test_lead_complete.id
        assert 'quality_score' in result
        assert 'quality_level' in result
        assert 'missing_fields' in result
        assert 'recommendations' in result

    def test_get_quality_score_quote(self, information_gap_analysis_service, test_quote_complete):
        """测试获取质量评分 - 报价"""
        result = information_gap_analysis_service.get_quality_score('QUOTE', test_quote_complete.id)
        
        assert result is not None
        assert result['entity_type'] == 'QUOTE'
        assert 'recommendations' in result

    def test_get_quality_score_with_recommendations(self, information_gap_analysis_service, test_lead_incomplete):
        """测试获取质量评分 - 带改进建议"""
        result = information_gap_analysis_service.get_quality_score('LEAD', test_lead_incomplete.id)
        
        assert result is not None
        assert len(result['recommendations']) > 0
