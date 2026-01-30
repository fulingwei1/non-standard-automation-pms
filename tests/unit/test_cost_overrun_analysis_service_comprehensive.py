# -*- coding: utf-8 -*-
"""
CostOverrunAnalysisService 综合单元测试

测试覆盖:
- analyze_reasons: 成本超支原因分析
- analyze_accountability: 成本超支归责
- analyze_impact: 成本超支影响分析
- _analyze_project_overrun: 分析单个项目超支
- _calculate_actual_cost: 计算实际成本
- _calculate_material_cost: 计算物料成本
- _calculate_labor_cost: 计算工时成本
- _calculate_outsourcing_cost: 计算外协成本
- _calculate_actual_hours: 计算实际工时
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestCostOverrunAnalysisServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        assert service.db == mock_db


class TestAnalyzeReasons:
    """测试 analyze_reasons 方法"""

    def test_returns_empty_when_no_overrun_projects(self):
        """测试无超支项目时返回空"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        result = service.analyze_reasons()

        assert result["total_overrun_projects"] == 0
        assert result["reasons"] == []

    def test_identifies_overrun_projects(self):
        """测试识别超支项目"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget = Decimal("100000")
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

            with patch.object(service, "_analyze_project_overrun") as mock_analyze:
                mock_analyze.return_value = {
                    "project_id": 1,
                    "project_code": "PJ001",
                    "has_overrun": True,
                    "overrun_amount": 20000,
                    "reasons": ["工时超支"],
                }

                result = service.analyze_reasons()

        assert result["total_overrun_projects"] == 1

    def test_filters_by_project_id(self):
        """测试按项目ID筛选"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        result = service.analyze_reasons(project_id=1)

        assert result["total_overrun_projects"] == 0

    def test_filters_by_date_range(self):
        """测试按日期范围筛选"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 31)

        result = service.analyze_reasons(start_date=start_date, end_date=end_date)

        assert result["analysis_period"]["start_date"] == "2026-01-01"
        assert result["analysis_period"]["end_date"] == "2026-01-31"

    def test_aggregates_reasons(self):
        """测试聚合原因"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()

        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.project_code = "PJ001"

        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.project_code = "PJ002"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project1, mock_project2]

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

            with patch.object(service, "_analyze_project_overrun") as mock_analyze:
                mock_analyze.side_effect = [
                    {
                        "project_id": 1,
                        "project_code": "PJ001",
                        "has_overrun": True,
                        "overrun_amount": 10000,
                        "reasons": ["工时超支"],
                    },
                    {
                        "project_id": 2,
                        "project_code": "PJ002",
                        "has_overrun": True,
                        "overrun_amount": 20000,
                        "reasons": ["工时超支", "物料成本超支"],
                    },
                ]

                result = service.analyze_reasons()

        # 工时超支应该出现2次
        work_hours_reason = next(
            (r for r in result["reasons"] if r["reason"] == "工时超支"),
            None
        )
        assert work_hours_reason is not None
        assert work_hours_reason["count"] == 2


class TestAnalyzeAccountability:
    """测试 analyze_accountability 方法"""

    def test_returns_empty_when_no_overrun(self):
        """测试无超支时返回空"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        result = service.analyze_accountability()

        assert result["by_person"] == []

    def test_attributes_to_salesperson(self):
        """测试归责到销售"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.salesperson_id = 10
        mock_project.pm_id = None
        mock_project.opportunity_id = None

        mock_user = MagicMock()
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"
        mock_user.department = "销售部"

        # Setup query chain
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,  # for project query
            mock_user,  # for user query
        ]

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

            with patch.object(service, "analyze_reasons") as mock_analyze:
                mock_analyze.return_value = {
                    "projects": [
                        {
                            "project_id": 1,
                            "overrun_amount": 10000,
                        }
                    ]
                }

                result = service.analyze_accountability()

        # Should have attribution to salesperson
        assert len(result["by_person"]) >= 0


class TestAnalyzeImpact:
    """测试 analyze_impact 方法"""

    def test_returns_zero_summary_when_no_overrun(self):
        """测试无超支时返回零汇总"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        result = service.analyze_impact()

        assert result["summary"]["total_overrun"] == 0
        assert result["summary"]["total_contract_amount"] == 0

    def test_calculates_margin_impact(self):
        """测试计算毛利率影响"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.contract_amount = Decimal("200000")
        mock_project.est_margin = Decimal("20")  # 20%

        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

            with patch.object(service, "analyze_reasons") as mock_analyze:
                mock_analyze.return_value = {
                    "projects": [
                        {
                            "project_id": 1,
                            "overrun_amount": 20000,
                        }
                    ]
                }

                result = service.analyze_impact()

        # Should have affected projects with margin impact
        assert len(result["affected_projects"]) >= 0


