# -*- coding: utf-8 -*-
"""
阶段推进服务单元测试

测试内容：
- validate_target_stage() - 验证目标阶段编码
- validate_stage_advancement() - 检查阶段是否向前推进
- get_stage_status_mapping() - 获取阶段到状态的映射
"""

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.stage_advance_service import (
    get_stage_status_mapping,
    perform_gate_check,
    update_project_stage_and_status,
    validate_stage_advancement,
    validate_target_stage,
)


@pytest.mark.unit
class TestValidateTargetStage:
    """验证目标阶段编码测试"""

    def test_validate_target_stage_valid_stages(self):
        """测试有效的阶段编码"""
        valid_stages = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]

        for stage in valid_stages:
            # 不应该抛出异常
            validate_target_stage(stage)

    def test_validate_target_stage_invalid_stage_empty(self):
        """测试空字符串阶段编码"""
        with pytest.raises(HTTPException) as exc_info:
            validate_target_stage("")

        assert exc_info.value.status_code == 400
        assert "无效的目标阶段" in exc_info.value.detail

    def test_validate_target_stage_invalid_stage_none(self):
        """测试None阶段编码"""
        with pytest.raises(HTTPException) as exc_info:
            validate_target_stage(None)

        assert exc_info.value.status_code == 400
        assert "无效的目标阶段" in exc_info.value.detail

    def test_validate_target_stage_invalid_stage_format(self):
        """测试无效格式的阶段编码"""
        invalid_stages = [
            "s1",  # 小写
            "S01",  # 两位数字
            "SA",  # 字母而非数字
            "S0",  # 0不在有效范围
            "S10",  # 10不在有效范围
            "Stage1",  # 完全不同的格式
            "S-1",  # 包含特殊字符
            "",  # 空字符串
        ]

        for stage in invalid_stages:
            with pytest.raises(HTTPException) as exc_info:
                validate_target_stage(stage)

            assert exc_info.value.status_code == 400
            assert "无效的目标阶段" in exc_info.value.detail

    def test_validate_target_stage_error_message_format(self):
        """测试错误消息格式包含所有有效值"""
        with pytest.raises(HTTPException) as exc_info:
            validate_target_stage("INVALID")

        error_detail = exc_info.value.detail
        assert "有效值：" in error_detail
        assert "S1" in error_detail
        assert "S9" in error_detail
        assert error_detail.count("S") >= 9  # 应该包含所有9个阶段


