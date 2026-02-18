# -*- coding: utf-8 -*-
"""
第十九批 - 信息把握不足分析服务单元测试
"""
import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.information_gap_analysis_service")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    from app.services.information_gap_analysis_service import InformationGapAnalysisService
    return InformationGapAnalysisService(mock_db)


def _make_lead(customer_name="客户A", contact_name="张三", contact_phone="13800138000",
               demand_summary="需求摘要", source="REFERRAL", industry="IT"):
    lead = MagicMock()
    lead.customer_name = customer_name
    lead.contact_name = contact_name
    lead.contact_phone = contact_phone
    lead.demand_summary = demand_summary
    lead.source = source
    lead.industry = industry
    lead.status = "ACTIVE"
    return lead


def _make_opportunity(opp_name="商机A", est_amount=100000.0, budget_range="10-20万",
                      delivery_window="Q1", decision_chain="CTO", acceptance_basis="验收标准"):
    opp = MagicMock()
    opp.opp_name = opp_name
    opp.est_amount = est_amount
    opp.budget_range = budget_range
    opp.delivery_window = delivery_window
    opp.decision_chain = decision_chain
    opp.acceptance_basis = acceptance_basis
    return opp


def _make_quote(items=None, total_amount=50000.0, valid_until="2024-12-31"):
    quote = MagicMock()
    quote.items = items if items is not None else [MagicMock()]
    quote.total_amount = total_amount
    quote.valid_until = valid_until
    return quote


def test_analyze_missing_lead_complete(service, mock_db):
    """完整线索信息返回满分"""
    lead = _make_lead()
    mock_db.query.return_value.filter.return_value.first.return_value = lead
    result = service.analyze_missing("LEAD", entity_id=1)
    assert result['completeness_score'] == 100
    assert result['missing_fields'] == []


def test_analyze_missing_lead_missing_fields(service, mock_db):
    """缺少字段时扣分"""
    lead = _make_lead(customer_name=None, contact_phone=None)
    mock_db.query.return_value.filter.return_value.first.return_value = lead
    result = service.analyze_missing("LEAD", entity_id=1)
    assert result['completeness_score'] < 100
    assert 'customer_name' in result['missing_fields']
    assert 'contact_phone' in result['missing_fields']


def test_analyze_missing_opportunity_complete(service, mock_db):
    """完整商机信息返回满分"""
    opp = _make_opportunity()
    mock_db.query.return_value.filter.return_value.first.return_value = opp
    result = service.analyze_missing("OPPORTUNITY", entity_id=1)
    assert result['completeness_score'] == 100


def test_analyze_missing_opportunity_missing(service, mock_db):
    """商机缺少预估金额时扣分"""
    opp = _make_opportunity(est_amount=None, budget_range=None)
    mock_db.query.return_value.filter.return_value.first.return_value = opp
    result = service.analyze_missing("OPPORTUNITY", entity_id=2)
    assert result['completeness_score'] < 100
    assert 'est_amount' in result['missing_fields']


def test_analyze_missing_quote_no_items(service, mock_db):
    """报价无明细时扣分"""
    quote = _make_quote(items=[])
    mock_db.query.return_value.filter.return_value.first.return_value = quote
    result = service.analyze_missing("QUOTE", entity_id=1)
    assert 'quote_items' in result['missing_fields']
    assert result['completeness_score'] < 100


def test_get_quality_score_high(service, mock_db):
    """高质量线索返回 HIGH 等级"""
    lead = _make_lead()
    mock_db.query.return_value.filter.return_value.first.return_value = lead
    result = service.get_quality_score("LEAD", entity_id=1)
    assert result['quality_level'] == 'HIGH'
    assert result['quality_score'] == 100


def test_analyze_missing_batch_leads(service, mock_db):
    """批量分析线索质量分布"""
    leads = [
        _make_lead(),
        _make_lead(customer_name=None),
    ]
    mock_db.query.return_value.all.return_value = leads
    result = service.analyze_missing("LEAD")
    assert 'quality_distribution' in result
    assert result['total'] == 2


def test_get_recommendations(service):
    """缺失字段对应建议"""
    recs = service._get_recommendations(['customer_name', 'contact_phone', 'demand_summary'])
    assert len(recs) == 3
    assert any('客户名称' in r for r in recs)


def test_quality_level_low(service):
    """低分返回 LOW 等级"""
    level = service._get_quality_level(50)
    assert level == 'LOW'


def test_quality_level_medium(service):
    """中等分返回 MEDIUM 等级"""
    level = service._get_quality_level(70)
    assert level == 'MEDIUM'
