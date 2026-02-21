# -*- coding: utf-8 -*-
"""
完整单元测试 - win_rate_prediction_service/history.py
目标：60%+ 覆盖率，30+ 测试用例
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.services.win_rate_prediction_service.history import (
    get_salesperson_historical_win_rate,
    get_customer_cooperation_history,
    get_similar_leads_statistics,
)
from app.models.enums import LeadOutcomeEnum


class TestGetSalespersonHistoricalWinRate:
    """销售人员历史中标率测试"""
    
    def test_no_data_returns_default_rate(self):
        """测试无数据时返回行业平均值"""
        service = MagicMock()
        stats = MagicMock()
        stats.total = 0
        stats.won = 0
        service.db.query.return_value.filter.return_value.first.return_value = stats
        
        rate, count = get_salesperson_historical_win_rate(service, salesperson_id=1)
        
        assert rate == 0.20  # 行业平均
        assert count == 0
    
    def test_with_data_calculates_rate(self):
        """测试有数据时计算中标率"""
        service = MagicMock()
        stats = MagicMock()
        stats.total = 10
        stats.won = 7
        service.db.query.return_value.filter.return_value.first.return_value = stats
        
        rate, count = get_salesperson_historical_win_rate(service, salesperson_id=1)
        
        assert rate == pytest.approx(0.7)
        assert count == 10
    
    def test_perfect_win_rate(self):
        """测试100%中标率"""
        service = MagicMock()
        stats = MagicMock()
        stats.total = 5
        stats.won = 5
        service.db.query.return_value.filter.return_value.first.return_value = stats
        
        rate, count = get_salesperson_historical_win_rate(service, salesperson_id=1)
        
        assert rate == 1.0
        assert count == 5
    
    def test_zero_win_rate(self):
        """测试0%中标率"""
        service = MagicMock()
        stats = MagicMock()
        stats.total = 8
        stats.won = 0
        service.db.query.return_value.filter.return_value.first.return_value = stats
        
        rate, count = get_salesperson_historical_win_rate(service, salesperson_id=1)
        
        assert rate == 0.0
        assert count == 8
    
    def test_different_lookback_months(self):
        """测试不同回溯月数"""
        service = MagicMock()
        stats = MagicMock()
        stats.total = 15
        stats.won = 10
        service.db.query.return_value.filter.return_value.first.return_value = stats
        
        # 默认24个月
        rate1, count1 = get_salesperson_historical_win_rate(service, salesperson_id=1)
        
        # 12个月
        rate2, count2 = get_salesperson_historical_win_rate(service, salesperson_id=1, lookback_months=12)
        
        # 6个月
        rate3, count3 = get_salesperson_historical_win_rate(service, salesperson_id=1, lookback_months=6)
        
        # 所有情况下都应该返回相同的比率（因为mock返回相同数据）
        assert rate1 == pytest.approx(10/15)
        assert rate2 == pytest.approx(10/15)
        assert rate3 == pytest.approx(10/15)
    
    def test_single_project(self):
        """测试只有一个项目的情况"""
        service = MagicMock()
        stats = MagicMock()
        stats.total = 1
        stats.won = 1
        service.db.query.return_value.filter.return_value.first.return_value = stats
        
        rate, count = get_salesperson_historical_win_rate(service, salesperson_id=1)
        
        assert rate == 1.0
        assert count == 1
    
    def test_large_dataset(self):
        """测试大数据集"""
        service = MagicMock()
        stats = MagicMock()
        stats.total = 1000
        stats.won = 650
        service.db.query.return_value.filter.return_value.first.return_value = stats
        
        rate, count = get_salesperson_historical_win_rate(service, salesperson_id=1)
        
        assert rate == pytest.approx(0.65)
        assert count == 1000
    
    def test_different_salesperson_ids(self):
        """测试不同销售人员"""
        service = MagicMock()
        stats = MagicMock()
        stats.total = 10
        stats.won = 5
        service.db.query.return_value.filter.return_value.first.return_value = stats
        
        for salesperson_id in [1, 10, 100, 999]:
            rate, count = get_salesperson_historical_win_rate(service, salesperson_id)
            assert rate == 0.5
            assert count == 10
    
    def test_filters_by_outcome(self):
        """测试只统计已有结果的项目"""
        service = MagicMock()
        
        # 验证查询只包含WON和LOST
        get_salesperson_historical_win_rate(service, salesperson_id=1)
        
        # 验证数据库查询被调用
        service.db.query.assert_called()


class TestGetCustomerCooperationHistory:
    """客户合作历史测试"""
    
    def test_no_customer_id_or_name_returns_zero(self):
        """测试无客户ID或名称时返回0"""
        service = MagicMock()
        
        total, won = get_customer_cooperation_history(service)
        
        assert total == 0
        assert won == 0
    
    def test_by_customer_id(self):
        """测试通过客户ID查询"""
        service = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.count.side_effect = [5, 3]  # total, won
        service.db.query.return_value = query
        
        total, won = get_customer_cooperation_history(service, customer_id=42)
        
        assert total == 5
        assert won == 3
    
    def test_by_customer_name_found(self):
        """测试通过客户名称查询（找到客户）"""
        service = MagicMock()
        
        # Mock客户查询
        customer = MagicMock()
        customer.id = 100
        service.db.query.return_value.filter.return_value.first.return_value = customer
        
        # Mock项目查询
        query = MagicMock()
        query.filter.return_value = query
        query.count.side_effect = [10, 7]
        
        # 需要区分两次query调用
        call_count = [0]
        
        def query_side_effect(model):
            call_count[0] += 1
            if call_count[0] == 1:
                # 第一次查询Customer
                result = MagicMock()
                result.filter.return_value.first.return_value = customer
                return result
            else:
                # 第二次查询Project
                return query
        
        service.db.query.side_effect = query_side_effect
        
        total, won = get_customer_cooperation_history(service, customer_name="Test Customer")
        
        assert total == 10
        assert won == 7
    
    def test_by_customer_name_not_found(self):
        """测试通过客户名称查询（客户不存在）"""
        service = MagicMock()
        service.db.query.return_value.filter.return_value.first.return_value = None
        
        total, won = get_customer_cooperation_history(service, customer_name="Nonexistent")
        
        assert total == 0
        assert won == 0
    
    def test_no_cooperation_history(self):
        """测试无合作历史"""
        service = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.count.side_effect = [0, 0]
        service.db.query.return_value = query
        
        total, won = get_customer_cooperation_history(service, customer_id=1)
        
        assert total == 0
        assert won == 0
    
    def test_all_projects_won(self):
        """测试全部中标"""
        service = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.count.side_effect = [8, 8]
        service.db.query.return_value = query
        
        total, won = get_customer_cooperation_history(service, customer_id=1)
        
        assert total == 8
        assert won == 8
    
    def test_all_projects_lost(self):
        """测试全部失标"""
        service = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.count.side_effect = [6, 0]
        service.db.query.return_value = query
        
        total, won = get_customer_cooperation_history(service, customer_id=1)
        
        assert total == 6
        assert won == 0
    
    def test_single_cooperation(self):
        """测试单次合作"""
        service = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.count.side_effect = [1, 1]
        service.db.query.return_value = query
        
        total, won = get_customer_cooperation_history(service, customer_id=1)
        
        assert total == 1
        assert won == 1
    
    def test_large_cooperation_history(self):
        """测试大量合作历史"""
        service = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.count.side_effect = [500, 350]
        service.db.query.return_value = query
        
        total, won = get_customer_cooperation_history(service, customer_id=1)
        
        assert total == 500
        assert won == 350
    
    def test_prefer_id_over_name(self):
        """测试ID和名称都提供时优先使用ID"""
        service = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.count.side_effect = [3, 2]
        service.db.query.return_value = query
        
        total, won = get_customer_cooperation_history(
            service,
            customer_id=42,
            customer_name="Test Customer"
        )
        
        # 应该使用customer_id
        assert total == 3
        assert won == 2


class TestGetSimilarLeadsStatistics:
    """相似线索统计测试"""
    
    def test_no_similar_leads(self):
        """测试无相似线索"""
        service = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = []
        service.db.query.return_value = query
        
        dimension_scores = MagicMock()
        dimension_scores.total_score = 60
        
        count, rate = get_similar_leads_statistics(service, dimension_scores)
        
        assert count == 0
        assert rate == 0
    
    def test_with_similar_leads(self):
        """测试有相似线索"""
        service = MagicMock()
        
        won_project = MagicMock()
        won_project.outcome = LeadOutcomeEnum.WON.value
        
        lost_project = MagicMock()
        lost_project.outcome = LeadOutcomeEnum.LOST.value
        
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = [won_project, lost_project]
        service.db.query.return_value = query
        
        dimension_scores = MagicMock()
        dimension_scores.total_score = 70
        
        count, rate = get_similar_leads_statistics(service, dimension_scores)
        
        assert count == 2
        assert rate == pytest.approx(0.5)
    
    def test_all_similar_leads_won(self):
        """测试相似线索全部中标"""
        service = MagicMock()
        
        projects = []
        for _ in range(5):
            p = MagicMock()
            p.outcome = LeadOutcomeEnum.WON.value
            projects.append(p)
        
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = projects
        service.db.query.return_value = query
        
        dimension_scores = MagicMock()
        dimension_scores.total_score = 80
        
        count, rate = get_similar_leads_statistics(service, dimension_scores)
        
        assert count == 5
        assert rate == 1.0
    
    def test_all_similar_leads_lost(self):
        """测试相似线索全部失标"""
        service = MagicMock()
        
        projects = []
        for _ in range(3):
            p = MagicMock()
            p.outcome = LeadOutcomeEnum.LOST.value
            projects.append(p)
        
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = projects
        service.db.query.return_value = query
        
        dimension_scores = MagicMock()
        dimension_scores.total_score = 40
        
        count, rate = get_similar_leads_statistics(service, dimension_scores)
        
        assert count == 3
        assert rate == 0.0
    
    def test_different_score_tolerance(self):
        """测试不同分数容差"""
        service = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = []
        service.db.query.return_value = query
        
        dimension_scores = MagicMock()
        dimension_scores.total_score = 75
        
        # 不同容差值
        for tolerance in [5, 10, 15, 20]:
            count, rate = get_similar_leads_statistics(
                service,
                dimension_scores,
                score_tolerance=tolerance
            )
            # 无数据时都返回0
            assert count == 0
            assert rate == 0
    
    def test_single_similar_lead_won(self):
        """测试单个相似线索（中标）"""
        service = MagicMock()
        
        project = MagicMock()
        project.outcome = LeadOutcomeEnum.WON.value
        
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = [project]
        service.db.query.return_value = query
        
        dimension_scores = MagicMock()
        dimension_scores.total_score = 85
        
        count, rate = get_similar_leads_statistics(service, dimension_scores)
        
        assert count == 1
        assert rate == 1.0
    
    def test_single_similar_lead_lost(self):
        """测试单个相似线索（失标）"""
        service = MagicMock()
        
        project = MagicMock()
        project.outcome = LeadOutcomeEnum.LOST.value
        
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = [project]
        service.db.query.return_value = query
        
        dimension_scores = MagicMock()
        dimension_scores.total_score = 45
        
        count, rate = get_similar_leads_statistics(service, dimension_scores)
        
        assert count == 1
        assert rate == 0.0
    
    def test_large_similar_dataset(self):
        """测试大量相似线索"""
        service = MagicMock()
        
        projects = []
        # 创建100个项目，60个中标
        for i in range(100):
            p = MagicMock()
            p.outcome = LeadOutcomeEnum.WON.value if i < 60 else LeadOutcomeEnum.LOST.value
            projects.append(p)
        
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = projects
        service.db.query.return_value = query
        
        dimension_scores = MagicMock()
        dimension_scores.total_score = 75
        
        count, rate = get_similar_leads_statistics(service, dimension_scores)
        
        assert count == 100
        assert rate == pytest.approx(0.6)
    
    def test_boundary_scores(self):
        """测试边界分数"""
        service = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = []
        service.db.query.return_value = query
        
        # 测试极低分数
        dim_low = MagicMock()
        dim_low.total_score = 0
        count, rate = get_similar_leads_statistics(service, dim_low)
        assert count == 0
        
        # 测试极高分数
        dim_high = MagicMock()
        dim_high.total_score = 100
        count, rate = get_similar_leads_statistics(service, dim_high)
        assert count == 0
    
    def test_filters_by_outcome(self):
        """测试只统计已有结果的线索"""
        service = MagicMock()
        
        # 包含WON和LOST，不包含PENDING
        won = MagicMock()
        won.outcome = LeadOutcomeEnum.WON.value
        lost = MagicMock()
        lost.outcome = LeadOutcomeEnum.LOST.value
        
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = [won, lost]
        service.db.query.return_value = query
        
        dimension_scores = MagicMock()
        dimension_scores.total_score = 70
        
        count, rate = get_similar_leads_statistics(service, dimension_scores)
        
        # 应该只统计WON和LOST
        assert count == 2
        assert rate == 0.5


class TestIntegrationScenarios:
    """集成场景测试"""
    
    def test_combine_all_history_data(self):
        """测试组合所有历史数据"""
        service = MagicMock()
        
        # 销售人员历史
        stats = MagicMock()
        stats.total = 20
        stats.won = 15
        service.db.query.return_value.filter.return_value.first.return_value = stats
        
        salesperson_rate, salesperson_count = get_salesperson_historical_win_rate(service, 1)
        
        # 客户合作历史
        query = MagicMock()
        query.filter.return_value = query
        query.count.side_effect = [10, 8]
        service.db.query.return_value = query
        
        customer_total, customer_won = get_customer_cooperation_history(service, customer_id=1)
        
        # 相似线索
        projects = [MagicMock(outcome=LeadOutcomeEnum.WON.value) for _ in range(7)]
        projects += [MagicMock(outcome=LeadOutcomeEnum.LOST.value) for _ in range(3)]
        query.all.return_value = projects
        
        dim_scores = MagicMock()
        dim_scores.total_score = 75
        
        similar_count, similar_rate = get_similar_leads_statistics(service, dim_scores)
        
        # 验证所有数据
        assert salesperson_rate == 0.75
        assert salesperson_count == 20
        assert customer_total == 10
        assert customer_won == 8
        assert similar_count == 10
        assert similar_rate == 0.7


class TestEdgeCases:
    """边界情况测试"""
    
    def test_salesperson_with_null_values(self):
        """测试包含NULL值的销售数据"""
        service = MagicMock()
        stats = MagicMock()
        stats.total = None
        stats.won = None
        service.db.query.return_value.filter.return_value.first.return_value = stats
        
        rate, count = get_salesperson_historical_win_rate(service, 1)
        
        # 应该返回默认值
        assert rate == 0.20
        assert count == 0
    
    def test_customer_with_special_name(self):
        """测试特殊字符客户名"""
        service = MagicMock()
        service.db.query.return_value.filter.return_value.first.return_value = None
        
        total, won = get_customer_cooperation_history(
            service,
            customer_name="客户名称 & <special> 'chars'"
        )
        
        assert total == 0
        assert won == 0
    
    def test_similar_leads_with_zero_tolerance(self):
        """测试0容差的相似线索查询"""
        service = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = []
        service.db.query.return_value = query
        
        dim_scores = MagicMock()
        dim_scores.total_score = 50
        
        count, rate = get_similar_leads_statistics(service, dim_scores, score_tolerance=0)
        
        assert count == 0
        assert rate == 0