@pytest.mark.unit
class TestValidateStageAdvancement:
    """检查阶段是否向前推进测试"""

    def test_validate_stage_advancement_forward_single(self):
        """测试单级向前推进 (S1->S2)"""
        # 不应该抛出异常
        validate_stage_advancement("S1", "S2")

    def test_validate_stage_advancement_forward_multiple(self):
        """测试多级向前推进 (S1->S3)"""
        # 不应该抛出异常
        validate_stage_advancement("S1", "S3")
        validate_stage_advancement("S2", "S5")
        validate_stage_advancement("S1", "S9")

    def test_validate_stage_advancement_invalid_same_stage(self):
        """测试目标阶段等于当前阶段"""
        with pytest.raises(HTTPException) as exc_info:
            validate_stage_advancement("S1", "S1")

        assert exc_info.value.status_code == 400
        assert "不能早于或等于" in exc_info.value.detail
        assert "S1" in exc_info.value.detail

    def test_validate_stage_advancement_invalid_backward(self):
        """测试向后推进 (S2->S1)"""
        with pytest.raises(HTTPException) as exc_info:
            validate_stage_advancement("S2", "S1")

        assert exc_info.value.status_code == 400
        assert "不能早于或等于" in exc_info.value.detail

    def test_validate_stage_advancement_invalid_skip_backwards(self):
        """测试跨级向后推进 (S5->S3)"""
        with pytest.raises(HTTPException) as exc_info:
            validate_stage_advancement("S5", "S3")

        assert exc_info.value.status_code == 400
        assert "不能早于或等于" in exc_info.value.detail

    def test_validate_stage_advancement_boundary_conditions(self):
        """测试边界条件 - 阶段1到阶段9的推进"""
        valid_transitions = [
            ("S1", "S2"),
            ("S2", "S3"),
            ("S3", "S4"),
            ("S4", "S5"),
            ("S5", "S6"),
            ("S6", "S7"),
            ("S7", "S8"),
            ("S8", "S9"),
        ]

        for current, target in valid_transitions:
            validate_stage_advancement(current, target)

    def test_validate_stage_advancement_invalid_transitions(self):
        """测试所有无效的阶段转换"""
        invalid_transitions = [
            ("S2", "S1"),
            ("S3", "S2"),
            ("S3", "S1"),
            ("S4", "S3"),
            ("S4", "S2"),
            ("S4", "S1"),
            ("S5", "S4"),
            ("S5", "S3"),
            ("S5", "S2"),
            ("S5", "S1"),
            ("S6", "S5"),
            ("S6", "S4"),
            ("S6", "S3"),
            ("S6", "S2"),
            ("S6", "S1"),
            ("S7", "S6"),
            ("S7", "S5"),
            ("S7", "S4"),
            ("S7", "S3"),
            ("S7", "S2"),
            ("S7", "S1"),
            ("S8", "S7"),
            ("S8", "S6"),
            ("S8", "S5"),
            ("S8", "S4"),
            ("S8", "S3"),
            ("S8", "S2"),
            ("S8", "S1"),
            ("S9", "S8"),
            ("S9", "S7"),
            ("S9", "S6"),
            ("S9", "S5"),
            ("S9", "S4"),
            ("S9", "S3"),
            ("S9", "S2"),
            ("S9", "S1"),
            # 相同阶段
            ("S1", "S1"),
            ("S2", "S2"),
            ("S3", "S3"),
            ("S4", "S4"),
            ("S5", "S5"),
            ("S6", "S6"),
            ("S7", "S7"),
            ("S8", "S8"),
            ("S9", "S9"),
        ]

        for current, target in invalid_transitions:
            with pytest.raises(HTTPException) as exc_info:
                validate_stage_advancement(current, target)

            assert exc_info.value.status_code == 400
            assert "不能早于或等于" in exc_info.value.detail
            assert current in exc_info.value.detail
            assert target in exc_info.value.detail


@pytest.mark.unit
class TestGetStageStatusMapping:
    """获取阶段到状态的映射测试"""

    def test_get_stage_status_mapping_returns_dict(self):
        """测试返回字典类型"""
        mapping = get_stage_status_mapping()

        assert isinstance(mapping, dict)

    def test_get_stage_status_mapping_correctness(self):
        """测试映射的正确性"""
        mapping = get_stage_status_mapping()

        # 验证所有9个阶段都存在
        expected_stages = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]
        for stage in expected_stages:
            assert stage in mapping, f"阶段 {stage} 不在映射中"

    def test_get_stage_status_mapping_values_format(self):
        """测试映射值的格式（ST开头）"""
        mapping = get_stage_status_mapping()

        for stage, status in mapping.items():
            assert status.startswith("ST"), f"状态 {status} 不以ST开头"
            assert len(status) >= 3, f"状态 {status} 长度不足"

    def test_get_stage_status_mapping_specific_values(self):
        """测试特定阶段的映射值"""
        mapping = get_stage_status_mapping()

        expected_mapping = {
            "S1": "ST01",
            "S2": "ST03",
            "S3": "ST05",
            "S4": "ST07",
            "S5": "ST10",
            "S6": "ST15",
            "S7": "ST20",
            "S8": "ST25",
            "S9": "ST30",
        }

        for stage, expected_status in expected_mapping.items():
            actual_status = mapping.get(stage)
            assert actual_status == expected_status, (
                f"阶段 {stage} 的映射应该是 {expected_status}，实际是 {actual_status}"
            )

    def test_get_stage_status_mapping_monotonic_status_codes(self):
        """测试状态代码单调递增"""
        mapping = get_stage_status_mapping()

        stages_in_order = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]
        status_numbers = []

        for stage in stages_in_order:
            status = mapping[stage]
            status_number = int(status[2:])  # 提取数字部分
            status_numbers.append(status_number)

        # 验证状态编号单调递增
        for i in range(len(status_numbers) - 1):
            assert status_numbers[i] < status_numbers[i + 1], (
                f"状态编号不是单调递增: {status_numbers}"
            )

    def test_get_stage_status_mapping_immutability(self):
        """测试返回的映射是否可变"""
        mapping = get_stage_status_mapping()

        # 尝试修改映射
        original_value = mapping["S1"]
        mapping["S1"] = "INVALID"

        # 再次获取映射，应该不受影响（因为每次返回新的字典）
        new_mapping = get_stage_status_mapping()
        assert new_mapping["S1"] == original_value


