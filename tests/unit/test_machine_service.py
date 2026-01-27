# -*- coding: utf-8 -*-
"""
machine_service 单元测试

测试机台管理服务的各个方法：
- 编码生成
- 阶段验证
- 阶段转移验证
- 项目聚合计算
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.machine_service import (
    HEALTH_PRIORITY,
    STAGE_PRIORITY,
    VALID_HEALTH,
    VALID_STAGES,
    MachineService,
    ProjectAggregationService,
)


def create_mock_db_session():
    """创建模拟的数据库会话"""
    return MagicMock()


def create_mock_project(project_id=1, project_code="PJ250712001"):
    """创建模拟的项目对象"""
    mock = MagicMock()
    mock.id = project_id
    mock.project_code = project_code
    mock.progress_pct = Decimal("0")
    mock.stage = "S1"
    mock.health = "H1"
    return mock


def create_mock_machine(
    machine_id=1,
    project_id=1,
    machine_no=1,
    stage="S1",
    health="H1",
    progress_pct=Decimal("0"),
):
    """创建模拟的机台对象"""
    mock = MagicMock()
    mock.id = machine_id
    mock.project_id = project_id
    mock.machine_no = machine_no
    mock.stage = stage
    mock.health = health
    mock.progress_pct = progress_pct
    return mock


@pytest.mark.unit
class TestConstants:
    """测试模块常量"""

    def test_stage_priority_has_all_stages(self):
        """测试阶段优先级包含所有阶段"""
        assert set(STAGE_PRIORITY.keys()) == set(VALID_STAGES)

    def test_health_priority_has_all_health(self):
        """测试健康度优先级包含所有健康度"""
        assert set(HEALTH_PRIORITY.keys()) == set(VALID_HEALTH)

    def test_stage_priority_order(self):
        """测试阶段优先级顺序正确"""
        assert STAGE_PRIORITY["S1"] < STAGE_PRIORITY["S2"]
        assert STAGE_PRIORITY["S8"] < STAGE_PRIORITY["S9"]

    def test_health_priority_order(self):
        """测试健康度优先级顺序正确（H3最高）"""
        assert HEALTH_PRIORITY["H3"] < HEALTH_PRIORITY["H2"]
        assert HEALTH_PRIORITY["H2"] < HEALTH_PRIORITY["H1"]
        assert HEALTH_PRIORITY["H1"] < HEALTH_PRIORITY["H4"]


@pytest.mark.unit
class TestMachineServiceGenerateCode:
    """测试 MachineService.generate_machine_code 方法"""

    def test_generates_first_machine_code(self):
        """测试生成第一个机台编码"""
        db = create_mock_db_session()
        project = create_mock_project(project_code="PJ250712001")
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.scalar.return_value = None

        service = MachineService(db)
        code, no = service.generate_machine_code(1)

        assert code == "PJ250712001-PN001"
        assert no == 1

    def test_generates_sequential_machine_code(self):
        """测试生成连续机台编码"""
        db = create_mock_db_session()
        project = create_mock_project(project_code="PJ250712001")

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            if call_count[0] == 0:  # Project query
            mock_query.filter.return_value.first.return_value = project
            call_count[0] += 1
        else:  # Max machine_no query
        mock_query.filter.return_value.scalar.return_value = 5
        return mock_query

        db.query.side_effect = query_side_effect

        service = MachineService(db)
        code, no = service.generate_machine_code(1)

        assert code == "PJ250712001-PN006"
        assert no == 6

    def test_raises_error_for_nonexistent_project(self):
        """测试项目不存在时抛出错误"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        service = MachineService(db)

        with pytest.raises(ValueError, match="项目不存在"):
            service.generate_machine_code(999)

    def test_pads_machine_number_to_three_digits(self):
        """测试机台序号补零到三位"""
        db = create_mock_db_session()
        project = create_mock_project(project_code="PJ250712001")
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.scalar.return_value = 0

        service = MachineService(db)
        code, no = service.generate_machine_code(1)

        assert "-PN001" in code


