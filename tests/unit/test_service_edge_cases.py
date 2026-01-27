# -*- coding: utf-8 -*-
"""
服务层边界测试

测试内容：
- 空值处理
- 异常值处理
- 边界条件
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock

import pytest

from app.models import Project
from app.services.health_calculator import HealthCalculator
from app.services.stage_advance_service import (
    get_stage_status_mapping,
    validate_stage_advancement,
    validate_target_stage,
)


@pytest.mark.unit
class TestHealthCalculatorEdgeCases:
    """健康度计算器边界测试"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def health_calculator(self, db_session):
        """创建健康度计算器实例"""
        return HealthCalculator(db_session)

    @pytest.fixture
    def mock_project(self):
        """创建模拟项目对象"""
        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PJ-TEST-001"
        project.status = "ST01"
        project.health = "H1"
        project.progress_pct = Decimal("50.00")
        project.planned_start_date = date.today() - timedelta(days=30)
        project.planned_end_date = date.today() + timedelta(days=60)
        project.actual_start_date = date.today() - timedelta(days=30)
        return project

    # ==================== 空值边界测试 ====================

    def test_calculate_health_none_project(self, health_calculator):
        """测试计算健康度 - None 项目"""
        with pytest.raises(AttributeError):
            health_calculator.calculate_health(None)

    def test_is_closed_none_status(self, health_calculator, mock_project):
        """测试判断已完结 - None 状态"""
        mock_project.status = None
        result = health_calculator._is_closed(mock_project)
        assert result is False

    def test_is_deadline_approaching_none_date(self, health_calculator, mock_project):
        """测试交期临近 - None 日期"""
        mock_project.planned_end_date = None
        result = health_calculator._is_deadline_approaching(mock_project, days=7)
        assert result is False

    def test_has_schedule_variance_none_progress(self, health_calculator, mock_project):
        """测试进度偏差 - None 进度"""
        mock_project.progress_pct = None
        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    def test_has_schedule_variance_none_end_date(self, health_calculator, mock_project):
        """测试进度偏差 - None 结束日期"""
        mock_project.planned_end_date = None
        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    # ==================== 异常值边界测试 ====================

    def test_is_deadline_approaching_past_deadline(
        self, health_calculator, mock_project
    ):
        """测试交期临近 - 过去日期"""
        mock_project.planned_end_date = date.today() - timedelta(days=1)
        result = health_calculator._is_deadline_approaching(mock_project, days=7)
        assert result is False

    def test_is_deadline_approaching_far_future(self, health_calculator, mock_project):
        """测试交期临近 - 遥远的未来"""
        mock_project.planned_end_date = date.today() + timedelta(days=365)
        result = health_calculator._is_deadline_approaching(mock_project, days=7)
        assert result is False

    def test_is_deadline_approaching_exactly_boundary(
        self, health_calculator, mock_project
    ):
        """测试交期临近 - 正好在边界上"""
        mock_project.planned_end_date = date.today() + timedelta(days=7)
        result = health_calculator._is_deadline_approaching(mock_project, days=7)
        assert result is True

    def test_has_schedule_variance_zero_progress(self, health_calculator, mock_project):
        """测试进度偏差 - 零进度"""
        mock_project.progress_pct = Decimal("0")
        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is True

    def test_has_schedule_variance_hundred_progress(
        self, health_calculator, mock_project
    ):
        """测试进度偏差 - 100% 进度"""
        mock_project.progress_pct = Decimal("100")
        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    def test_has_schedule_variance_same_day_start_end(
        self, health_calculator, mock_project
    ):
        """测试进度偏差 - 同一天开始和结束"""
        today = date.today()
        mock_project.planned_start_date = today
        mock_project.planned_end_date = today
        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    # ==================== 类型错误边界测试 ====================

    def test_calculate_health_invalid_status_type(
        self, health_calculator, mock_project
    ):
        """测试计算健康度 - 无效状态类型"""
        mock_project.status = 123
        result = health_calculator._is_closed(mock_project)
        assert result is False

    def test_calculate_health_empty_string_status(
        self, health_calculator, mock_project
    ):
        """测试计算健康度 - 空字符串状态"""
        mock_project.status = ""
        result = health_calculator._is_closed(mock_project)
        assert result is False

    def test_is_deadline_approaching_invalid_date_type(
        self, health_calculator, mock_project
    ):
        """测试交期临近 - 无效日期类型"""
        mock_project.planned_end_date = "2024-01-01"
        with pytest.raises(TypeError):
            health_calculator._is_deadline_approaching(mock_project, days=7)

            # ==================== 数据库错误边界测试 ====================

    def test_has_blocked_critical_tasks_database_error(
        self, health_calculator, mock_project, db_session
    ):
        """测试有关键任务阻塞 - 数据库错误"""
        from sqlalchemy.exc import SQLAlchemyError

        db_session.query.side_effect = SQLAlchemyError("Database error")
        with pytest.raises(SQLAlchemyError):
            health_calculator._has_blocked_critical_tasks(mock_project)

    def test_has_blocking_issues_database_error(
        self, health_calculator, mock_project, db_session
    ):
        """测试有阻塞问题 - 数据库错误"""
        from sqlalchemy.exc import SQLAlchemyError

        db_session.query.side_effect = SQLAlchemyError("Database error")
        with pytest.raises(SQLAlchemyError):
            health_calculator._has_blocking_issues(mock_project)

            # ==================== 计算精度边界测试 ====================

    def test_schedule_variance_extreme_precision(self, health_calculator, mock_project):
        """测试进度偏差 - 极端精度"""
        mock_project.progress_pct = Decimal("66.66666666666666")
        result = health_calculator._has_schedule_variance(mock_project, threshold=0.001)
        assert result is True