@pytest.mark.unit
class TestUpdateProjectStageAndStatus:
    """更新项目阶段和状态测试"""

    def test_update_project_stage_and_status_with_status_change(
        self, db_session: Session
    ):
        """测试状态发生变更时的更新"""
        from app.models import Project

        # 创建测试项目
        project = Project(
            project_code="PJ-TEST-001",
            project_name="测试项目",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        # 更新阶段和状态
        new_status = update_project_stage_and_status(
            db_session, project, "S2", "S1", "ST01"
        )

        assert project.stage == "S2"
        assert project.status == "ST03"  # S2对应ST03
        assert new_status == "ST03"

        db_session.rollback()

    def test_update_project_stage_and_status_without_status_change(
        self, db_session: Session
    ):
        """测试状态不发生变更时的更新（保持旧状态）"""
        from app.models import Project

        # 创建测试项目
        project = Project(
            project_code="PJ-TEST-002",
            project_name="测试项目",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        # 传入一个映射中不存在的阶段，应该保持旧状态
        with patch(
            "app.services.stage_advance_service.get_stage_status_mapping"
        ) as mock_mapping:
            mock_mapping.return_value = {}  # 空映射，模拟目标阶段没有对应状态

            new_status = update_project_stage_and_status(
                db_session, project, "INVALID", "S1", "ST01"
            )

            assert project.stage == "INVALID"
            assert project.status == "ST01"  # 保持旧状态
            assert new_status == "ST01"

        db_session.rollback()

    def test_update_project_stage_and_status_adds_to_session(self, db_session: Session):
        """测试将项目添加到数据库会话"""
        from app.models import Project

        # 创建测试项目
        project = Project(
            project_code="PJ-TEST-003",
            project_name="测试项目",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        # 更新项目
        update_project_stage_and_status(db_session, project, "S3", "S1", "ST01")

        # 验证项目在会话中
        assert project in db_session
        assert project.stage == "S3"

        db_session.rollback()


@pytest.mark.unit
class TestPerformGateCheck:
    """执行阶段门校验测试"""

    def test_perform_gate_check_skip_as_superuser(self, db_session: Session):
        """测试超级用户跳过阶段门校验"""
        from app.models import Project

        project = Mock(spec=Project)
        project.id = 1

        passed, missing, result = perform_gate_check(
            db_session,
            project,
            "S2",
            skip_gate_check=True,
            current_user_is_superuser=True,
        )

        assert passed
        assert missing == []
        assert result is None

    def test_perform_gate_check_skip_as_non_superuser(self, db_session: Session):
        """测试非超级用户尝试跳过阶段门校验"""
        from app.models import Project

        project = Mock(spec=Project)
        project.id = 1

        with pytest.raises(HTTPException) as exc_info:
            perform_gate_check(
                db_session,
                project,
                "S2",
                skip_gate_check=True,
                current_user_is_superuser=False,
            )

        assert exc_info.value.status_code == 403
        assert "只有管理员可以跳过阶段门校验" in exc_info.value.detail

    def test_perform_gate_check_superuser_auto_pass(self, db_session: Session):
        """测试超级用户自动通过阶段门校验（不跳过）"""
        from app.models import Project

        project = Mock(spec=Project)
        project.id = 1

        passed, missing, result = perform_gate_check(
            db_session,
            project,
            "S2",
            skip_gate_check=False,
            current_user_is_superuser=True,
        )

        assert passed
        assert missing == []
        assert result is None

    @patch("app.api.v1.endpoints.projects.check_gate")
    @patch("app.api.v1.endpoints.projects.check_gate_detailed")
    def test_perform_gate_check_normal_user_passed(
        self, mock_check_gate_detailed, mock_check_gate, db_session: Session
    ):
        """测试普通用户通过阶段门校验"""
        from app.models import Project

        project = Mock(spec=Project)
        project.id = 1

        # Mock check_gate 返回通过
        mock_check_gate.return_value = (True, [])

        passed, missing, result = perform_gate_check(
            db_session,
            project,
            "S2",
            skip_gate_check=False,
            current_user_is_superuser=False,
        )

        assert passed
        assert missing == []
        assert result is None
        mock_check_gate.assert_called_once()
        mock_check_gate_detailed.assert_not_called()

    @patch("app.api.v1.endpoints.projects.check_gate")
    @patch("app.api.v1.endpoints.projects.check_gate_detailed")
    def test_perform_gate_check_normal_user_failed(
        self, mock_check_gate_detailed, mock_check_gate, db_session: Session
    ):
        """测试普通用户未通过阶段门校验"""
        from app.models import Project

        project = Mock(spec=Project)
        project.id = 1

        # Mock check_gate 返回未通过
        mock_check_gate.return_value = (False, ["缺少物料A", "缺少物料B"])
        mock_check_gate_detailed.return_value = {"total": 10, "completed": 5}

        passed, missing, result = perform_gate_check(
            db_session,
            project,
            "S2",
            skip_gate_check=False,
            current_user_is_superuser=False,
        )

        assert not passed
        assert missing == ["缺少物料A", "缺少物料B"]
        assert result == {"total": 10, "completed": 5}
        mock_check_gate.assert_called_once()
        mock_check_gate_detailed.assert_called_once()


@pytest.mark.unit
class TestIntegrationScenarios:
    """集成场景测试"""

    def test_complete_validation_chain_valid(self):
        """测试完整的验证链条 - 有效场景"""
        # 验证目标阶段
        validate_target_stage("S2")

        # 验证阶段推进
        validate_stage_advancement("S1", "S2")

        # 获取状态映射
        mapping = get_stage_status_mapping()
        assert mapping["S2"] == "ST03"

    def test_complete_validation_chain_invalid_stage(self):
        """测试完整的验证链条 - 无效阶段"""
        with pytest.raises(HTTPException) as exc_info:
            validate_target_stage("INVALID")

        assert exc_info.value.status_code == 400

    def test_complete_validation_chain_invalid_advancement(self):
        """测试完整的验证链条 - 无效推进"""
        validate_target_stage("S1")

        with pytest.raises(HTTPException) as exc_info:
            validate_stage_advancement("S2", "S1")

        assert exc_info.value.status_code == 400

    @patch("app.api.v1.endpoints.projects.check_gate")
    @patch("app.api.v1.endpoints.projects.check_gate_detailed")
    def test_stage_advance_with_gate_check(
        self, mock_check_gate_detailed, mock_check_gate, db_session: Session
    ):
        """测试带阶段门校验的完整阶段推进流程（跳过校验作为超级用户）"""
        from app.models import Project

        # 创建测试项目
        project = Project(
            project_code="PJ-TEST-INTEGRATION",
            project_name="集成测试项目",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        # 验证阶段
        validate_target_stage("S2")
        validate_stage_advancement("S1", "S2")

        # 执行阶段门校验
        mock_check_gate.return_value = (True, [])
        passed, missing, _ = perform_gate_check(
            db_session,
            project,
            "S2",
            skip_gate_check=False,
            current_user_is_superuser=False,
        )

        assert passed

        # 更新项目
        update_project_stage_and_status(db_session, project, "S2", "S1", "ST01")

        assert project.stage == "S2"
        assert project.status == "ST03"

        db_session.rollback()
