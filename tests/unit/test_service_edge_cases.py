# -*- coding: utf-8 -*-
"""
服务层边界测试

测试内容：
- 空值处理
- 异常值处理
- 边界条件
- 类型错误处理
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models.project import Project
from app.services.health_calculator import HealthCalculator
from app.services.stage_advance_service import (
    get_stage_status_mapping,
    perform_gate_check,
    update_project_stage_and_status,
    validate_stage_advancement,
    validate_target_stage,
)


@pytest.mark.unit
class TestHealthCalculatorEdgeCases:
    """健康度计算器边界测试"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        mock_session = MagicMock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_session.query.return_value = mock_query
        return mock_session

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
        project.project_name = "测试项目"
        project.status = "ST01"
        project.stage = "S1"
        project.health = "H1"
        project.progress_pct = Decimal("50.00")
        project.planned_start_date = date.today() - timedelta(days=30)
        project.planned_end_date = date.today() + timedelta(days=60)
        project.actual_start_date = date.today() - timedelta(days=30)
        project.is_active = True
        project.is_archived = False
        return project

    def _setup_db_query_mock(self, db_session, return_value=0):
        """设置数据库查询 mock"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = return_value
        db_session.query.return_value = mock_query
        return mock_query

    # ==================== 空值边界测试 ====================

    def test_calculate_health_none_project(self, health_calculator):
        """测试计算健康度 - None 项目"""
        with pytest.raises(AttributeError):
            health_calculator.calculate_health(None)

    def test_calculate_health_missing_status(self, health_calculator, mock_project):
        """测试计算健康度 - 缺少 status 属性"""
        del mock_project.status
        with pytest.raises(AttributeError):
            health_calculator.calculate_health(mock_project)

    def test_is_closed_none_status(self, health_calculator, mock_project):
        """测试判断已完结 - None 状态"""
        mock_project.status = None
        result = health_calculator._is_closed(mock_project)
        assert result is False

    def test_is_blocked_none_status(self, health_calculator, mock_project, db_session):
        """测试判断阻塞 - None 状态"""
        mock_project.status = None
        self._setup_db_query_mock(db_session, 0)
        result = health_calculator._is_blocked(mock_project)
        assert result is False

    def test_has_risks_none_status(self, health_calculator, mock_project, db_session):
        """测试有风险 - None 状态"""
        mock_project.status = None
        self._setup_db_query_mock(db_session, 0)
        result = health_calculator._has_risks(mock_project)
        assert result is False

    def test_is_deadline_approaching_none_date(self, health_calculator, mock_project):
        """测试交期临近 - None 日期"""
        mock_project.planned_end_date = None
        result = health_calculator._is_deadline_approaching(mock_project, days=7)
        assert result is False

    def test_has_schedule_variance_none_progress(self, health_calculator, mock_project):
        """测试进度偏差 - None 进度"""
        mock_project.planned_start_date = date.today() - timedelta(days=30)
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = date.today() - timedelta(days=30)
        mock_project.progress_pct = None
        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    def test_has_schedule_variance_none_start_date(
        self, health_calculator, mock_project
    ):
        """测试进度偏差 - None 开始日期"""
        mock_project.planned_start_date = None
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = date.today()
        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    def test_has_schedule_variance_none_end_date(self, health_calculator, mock_project):
        """测试进度偏差 - None 结束日期"""
        mock_project.planned_start_date = date.today() - timedelta(days=30)
        mock_project.planned_end_date = None
        mock_project.actual_start_date = date.today() - timedelta(days=30)
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
        mock_project.planned_start_date = date.today() - timedelta(days=60)
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = date.today() - timedelta(days=60)
        mock_project.progress_pct = Decimal("0")
        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is True

    def test_has_schedule_variance_hundred_progress(
        self, health_calculator, mock_project
    ):
        """测试进度偏差 - 100% 进度"""
        mock_project.planned_start_date = date.today() - timedelta(days=60)
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = date.today() - timedelta(days=60)
        mock_project.progress_pct = Decimal("100")
        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    def test_has_schedule_variance_negative_threshold(
        self, health_calculator, mock_project
    ):
        """测试进度偏差 - 负阈值"""
        mock_project.planned_start_date = date.today() - timedelta(days=60)
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = date.today() - timedelta(days=60)
        mock_project.progress_pct = Decimal("50")
        result = health_calculator._has_schedule_variance(mock_project, threshold=-10)
        assert result is True

    def test_has_schedule_variance_zero_threshold(
        self, health_calculator, mock_project
    ):
        """测试进度偏差 - 零阈值"""
        mock_project.planned_start_date = date.today() - timedelta(days=60)
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = date.today() - timedelta(days=60)
        mock_project.progress_pct = Decimal("66.67")
        result = health_calculator._has_schedule_variance(mock_project, threshold=0)
        assert result is False

    def test_has_schedule_variance_same_day_start_end(
        self, health_calculator, mock_project
    ):
        """测试进度偏差 - 同一天开始和结束"""
        today = date.today()
        mock_project.planned_start_date = today
        mock_project.planned_end_date = today
        mock_project.actual_start_date = today
        mock_project.progress_pct = Decimal("50")
        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    def test_has_schedule_variance_future_start_date(
        self, health_calculator, mock_project
    ):
        """测试进度偏差 - 开始日期在将来"""
        future_date = date.today() + timedelta(days=30)
        mock_project.planned_start_date = future_date
        mock_project.planned_end_date = future_date + timedelta(days=60)
        mock_project.actual_start_date = None
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

    def test_calculate_health_whitespace_status(self, health_calculator, mock_project):
        """测试计算健康度 - 空白字符串状态"""
        mock_project.status = "  "
        result = health_calculator._is_closed(mock_project)
        assert result is False

    def test_is_deadline_approaching_invalid_date_type(
        self, health_calculator, mock_project
    ):
        """测试交期临近 - 无效日期类型"""
        mock_project.planned_end_date = "2024-01-01"
        with pytest.raises(TypeError):
            health_calculator._is_deadline_approaching(mock_project, days=7)

    def test_has_schedule_variance_invalid_progress_type(
        self, health_calculator, mock_project
    ):
        """测试进度偏差 - 无效进度类型"""
        mock_project.planned_start_date = date.today() - timedelta(days=30)
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = date.today() - timedelta(days=30)
        mock_project.progress_pct = "50"
        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert isinstance(result, bool)

    def test_has_schedule_variance_string_decimal(
        self, health_calculator, mock_project
    ):
        """测试进度偏差 - 字符串 Decimal"""
        mock_project.planned_start_date = date.today() - timedelta(days=30)
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = date.today() - timedelta(days=30)
        mock_project.progress_pct = "50.00"
        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert isinstance(result, bool)

    # ==================== 特殊数据库查询边界测试 ====================

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

    def test_has_overdue_milestones_database_error(
        self, health_calculator, mock_project, db_session
    ):
        """测试有逾期里程碑 - 数据库错误"""
        from sqlalchemy.exc import SQLAlchemyError

        db_session.query.side_effect = SQLAlchemyError("Database error")
        with pytest.raises(SQLAlchemyError):
            health_calculator._has_overdue_milestones(mock_project)

    def test_has_critical_shortage_alerts_database_error(
        self, health_calculator, mock_project, db_session
    ):
        """测试有严重缺料预警 - 数据库错误"""
        from sqlalchemy.exc import SQLAlchemyError

        db_session.query.side_effect = SQLAlchemyError("Database error")
        with pytest.raises(SQLAlchemyError):
            health_calculator._has_critical_shortage_alerts(mock_project)

    def test_has_high_priority_issues_database_error(
        self, health_calculator, mock_project, db_session
    ):
        """测试有高优先级问题 - 数据库错误"""
        from sqlalchemy.exc import SQLAlchemyError

        db_session.query.side_effect = SQLAlchemyError("Database error")
        with pytest.raises(SQLAlchemyError):
            health_calculator._has_high_priority_issues(mock_project)

    # ==================== 计算精度边界测试 ====================

    def test_schedule_variance_extreme_precision(self, health_calculator, mock_project):
        """测试进度偏差 - 极端精度"""
        mock_project.planned_start_date = date.today() - timedelta(days=100)
        mock_project.planned_end_date = date.today()
        mock_project.actual_start_date = date.today() - timedelta(days=100)
        mock_project.progress_pct = Decimal("66.66666666666666")
        result = health_calculator._has_schedule_variance(mock_project, threshold=0.001)
        assert result is True

    def test_batch_calculate_empty_list(self, health_calculator, db_session):
        """测试批量计算 - 空项目列表"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        db_session.query.return_value = mock_query

        result = health_calculator.batch_calculate(project_ids=[], batch_size=100)
        assert result["total"] == 0
        assert result["updated"] == 0
        assert result["unchanged"] == 0

    def test_batch_calculate_very_large_batch_size(self, health_calculator, db_session):
        """测试批量计算 - 极大的批次大小"""
        project = Mock(spec=Project)
        project.id = 1
        project.is_active = True
        project.is_archived = False
        project.health = "H1"

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [project]
        db_session.query.return_value = mock_query

        with patch.object(health_calculator, "calculate_and_update") as mock_calc:
            mock_calc.return_value = {"project_id": 1, "changed": False}

            result = health_calculator.batch_calculate(
                project_ids=None, batch_size=999999
            )

        assert result["total"] == 1