@pytest.mark.unit
class TestMachineServiceValidateStage:
    """测试 MachineService.validate_stage 方法"""

    def test_returns_true_for_valid_stages(self):
        """测试有效阶段返回True"""
        db = create_mock_db_session()
        service = MachineService(db)

        for stage in VALID_STAGES:
            assert service.validate_stage(stage) is True

    def test_returns_false_for_invalid_stage(self):
        """测试无效阶段返回False"""
        db = create_mock_db_session()
        service = MachineService(db)

        assert service.validate_stage("S0") is False
        assert service.validate_stage("S10") is False
        assert service.validate_stage("INVALID") is False


@pytest.mark.unit
class TestMachineServiceValidateHealth:
    """测试 MachineService.validate_health 方法"""

    def test_returns_true_for_valid_health(self):
        """测试有效健康度返回True"""
        db = create_mock_db_session()
        service = MachineService(db)

        for health in VALID_HEALTH:
            assert service.validate_health(health) is True

    def test_returns_false_for_invalid_health(self):
        """测试无效健康度返回False"""
        db = create_mock_db_session()
        service = MachineService(db)

        assert service.validate_health("H0") is False
        assert service.validate_health("H5") is False
        assert service.validate_health("INVALID") is False


@pytest.mark.unit
class TestMachineServiceValidateStageTransition:
    """测试 MachineService.validate_stage_transition 方法"""

    def test_allows_forward_transition(self):
        """测试允许向前推进"""
        db = create_mock_db_session()
        service = MachineService(db)

        is_valid, msg = service.validate_stage_transition("S1", "S2")
        assert is_valid is True
        assert msg == ""

        is_valid, msg = service.validate_stage_transition("S1", "S9")
        assert is_valid is True

    def test_allows_same_stage(self):
        """测试允许保持同一阶段"""
        db = create_mock_db_session()
        service = MachineService(db)

        is_valid, msg = service.validate_stage_transition("S3", "S3")
        assert is_valid is True

    def test_rejects_backward_transition(self):
        """测试拒绝回退"""
        db = create_mock_db_session()
        service = MachineService(db)

        is_valid, msg = service.validate_stage_transition("S5", "S3")
        assert is_valid is False
        assert "只能向前推进" in msg

    def test_rejects_transition_from_s9(self):
        """测试S9终态不能变更"""
        db = create_mock_db_session()
        service = MachineService(db)

        is_valid, msg = service.validate_stage_transition("S9", "S1")
        assert is_valid is False
        assert "S9是终态" in msg

    def test_rejects_invalid_current_stage(self):
        """测试无效当前阶段"""
        db = create_mock_db_session()
        service = MachineService(db)

        is_valid, msg = service.validate_stage_transition("INVALID", "S2")
        assert is_valid is False
        assert "无效的当前阶段" in msg

    def test_rejects_invalid_new_stage(self):
        """测试无效目标阶段"""
        db = create_mock_db_session()
        service = MachineService(db)

        is_valid, msg = service.validate_stage_transition("S1", "INVALID")
        assert is_valid is False
        assert "无效的目标阶段" in msg


@pytest.mark.unit
class TestProjectAggregationCalculateProgress:
    """测试 ProjectAggregationService.calculate_project_progress 方法"""

    def test_returns_zero_for_no_machines(self):
        """测试无机台返回0"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.scalar.return_value = None

        service = ProjectAggregationService(db)
        result = service.calculate_project_progress(1)

        assert result == Decimal("0.00")

    def test_calculates_average_progress(self):
        """测试计算平均进度"""
        db = create_mock_db_session()
        # 模拟平均值为 50.00
        db.query.return_value.filter.return_value.scalar.return_value = 50.0

        service = ProjectAggregationService(db)
        result = service.calculate_project_progress(1)

        assert result == Decimal("50.00")

    def test_rounds_to_two_decimals(self):
        """测试四舍五入到两位小数"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.scalar.return_value = 33.3333

        service = ProjectAggregationService(db)
        result = service.calculate_project_progress(1)

        assert result == Decimal("33.33")


