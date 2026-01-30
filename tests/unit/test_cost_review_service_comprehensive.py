# -*- coding: utf-8 -*-
"""
CostReviewService 综合单元测试

测试覆盖:
- generate_cost_review_report: 自动生成项目成本复盘报告
- _generate_review_no: 生成复盘编号
- _generate_cost_summary: 生成成本分析总结
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestGenerateCostReviewReport:
    """测试 generate_cost_review_report 方法"""

    def test_raises_error_when_project_not_found(self):
        """测试项目不存在时抛出异常"""
        from app.services.cost_review_service import CostReviewService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="项目不存在"):
            CostReviewService.generate_cost_review_report(mock_db, 1, 10)

    def test_raises_error_when_project_not_closed(self):
        """测试项目未结项时抛出异常"""
        from app.services.cost_review_service import CostReviewService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.stage = "S5"
        mock_project.status = "ST20"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with pytest.raises(ValueError, match="项目未结项"):
            CostReviewService.generate_cost_review_report(mock_db, 1, 10)

    def test_raises_error_when_review_exists(self):
        """测试复盘报告已存在时抛出异常"""
        from app.services.cost_review_service import CostReviewService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.stage = "S9"
        mock_project.status = "ST30"

        mock_existing_review = MagicMock()

        # First call returns project, second returns existing review
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project, mock_existing_review
        ]

        with pytest.raises(ValueError, match="已存在结项复盘报告"):
            CostReviewService.generate_cost_review_report(mock_db, 1, 10)

    def test_creates_review_report(self):
        """测试创建复盘报告"""
        from app.services.cost_review_service import CostReviewService

        mock_db = MagicMock()

        # Mock project
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.stage = "S9"
        mock_project.status = "ST30"
        mock_project.planned_start_date = date(2025, 1, 1)
        mock_project.planned_end_date = date(2025, 6, 30)
        mock_project.actual_start_date = date(2025, 1, 15)
        mock_project.actual_end_date = date(2025, 7, 15)
        mock_project.budget_amount = Decimal("100000")
        mock_project.actual_cost = Decimal("110000")

        # Mock reviewer
        mock_reviewer = MagicMock()
        mock_reviewer.real_name = "张三"
        mock_reviewer.username = "zhangsan"

        # Setup query chain
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
            elif model.__name__ == 'ProjectReview':
                # For existing review check
                query_mock.filter.return_value.first.return_value = None
                # For generate_review_no
                query_mock.filter.return_value.order_by.return_value.first.return_value = None
            elif model.__name__ == 'ProjectBudget':
                query_mock.filter.return_value.order_by.return_value.first.return_value = None
            elif model.__name__ == 'ProjectCost':
                query_mock.filter.return_value.all.return_value = []
            elif model.__name__ == 'Ecn':
                query_mock.filter.return_value.count.return_value = 2
            elif model.__name__ == 'User':
                query_mock.filter.return_value.first.return_value = mock_reviewer
            return query_mock

        mock_db.query.side_effect = query_side_effect

        result = CostReviewService.generate_cost_review_report(mock_db, 1, 10)

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert result.project_id == 1
        assert result.reviewer_name == "张三"

    def test_calculates_schedule_variance(self):
        """测试计算进度偏差"""
        from app.services.cost_review_service import CostReviewService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.stage = "S9"
        mock_project.status = "ST30"
        mock_project.planned_start_date = date(2025, 1, 1)
        mock_project.planned_end_date = date(2025, 3, 31)  # 89天
        mock_project.actual_start_date = date(2025, 1, 1)
        mock_project.actual_end_date = date(2025, 4, 30)  # 119天
        mock_project.budget_amount = Decimal("100000")
        mock_project.actual_cost = None

        mock_reviewer = MagicMock()
        mock_reviewer.real_name = "测试员"

        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
            elif model.__name__ == 'ProjectReview':
                query_mock.filter.return_value.first.return_value = None
                query_mock.filter.return_value.order_by.return_value.first.return_value = None
            elif model.__name__ == 'ProjectBudget':
                query_mock.filter.return_value.order_by.return_value.first.return_value = None
            elif model.__name__ == 'ProjectCost':
                query_mock.filter.return_value.all.return_value = []
            elif model.__name__ == 'Ecn':
                query_mock.filter.return_value.count.return_value = 0
            elif model.__name__ == 'User':
                query_mock.filter.return_value.first.return_value = mock_reviewer
            return query_mock

        mock_db.query.side_effect = query_side_effect

        result = CostReviewService.generate_cost_review_report(mock_db, 1, 10)

        assert result.plan_duration == 89
        assert result.actual_duration == 119
        assert result.schedule_variance == 30  # 延期30天


class TestGenerateReviewNo:
    """测试 _generate_review_no 方法"""

    def test_generates_first_review_no(self):
        """测试生成第一个复盘编号"""
        from app.services.cost_review_service import CostReviewService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = CostReviewService._generate_review_no(mock_db)

        today = datetime.now().strftime("%y%m%d")
        assert result == f"REV-{today}-001"

    def test_increments_sequence_number(self):
        """测试递增序号"""
        from app.services.cost_review_service import CostReviewService

        mock_db = MagicMock()
        mock_existing = MagicMock()
        today = datetime.now().strftime("%y%m%d")
        mock_existing.review_no = f"REV-{today}-005"

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_existing

        result = CostReviewService._generate_review_no(mock_db)

        assert result == f"REV-{today}-006"


class TestGenerateCostSummary:
    """测试 _generate_cost_summary 方法"""

    def test_generates_severe_overrun_summary(self):
        """测试生成严重超支总结"""
        from app.services.cost_review_service import CostReviewService

        result = CostReviewService._generate_cost_summary(
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("115000"),
            cost_variance=Decimal("15000"),
            cost_by_type={"材料": Decimal("80000"), "人工": Decimal("35000")},
            cost_by_category={},
            ecn_count=3
        )

        assert "严重超支" in result
        assert "15.0%" in result

    def test_generates_moderate_overrun_summary(self):
        """测试生成中度超支总结"""
        from app.services.cost_review_service import CostReviewService

        result = CostReviewService._generate_cost_summary(
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("108000"),
            cost_variance=Decimal("8000"),
            cost_by_type={},
            cost_by_category={},
            ecn_count=0
        )

        assert "需要关注" in result

    def test_generates_under_budget_summary(self):
        """测试生成低于预算总结"""
        from app.services.cost_review_service import CostReviewService

        result = CostReviewService._generate_cost_summary(
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("90000"),
            cost_variance=Decimal("-10000"),
            cost_by_type={},
            cost_by_category={},
            ecn_count=0
        )

        assert "成本控制良好" in result

    def test_generates_on_budget_summary(self):
        """测试生成与预算一致总结"""
        from app.services.cost_review_service import CostReviewService

        result = CostReviewService._generate_cost_summary(
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("102000"),
            cost_variance=Decimal("2000"),
            cost_by_type={},
            cost_by_category={},
            ecn_count=0
        )

        assert "与预算基本一致" in result

    def test_includes_cost_breakdown(self):
        """测试包含成本构成"""
        from app.services.cost_review_service import CostReviewService

        result = CostReviewService._generate_cost_summary(
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("100000"),
            cost_variance=Decimal("0"),
            cost_by_type={
                "材料": Decimal("60000"),
                "人工": Decimal("30000"),
                "其他": Decimal("10000")
            },
            cost_by_category={},
            ecn_count=0
        )

        assert "成本构成" in result
        assert "材料" in result
        assert "人工" in result

    def test_includes_ecn_info(self):
        """测试包含变更信息"""
        from app.services.cost_review_service import CostReviewService

        result = CostReviewService._generate_cost_summary(
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("100000"),
            cost_variance=Decimal("0"),
            cost_by_type={},
            cost_by_category={},
            ecn_count=5
        )

        assert "5次工程变更" in result

    def test_handles_zero_budget(self):
        """测试处理零预算"""
        from app.services.cost_review_service import CostReviewService

        result = CostReviewService._generate_cost_summary(
            budget_amount=Decimal("0"),
            actual_cost=Decimal("50000"),
            cost_variance=Decimal("50000"),
            cost_by_type={},
            cost_by_category={},
            ecn_count=0
        )

        # Should handle division by zero gracefully
        assert result is not None

    def test_handles_zero_actual_cost(self):
        """测试处理零实际成本"""
        from app.services.cost_review_service import CostReviewService

        result = CostReviewService._generate_cost_summary(
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("0"),
            cost_variance=Decimal("-100000"),
            cost_by_type={"材料": Decimal("0")},
            cost_by_category={},
            ecn_count=0
        )

        assert result is not None

    def test_sorts_cost_types_by_amount(self):
        """测试按金额排序成本类型"""
        from app.services.cost_review_service import CostReviewService

        result = CostReviewService._generate_cost_summary(
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("100000"),
            cost_variance=Decimal("0"),
            cost_by_type={
                "其他": Decimal("10000"),
                "材料": Decimal("60000"),
                "人工": Decimal("30000")
            },
            cost_by_category={},
            ecn_count=0
        )

        # 材料应该排在第一位因为金额最高
        material_pos = result.find("材料")
        labor_pos = result.find("人工")
        other_pos = result.find("其他")

        assert material_pos < labor_pos < other_pos