@pytest.mark.unit
class TestStageAdvanceServiceEdgeCases:
    """阶段推进服务边界测试"""

    # ==================== 验证目标阶段边界测试 ====================

    def test_validate_target_stage_unicode_characters(self):
        """测试验证目标阶段 - Unicode 字符"""
        with pytest.raises(Exception):
            validate_target_stage("S1中文")

    def test_validate_target_stage_very_long_string(self):
        """测试验证目标阶段 - 很长的字符串"""
        with pytest.raises(Exception):
            validate_target_stage("S1" * 100)

    def test_validate_target_stage_special_characters(self):
        """测试验证目标阶段 - 特殊字符"""
        invalid_stages = ["S1!", "S1@", "S1#", "S1$", "S1%", "S1^", "S1&", "S1*"]
        for stage in invalid_stages:
            with pytest.raises(Exception):
                validate_target_stage(stage)

    def test_validate_target_stage_whitespace(self):
        """测试验证目标阶段 - 空白字符"""
        with pytest.raises(Exception):
            validate_target_stage(" S1")
        with pytest.raises(Exception):
            validate_target_stage("S1 ")
        with pytest.raises(Exception):
            validate_target_stage(" S 1 ")

    def test_validate_target_stage_tab_character(self):
        """测试验证目标阶段 - 制表符"""
        with pytest.raises(Exception):
            validate_target_stage("S\t1")

    def test_validate_target_stage_newline_character(self):
        """测试验证目标阶段 - 换行符"""
        with pytest.raises(Exception):
            validate_target_stage("S\n1")

    # ==================== 验证阶段推进边界测试 ====================

    def test_validate_stage_advancement_number_suffix(self):
        """测试验证阶段推进 - 数字后缀"""
        validate_stage_advancement("S1", "S2")
        validate_stage_advancement("S1", "S9")

    def test_validate_stage_advancement_float_like(self):
        """测试验证阶段推进 - 浮点数-like"""
        validate_stage_advancement("S1", "S2")
        validate_stage_advancement("S1", "S9")

    def test_validate_stage_advancement_negative_number(self):
        """测试验证阶段推进 - 负数"""
        with pytest.raises(Exception):
            validate_stage_advancement("S1", "S-1")

    def test_validate_stage_advancement_zero_prefix(self):
        """测试验证阶段推进 - 前导零"""
        with pytest.raises(Exception):
            validate_stage_advancement("S01", "S02")

    def test_validate_stage_advancement_very_large_number(self):
        """测试验证阶段推进 - 非常大的数字"""
        with pytest.raises(Exception):
            validate_stage_advancement("S1", "S999999")

    def test_validate_stage_advancement_leading_space(self):
        """测试验证阶段推进 - 前导空格"""
        with pytest.raises(Exception):
            validate_stage_advancement(" S1", " S2")

    def test_validate_stage_advancement_trailing_space(self):
        """测试验证阶段推进 - 尾随空格"""
        with pytest.raises(Exception):
            validate_stage_advancement("S1 ", "S2 ")

    # ==================== 状态映射边界测试 ====================

    def test_get_stage_status_mapping_missing_stage(self):
        """测试状态映射 - 缺失的阶段"""
        mapping = get_stage_status_mapping()
        assert mapping.get("S10") is None
        assert mapping.get("S0") is None
        assert mapping.get("INVALID") is None

    def test_get_stage_status_mapping_modify_protection(self):
        """测试状态映射 - 修改保护"""
        mapping = get_stage_status_mapping()
        original_s1 = mapping["S1"]
        mapping["S1"] = "MODIFIED"
        new_mapping = get_stage_status_mapping()
        assert new_mapping["S1"] == original_s1

    def test_get_stage_status_mapping_case_sensitive(self):
        """测试状态映射 - 大小写敏感"""
        mapping = get_stage_status_mapping()
        assert mapping.get("s1") is None
        assert mapping.get("S1") is not None

    # ==================== 更新项目阶段和状态边界测试 ====================

    def test_update_project_stage_and_status_none_status_mapping(self, db_session):
        """测试更新项目阶段和状态 - None 状态映射"""

        project = Project(
            project_code="PJ-TEST-EDGE",
            project_name="边界测试项目",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        with patch(
            "app.services.stage_advance_service.get_stage_status_mapping"
        ) as mock_mapping:
            mock_mapping.return_value = {}
            new_status = update_project_stage_and_status(
                db_session, project, "S2", "S1", "ST01"
            )
            assert new_status == "ST01"

        db_session.rollback()

    def test_update_project_stage_and_status_unicode_stage(self, db_session):
        """测试更新项目阶段和状态 - Unicode 阶段"""
        project = Project(
            project_code="PJ-TEST-UNICODE",
            project_name="Unicode测试项目",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        with patch(
            "app.services.stage_advance_service.get_stage_status_mapping"
        ) as mock_mapping:
            mock_mapping.return_value = {"S1": "ST01", "中文": "ST99"}
            new_status = update_project_stage_and_status(
                db_session, project, "中文", "S1", "ST01"
            )
            assert new_status == "ST99"

        db_session.rollback()

    # ==================== 执行阶段门校验边界测试 ====================

    def test_perform_gate_check_invalid_skip_flag_type(self, db_session):
        """测试执行阶段门校验 - 无效的跳过标志类型"""
        project = Mock(spec=Project)
        project.id = 1

        passed, missing, result = perform_gate_check(
            db_session,
            project,
            "S2",
            skip_gate_check="true",
            current_user_is_superuser=True,
        )
        assert passed

    def test_perform_gate_check_none_project(self, db_session):
        """测试执行阶段门校验 - None 项目"""
        with pytest.raises(AttributeError):
            perform_gate_check(
                db_session,
                None,
                "S2",
                skip_gate_check=False,
                current_user_is_superuser=False,
            )

    def test_perform_gate_check_none_target_stage(self, db_session):
        """测试执行阶段门校验 - None 目标阶段"""
        from fastapi import HTTPException

        project = Mock(spec=Project)
        project.id = 1

        with pytest.raises(HTTPException):
            perform_gate_check(
                db_session,
                project,
                None,
                skip_gate_check=False,
                current_user_is_superuser=False,
            )

    def test_perform_gate_check_very_long_target_stage(self, db_session):
        """测试执行阶段门校验 - 很长的目标阶段"""
        project = Mock(spec=Project)
        project.id = 1

        with pytest.raises(Exception):
            perform_gate_check(
                db_session,
                project,
                "S" + "2" * 100,
                skip_gate_check=False,
                current_user_is_superuser=False,
            )

    # ==================== 集成边界测试 ====================

    def test_complete_workflow_extreme_stage_jump(self):
        """测试完整工作流 - 极端阶段跳跃"""
        validate_target_stage("S9")
        validate_stage_advancement("S1", "S9")

        mapping = get_stage_status_mapping()
        assert mapping["S9"] == "ST30"

    def test_complete_workflow_backward_jump_all(self):
        """测试完整工作流 - 所有向后跳跃"""
        backward_jumps = [
            ("S9", "S1"),
            ("S9", "S2"),
            ("S9", "S5"),
            ("S8", "S1"),
            ("S8", "S3"),
            ("S7", "S4"),
        ]

        for current, target in backward_jumps:
            validate_target_stage(target)
            with pytest.raises(Exception):
                validate_stage_advancement(current, target)

    def test_validate_then_update_workflow(self, db_session):
        """测试验证后更新工作流"""
        project = Project(
            project_code="PJ-TEST-WORKFLOW",
            project_name="工作流测试项目",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        validate_target_stage("S5")
        validate_stage_advancement("S1", "S5")

        mapping = get_stage_status_mapping()
        expected_status = mapping["S5"]
        assert expected_status == "ST10"

        new_status = update_project_stage_and_status(
            db_session, project, "S5", "S1", "ST01"
        )
        assert project.stage == "S5"
        assert new_status == expected_status

        db_session.rollback()