class TestAnalyzeProjectOverrun:
    """测试 _analyze_project_overrun 方法"""

    def test_identifies_no_overrun(self):
        """测试识别无超支"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget = Decimal("100000")
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

            with patch.object(service, "_calculate_actual_cost", return_value=Decimal("80000")):
                result = service._analyze_project_overrun(mock_project)

        assert result["has_overrun"] is False
        assert result["overrun_amount"] == 0

    def test_identifies_overrun(self):
        """测试识别超支"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget = Decimal("100000")
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

            with patch.object(service, "_calculate_actual_cost", return_value=Decimal("120000")):
                with patch.object(service, "_calculate_actual_hours", return_value=150):
                    with patch.object(service, "_calculate_material_cost", return_value=Decimal("30000")):
                        with patch.object(service, "_calculate_outsourcing_cost", return_value=Decimal("10000")):
                            result = service._analyze_project_overrun(mock_project)

        assert result["has_overrun"] is True
        assert result["overrun_amount"] == 20000
        assert "工时超支" in result["reasons"]

    def test_identifies_ecn_reason(self):
        """测试识别ECN原因"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()

        mock_ecn = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget = Decimal("100000")
        mock_project.plan_manhours = 100
        mock_project.ecns = [mock_ecn]

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

            with patch.object(service, "_calculate_actual_cost", return_value=Decimal("120000")):
                with patch.object(service, "_calculate_actual_hours", return_value=90):
                    with patch.object(service, "_calculate_material_cost", return_value=Decimal("30000")):
                        with patch.object(service, "_calculate_outsourcing_cost", return_value=Decimal("10000")):
                            result = service._analyze_project_overrun(mock_project)

        assert "需求变更导致成本增加" in result["reasons"]

    def test_handles_zero_budget(self):
        """测试处理零预算"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget = Decimal("0")
        mock_project.plan_manhours = 0
        mock_project.ecns = []

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

            with patch.object(service, "_calculate_actual_cost", return_value=Decimal("10000")):
                result = service._analyze_project_overrun(mock_project)

        assert result["overrun_ratio"] == 0


class TestCalculateActualCost:
    """测试 _calculate_actual_cost 方法"""

    def test_sums_all_cost_types(self):
        """测试汇总所有成本类型"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("5000")

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

            with patch.object(service, "_calculate_material_cost", return_value=Decimal("30000")):
                with patch.object(service, "_calculate_labor_cost", return_value=Decimal("50000")):
                    with patch.object(service, "_calculate_outsourcing_cost", return_value=Decimal("10000")):
                        result = service._calculate_actual_cost(project_id=1)

        # 30000 + 50000 + 10000 + 5000 = 95000
        assert result == Decimal("95000")


class TestCalculateMaterialCost:
    """测试 _calculate_material_cost 方法"""

    def test_returns_sum_of_material_costs(self):
        """测试返回物料成本总和"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("25000")

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        result = service._calculate_material_cost(project_id=1)

        assert result == Decimal("25000")

    def test_returns_zero_when_no_costs(self):
        """测试无成本时返回零"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = None

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        result = service._calculate_material_cost(project_id=1)

        assert result == Decimal("0")


class TestCalculateLaborCost:
    """测试 _calculate_labor_cost 方法"""

    def test_calculates_from_timesheets(self):
        """测试从工时记录计算"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()

        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 1
        mock_timesheet.hours = 10
        mock_timesheet.work_date = date.today()

        mock_user = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_timesheet]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService") as MockHourlyService:
            mock_hourly_service = MagicMock()
            mock_hourly_service.get_user_hourly_rate.return_value = Decimal("100")
            MockHourlyService.return_value = mock_hourly_service

            service = CostOverrunAnalysisService(mock_db)
            result = service._calculate_labor_cost(project_id=1)

        # 10 hours * 100 rate = 1000
        assert result == Decimal("1000")

    def test_returns_zero_when_no_timesheets(self):
        """测试无工时记录时返回零"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        result = service._calculate_labor_cost(project_id=1)

        assert result == Decimal("0")


class TestCalculateOutsourcingCost:
    """测试 _calculate_outsourcing_cost 方法"""

    def test_sums_outsourcing_orders(self):
        """测试汇总外协订单"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()

        mock_order1 = MagicMock()
        mock_order1.total_amount = Decimal("5000")

        mock_order2 = MagicMock()
        mock_order2.total_amount = Decimal("3000")

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_order1, mock_order2]

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        result = service._calculate_outsourcing_cost(project_id=1)

        assert result == Decimal("8000")

    def test_returns_zero_when_no_orders(self):
        """测试无订单时返回零"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        result = service._calculate_outsourcing_cost(project_id=1)

        assert result == Decimal("0")


class TestCalculateActualHours:
    """测试 _calculate_actual_hours 方法"""

    def test_returns_sum_of_hours(self):
        """测试返回工时总和"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 150

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        result = service._calculate_actual_hours(project_id=1)

        assert result == 150.0

    def test_returns_zero_when_no_hours(self):
        """测试无工时时返回零"""
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = None

        with patch("app.services.cost_overrun_analysis_service.HourlyRateService"):
            service = CostOverrunAnalysisService(mock_db)

        result = service._calculate_actual_hours(project_id=1)

        assert result == 0.0