@pytest.mark.unit
class TestProjectAggregationCalculateStage:
    """测试 ProjectAggregationService.calculate_project_stage 方法"""

    def test_returns_s1_for_no_machines(self):
        """测试无机台返回S1"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.all.return_value = []

        service = ProjectAggregationService(db)
        result = service.calculate_project_stage(1)

        assert result == "S1"

    def test_returns_earliest_stage(self):
        """测试返回最早阶段"""
        db = create_mock_db_session()
        machines = [
        MagicMock(stage="S5"),
        MagicMock(stage="S2"),
        MagicMock(stage="S7"),
        ]
        db.query.return_value.filter.return_value.all.return_value = machines

        service = ProjectAggregationService(db)
        result = service.calculate_project_stage(1)

        assert result == "S2"

    def test_ignores_invalid_stages(self):
        """测试忽略无效阶段"""
        db = create_mock_db_session()
        machines = [
        MagicMock(stage="INVALID"),
        MagicMock(stage="S5"),
        ]
        db.query.return_value.filter.return_value.all.return_value = machines

        service = ProjectAggregationService(db)
        result = service.calculate_project_stage(1)

        assert result == "S5"

    def test_returns_s1_for_all_invalid_stages(self):
        """测试所有阶段无效时返回S1"""
        db = create_mock_db_session()
        machines = [MagicMock(stage="INVALID")]
        db.query.return_value.filter.return_value.all.return_value = machines

        service = ProjectAggregationService(db)
        result = service.calculate_project_stage(1)

        assert result == "S1"


@pytest.mark.unit
class TestProjectAggregationCalculateHealth:
    """测试 ProjectAggregationService.calculate_project_health 方法"""

    def test_returns_h1_for_no_machines(self):
        """测试无机台返回H1"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.all.return_value = []

        service = ProjectAggregationService(db)
        result = service.calculate_project_health(1)

        assert result == "H1"

    def test_returns_h3_if_any_blocked(self):
        """测试任一机台阻塞则返回H3"""
        db = create_mock_db_session()
        machines = [
        MagicMock(health="H1"),
        MagicMock(health="H3"),
        MagicMock(health="H1"),
        ]
        db.query.return_value.filter.return_value.all.return_value = machines

        service = ProjectAggregationService(db)
        result = service.calculate_project_health(1)

        assert result == "H3"

    def test_returns_h2_if_any_at_risk(self):
        """测试任一机台有风险则返回H2"""
        db = create_mock_db_session()
        machines = [
        MagicMock(health="H1"),
        MagicMock(health="H2"),
        MagicMock(health="H1"),
        ]
        db.query.return_value.filter.return_value.all.return_value = machines

        service = ProjectAggregationService(db)
        result = service.calculate_project_health(1)

        assert result == "H2"

    def test_returns_h4_if_all_completed(self):
        """测试全部完结则返回H4"""
        db = create_mock_db_session()
        machines = [
        MagicMock(health="H4"),
        MagicMock(health="H4"),
        MagicMock(health="H4"),
        ]
        db.query.return_value.filter.return_value.all.return_value = machines

        service = ProjectAggregationService(db)
        result = service.calculate_project_health(1)

        assert result == "H4"

    def test_returns_h1_for_normal(self):
        """测试正常情况返回H1"""
        db = create_mock_db_session()
        machines = [
        MagicMock(health="H1"),
        MagicMock(health="H1"),
        ]
        db.query.return_value.filter.return_value.all.return_value = machines

        service = ProjectAggregationService(db)
        result = service.calculate_project_health(1)

        assert result == "H1"

    def test_h3_takes_priority_over_h2(self):
        """测试H3优先于H2"""
        db = create_mock_db_session()
        machines = [
        MagicMock(health="H2"),
        MagicMock(health="H3"),
        ]
        db.query.return_value.filter.return_value.all.return_value = machines

        service = ProjectAggregationService(db)
        result = service.calculate_project_health(1)

        assert result == "H3"

    def test_ignores_invalid_health(self):
        """测试忽略无效健康度"""
        db = create_mock_db_session()
        machines = [
        MagicMock(health="INVALID"),
        MagicMock(health="H2"),
        ]
        db.query.return_value.filter.return_value.all.return_value = machines

        service = ProjectAggregationService(db)
        result = service.calculate_project_health(1)

        assert result == "H2"