@pytest.mark.unit
class TestStageAdvanceServiceEdgeCases:
    """阶段推进服务边界测试"""

    # ==================== 验证目标阶段边界测试 ====================

    def test_validate_target_stage_valid_stages(self):
        """测试有效阶段编码"""
        valid_stages = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]
        for stage in valid_stages:
            validate_target_stage(stage)

    def test_validate_target_stage_invalid_empty(self):
        """测试空字符串阶段编码"""
        with pytest.raises(Exception):
            validate_target_stage("")

    def test_validate_target_stage_invalid_format(self):
        """测试无效格式的阶段编码"""
        invalid_stages = ["s1", "S01", "SA", "S0", "S10", "Stage1"]
        for stage in invalid_stages:
            with pytest.raises(Exception):
                validate_target_stage(stage)

                # ==================== 验证阶段推进边界测试 ====================

    def test_validate_stage_advancement_forward(self):
        """测试向前推进"""
        validate_stage_advancement("S1", "S2")
        validate_stage_advancement("S1", "S9")

    def test_validate_stage_advancement_backward(self):
        """测试向后推进"""
        with pytest.raises(Exception):
            validate_stage_advancement("S2", "S1")

    def test_validate_stage_advancement_same(self):
        """测试相同阶段"""
        with pytest.raises(Exception):
            validate_stage_advancement("S1", "S1")

            # ==================== 状态映射边界测试 ====================

    def test_get_stage_status_mapping_completeness(self):
        """测试状态映射完整性"""
        mapping = get_stage_status_mapping()
        expected_stages = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]
        for stage in expected_stages:
            assert stage in mapping

    def test_get_stage_status_mapping_format(self):
        """测试状态值格式"""
        mapping = get_stage_status_mapping()
        for status in mapping.values():
            assert status.startswith("ST")

    def test_get_stage_status_mapping_missing(self):
        """测试缺失阶段"""
        mapping = get_stage_status_mapping()
        assert mapping.get("S10") is None
        assert mapping.get("INVALID") is None

    # ==================== 集成边界测试 ====================

    def test_complete_validation_chain(self):
        """测试完整验证链条"""
        validate_target_stage("S2")
        validate_stage_advancement("S1", "S2")
        mapping = get_stage_status_mapping()
        assert mapping["S2"] == "ST03"

    def test_complete_workflow_extreme_jump(self):
        """测试极端跳跃"""
        validate_target_stage("S9")
        validate_stage_advancement("S1", "S9")
        mapping = get_stage_status_mapping()
        assert mapping["S9"] == "ST30"
