# -*- coding: utf-8 -*-
"""
项目利润分析服务测试 - 扩展版
目标覆盖率: 70%+
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestProfitAnalysisService:
    """项目利润分析服务测试"""

    @pytest.fixture
    def mock_db(self):
        """创建 mock 数据库会话"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        from app.services.profit_analysis_service import ProfitAnalysisService
        return ProfitAnalysisService(mock_db)

    # ======================================================================
    # 1. 毛利率分析测试 - get_margin_analysis
    # ======================================================================
    def test_get_margin_analysis_basic(self, service, mock_db):
        """测试毛利率基础计算"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(service, '_get_actual_cost', return_value=50000):
            result = service.get_margin_analysis(project_id=1)

        assert 'current_margin' in result
        assert result['contract_amount'] == 100000.0

    def test_get_margin_analysis_no_project(self, service, mock_db):
        """测试项目不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_margin_analysis(project_id=999)
        assert result == {"error": "项目不存在"}

    def test_get_margin_analysis_zero_contract(self, service, mock_db):
        """测试合同金额为0"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("0")
        mock_project.budget_amount = Decimal("80000")
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = service.get_margin_analysis(project_id=1)
        assert result.get('current_margin_rate') == 0

    def test_get_margin_analysis_healthy(self, service, mock_db):
        """测试毛利率健康状态 - healthy"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(service, '_get_actual_cost', return_value=40000):
            result = service.get_margin_analysis(project_id=1, target_margin=25.0)

        assert result['health'] == 'healthy'
        assert result['current_margin_rate'] == 60.0

    def test_get_margin_analysis_warning(self, service, mock_db):
        """测试毛利率健康状态 - warning"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(service, '_get_actual_cost', return_value=80000):
            result = service.get_margin_analysis(project_id=1, target_margin=25.0)

        assert result['health'] == 'warning'
        assert result['current_margin_rate'] == 20.0

    def test_get_margin_analysis_critical(self, service, mock_db):
        """测试毛利率健康状态 - critical"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(service, '_get_actual_cost', return_value=90000):
            result = service.get_margin_analysis(project_id=1, target_margin=25.0)

        assert result['health'] == 'critical'
        assert result['current_margin_rate'] == 10.0

    def test_get_margin_analysis_no_budget(self, service, mock_db):
        """测试无预算情况"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("0")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(service, '_get_actual_cost', return_value=50000):
            result = service.get_margin_analysis(project_id=1)

        assert result['remaining_cost'] == 0

    def test_get_margin_analysis_negative_margin(self, service, mock_db):
        """测试负毛利"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(service, '_get_actual_cost', return_value=120000):
            result = service.get_margin_analysis(project_id=1)

        assert result['current_margin'] < 0

    # ======================================================================
    # 2. 成本优化建议测试 - get_cost_optimization
    # ======================================================================
    def test_get_cost_optimization(self, service, mock_db):
        """测试成本优化建议"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_project.progress_pct = 50.0
        mock_project.project_type = "ICT"
        mock_project.product_category = "测试设备"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(service, '_get_actual_cost', return_value=50000):
            with patch.object(service, '_get_cost_by_type', return_value={}):
                result = service.get_cost_optimization(project_id=1)

        assert 'cost_by_type' in result

    def test_get_cost_optimization_no_project(self, service, mock_db):
        """测试项目不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_cost_optimization(project_id=999)
        assert result == {"error": "项目不存在"}

    def test_get_cost_optimization_budget_pace(self, service, mock_db):
        """测试预算进度超支"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_project.progress_pct = 30.0
        mock_project.project_type = "ICT"
        mock_project.product_category = "测试设备"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(service, '_get_actual_cost', return_value=40000):
            with patch.object(service, '_get_cost_by_type', return_value={}):
                result = service.get_cost_optimization(project_id=1)

        suggestions = result.get('optimization_suggestions', [])
        budget_pace = [s for s in suggestions if s.get('type') == 'budget_pace']
        assert len(budget_pace) > 0

    def test_get_cost_optimization_labor_warning(self, service, mock_db):
        """测试人工成本警告"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_project.progress_pct = 50.0
        mock_project.project_type = "ICT"
        mock_project.product_category = "测试设备"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(service, '_get_actual_cost', return_value=50000):
            with patch.object(service, '_get_cost_by_type', return_value={'labor': 50000}):
                with patch.object(service, '_get_budget_by_category', return_value=50000):
                    result = service.get_cost_optimization(project_id=1)

        suggestions = result.get('optimization_suggestions', [])
        labor_warning = [s for s in suggestions if s.get('type') == 'labor_warning']
        assert len(labor_warning) > 0

    def test_get_cost_optimization_cost_overrun(self, service, mock_db):
        """测试成本超支建议"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_project.progress_pct = 50.0
        mock_project.project_type = "ICT"
        mock_project.product_category = "测试设备"

        similar_project = MagicMock()
        similar_project.id = 2
        similar_project.contract_amount = Decimal("80000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = [similar_project]

        with patch.object(service, '_get_actual_cost', return_value=0):
            with patch.object(service, '_get_cost_by_type', return_value={'材料': 50000}):
                with patch.object(service, '_get_avg_cost_ratio', return_value={'材料': 20.0}):
                    with patch.object(service, '_get_budget_by_category', return_value=0):
                        result = service.get_cost_optimization(project_id=1)

        suggestions = result.get('optimization_suggestions', [])
        cost_overrun = [s for s in suggestions if s.get('type') == 'cost_overrun']
        assert len(cost_overrun) > 0

    # ======================================================================
    # 3. 报价偏差分析测试 - get_quote_cost_variance
    # ======================================================================
    def test_get_quote_cost_variance(self, service, mock_db):
        """测试报价偏差分析"""
        mock_project = MagicMock()
        mock_project.id = 1

        mock_query_project = MagicMock()
        mock_query_project.filter.return_value.first.return_value = mock_project

        mock_query_contract = MagicMock()
        mock_query_contract.filter.return_value.first.return_value = None

        def query_side_effect(*args):
            if args[0].__name__ == 'Project':
                return mock_query_project
            elif args[0].__name__ == 'Contract':
                return mock_query_contract
            return MagicMock()

        mock_db.query.side_effect = query_side_effect

        result = service.get_quote_cost_variance(project_id=1)
        assert isinstance(result, dict)

    def test_get_quote_cost_variance_with_quote(self, service, mock_db):
        """测试有报价的偏差分析"""
        mock_project = MagicMock()
        mock_project.id = 1

        mock_contract = MagicMock()
        mock_contract.quote_id = 1

        mock_quote_item = MagicMock()
        mock_quote_item.item_name = "测试项目"
        mock_quote_item.cost = Decimal("100")
        mock_quote_item.qty = Decimal("10")
        mock_quote_item.cost_category = "材料"

        mock_query_project = MagicMock()
        mock_query_project.filter.return_value.first.return_value = mock_project

        mock_query_contract = MagicMock()
        mock_query_contract.filter.return_value.first.return_value = mock_contract

        mock_query_items = MagicMock()
        mock_query_items.filter.return_value.all.return_value = [mock_quote_item]

        def query_side_effect(*args):
            if args[0].__name__ == 'Project':
                return mock_query_project
            elif args[0].__name__ == 'Contract':
                return mock_query_contract
            elif args[0].__name__ == 'QuoteItem':
                return mock_query_items
            return MagicMock()

        mock_db.query.side_effect = query_side_effect

        with patch.object(service, '_get_cost_by_type', return_value={'材料': 1500}):
            result = service.get_quote_cost_variance(project_id=1)

        assert result['has_quote'] == True

    # ======================================================================
    # 4. 高利润项目特征测试 - get_high_profit_patterns
    # ======================================================================
    def test_get_high_profit_patterns(self, service, mock_db):
        """测试高利润项目特征分析"""
        projects = []
        for i in range(5):
            p = MagicMock()
            p.id = i + 1
            p.project_code = f"P00{i+1}"
            p.project_name = f"项目{i+1}"
            p.contract_amount = Decimal(str(100000 + i * 10000))
            p.actual_cost = Decimal(str(30000 + i * 5000))
            p.customer_name = f"客户{i}"
            p.project_type = "ICT"
            p.product_category = "测试设备"
            p.industry = "汽车电子"
            projects.append(p)

        mock_db.query.return_value.filter.return_value.all.return_value = projects

        result = service.get_high_profit_patterns(min_margin=30.0, limit=10)

        assert 'high_profit_count' in result
        assert 'patterns' in result

    def test_extract_patterns(self, service):
        """测试特征提取"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        projects = [
            {
                "project_id": 1,
                "customer_name": "客户A",
                "product_category": "测试设备",
                "industry": "汽车电子",
                "margin_rate": 70.0
            }
        ]

        patterns = ProfitAnalysisService._extract_patterns(projects)

        assert 'customer_types' in patterns
        assert 'product_types' in patterns

    def test_extract_patterns_empty(self, service):
        """测试空项目特征提取"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        patterns = ProfitAnalysisService._extract_patterns([])

        assert patterns['customer_types'] == []
        assert patterns['product_types'] == []

    # ======================================================================
    # 5. 低利润项目根因分析 - get_low_profit_root_cause
    # ======================================================================
    def test_get_low_profit_root_cause(self, service, mock_db):
        """测试低利润项目根因分析"""
        p = MagicMock()
        p.id = 1
        p.project_code = "P001"
        p.project_name = "项目1"
        p.customer_name = "客户A"
        p.project_type = "ICT"
        p.contract_amount = Decimal("100000")
        p.budget_amount = Decimal("70000")
        p.actual_cost = Decimal("90000")

        mock_db.query.return_value.filter.return_value.all.return_value = [p]

        result = service.get_low_profit_root_cause(max_margin=10.0, limit=10)

        assert 'total_low_profit' in result

    def test_get_low_profit_root_cause_cost_higher(self, service, mock_db):
        """测试成本倒挂"""
        p = MagicMock()
        p.id = 1
        p.project_code = "P001"
        p.project_name = "项目1"
        p.customer_name = "客户A"
        p.project_type = "ICT"
        p.contract_amount = Decimal("80000")
        p.budget_amount = Decimal("90000")
        p.actual_cost = Decimal("100000")

        mock_db.query.return_value.filter.return_value.all.return_value = [p]

        result = service.get_low_profit_root_cause(max_margin=10.0, limit=10)

        assert result['total_low_profit'] > 0

    # ======================================================================
    # 6. 综合利润分析 - get_profit_analysis
    # ======================================================================
    def test_get_profit_analysis(self, service, mock_db):
        """测试综合利润分析"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(service, '_get_actual_cost', return_value=50000):
            with patch.object(service, 'get_cost_optimization', return_value={'optimization_suggestions': []}):
                with patch.object(service, 'get_quote_cost_variance', return_value={'has_quote': False}):
                    result = service.get_profit_analysis(project_id=1)

        assert 'current_margin' in result

    def test_get_profit_analysis_error(self, service, mock_db):
        """测试项目不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_profit_analysis(project_id=999)
        assert result == {"error": "项目不存在"}

    # ======================================================================
    # 7. 内部辅助方法
    # ======================================================================
    def test_get_actual_cost(self, service, mock_db):
        """测试获取实际成本"""
        call_count = [0]
        
        def query_side_effect(*args):
            call_count[0] += 1
            mock_q = MagicMock()
            mock_q.filter.return_value.scalar.return_value = 25000
            return mock_q
        
        mock_db.query.side_effect = query_side_effect

        result = service._get_actual_cost(1)
        assert result == 50000.0

    def test_get_actual_cost_empty(self, service, mock_db):
        """测试无成本"""
        call_count = [0]
        
        def query_side_effect(*args):
            call_count[0] += 1
            mock_q = MagicMock()
            mock_q.filter.return_value.scalar.return_value = None
            return mock_q
        
        mock_db.query.side_effect = query_side_effect

        result = service._get_actual_cost(1)
        assert result == 0.0

    def test_get_cost_by_type(self, service, mock_db):
        """测试按类型获取成本"""
        mock_result = [('材料', 30000), ('人工', 20000)]
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = mock_result

        result = service._get_cost_by_type(1)

        assert '材料' in result
        assert '人工' in result

    def test_get_avg_cost_ratio(self, service, mock_db):
        """测试平均成本占比"""
        mock_project = MagicMock()
        mock_project.contract_amount = Decimal("100000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ('材料', 30000)
        ]

        result = service._get_avg_cost_ratio([1, 2])
        assert isinstance(result, dict)

    def test_get_budget_by_category(self, service, mock_db):
        """测试获取特定类别预算"""
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 50000

        result = service._get_budget_by_category(1, "LABOR")
        assert result == 50000.0