@pytest.mark.unit
class TestProjectAggregationUpdateProject:
    """测试 ProjectAggregationService.update_project_aggregation 方法"""

    def test_raises_error_for_nonexistent_project(self):
        """测试项目不存在时抛出错误"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        service = ProjectAggregationService(db)

        with pytest.raises(ValueError, match="项目不存在"):
            service.update_project_aggregation(999)

    def test_updates_project_fields(self):
        """测试更新项目字段"""
        db = create_mock_db_session()
        project = create_mock_project()

        call_count = [0]

        def query_side_effect(*args):
            mock_query = MagicMock()
            if call_count[0] == 0:  # Project query
            mock_query.filter.return_value.first.return_value = project
            mock_query.filter.return_value.scalar.return_value = 50.0
            mock_query.filter.return_value.all.return_value = []
        else:
            mock_query.filter.return_value.scalar.return_value = 50.0
            mock_query.filter.return_value.all.return_value = []
            call_count[0] += 1
            return mock_query

            db.query.side_effect = query_side_effect

            service = ProjectAggregationService(db)
            result = service.update_project_aggregation(1)

            db.add.assert_called_once()
            db.commit.assert_called_once()
            db.refresh.assert_called_once()


@pytest.mark.unit
class TestProjectAggregationMachineSummary:
    """测试 ProjectAggregationService.get_project_machine_summary 方法"""

    def test_returns_empty_summary_for_no_machines(self):
        """测试无机台返回空汇总"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.all.return_value = []

        service = ProjectAggregationService(db)
        result = service.get_project_machine_summary(1)

        assert result["total_machines"] == 0
        assert result["stage_distribution"] == {}
        assert result["health_distribution"] == {}
        assert result["avg_progress"] == Decimal("0.00")

    def test_calculates_distributions(self):
        """测试计算分布"""
        db = create_mock_db_session()
        machines = [
        create_mock_machine(stage="S2", health="H1", progress_pct=Decimal("30")),
        create_mock_machine(stage="S2", health="H2", progress_pct=Decimal("50")),
        create_mock_machine(stage="S5", health="H1", progress_pct=Decimal("70")),
        ]
        db.query.return_value.filter.return_value.all.return_value = machines

        service = ProjectAggregationService(db)
        result = service.get_project_machine_summary(1)

        assert result["total_machines"] == 3
        assert result["stage_distribution"]["S2"] == 2
        assert result["stage_distribution"]["S5"] == 1
        assert result["health_distribution"]["H1"] == 2
        assert result["health_distribution"]["H2"] == 1
        assert result["avg_progress"] == Decimal("50.00")

    def test_counts_completed_machines(self):
        """测试统计完结机台数"""
        db = create_mock_db_session()
        machines = [
        create_mock_machine(stage="S9", health="H4", progress_pct=Decimal("100")),
        create_mock_machine(stage="S9", health="H4", progress_pct=Decimal("100")),
        create_mock_machine(stage="S5", health="H1", progress_pct=Decimal("50")),
        ]
        db.query.return_value.filter.return_value.all.return_value = machines

        service = ProjectAggregationService(db)
        result = service.get_project_machine_summary(1)

        assert result["completed_count"] == 2

    def test_counts_at_risk_and_blocked(self):
        """测试统计风险和阻塞机台数"""
        db = create_mock_db_session()
        machines = [
        create_mock_machine(health="H2", progress_pct=Decimal("30")),
        create_mock_machine(health="H2", progress_pct=Decimal("40")),
        create_mock_machine(health="H3", progress_pct=Decimal("20")),
        ]
        db.query.return_value.filter.return_value.all.return_value = machines

        service = ProjectAggregationService(db)
        result = service.get_project_machine_summary(1)

        assert result["at_risk_count"] == 2
        assert result["blocked_count"] == 1

    def test_handles_none_progress(self):
        """测试处理空进度"""
        db = create_mock_db_session()
        machine = create_mock_machine(progress_pct=None)
        db.query.return_value.filter.return_value.all.return_value = [machine]

        service = ProjectAggregationService(db)
        result = service.get_project_machine_summary(1)

        assert result["avg_progress"] == Decimal("0.00")
