# -*- coding: utf-8 -*-
"""
阶段流转服务单元测试

测试内容：
- S3→S4 流转检查（合同签订）
- S4→S5 流转检查（BOM发布）
- S5→S6 流转检查（物料齐套）
- S7→S8 流转检查（FAT验收）
- S8→S9 流转检查（终验收+回款）
- 阶段流转执行
"""

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.stage_transition_checks import (
    check_s3_to_s4_transition,
    check_s4_to_s5_transition,
    check_s5_to_s6_transition,
    check_s7_to_s8_transition,
    check_s8_to_s9_transition,
    get_stage_status_mapping,
    execute_stage_transition
)
from app.models.project import Project, ProjectPaymentPlan
from app.models.sales import Contract
from app.models.material import BomHeader
from app.models.acceptance import AcceptanceOrder


class TestStageStatusMapping:
    """阶段状态映射测试"""

    def test_get_stage_status_mapping(self):
        """测试获取阶段状态映射"""
        mapping = get_stage_status_mapping()

        assert isinstance(mapping, dict)
        assert 'S4' in mapping
        assert 'S5' in mapping
        assert 'S6' in mapping
        assert 'S8' in mapping
        assert 'S9' in mapping

        # 验证映射值格式
        for stage, status in mapping.items():
            assert stage.startswith('S')
            assert status.startswith('ST')


class TestS3ToS4Transition:
    """S3→S4 流转检查测试"""

    def test_transition_missing_contract_info(self, db_session: Session):
        """测试缺少合同信息时的流转检查"""
        # 创建一个没有合同信息的项目Mock
        project = Mock(spec=Project)
        project.contract_no = None
        project.contract_date = None
        project.contract_amount = None

        can_advance, target_stage, missing = check_s3_to_s4_transition(
            db_session, project
        )

        assert can_advance == False
        assert target_stage is None
        assert len(missing) > 0
        assert any("合同信息" in m for m in missing)

    def test_transition_contract_not_signed(self, db_session: Session):
        """测试合同未签订时的流转检查"""
        project = Mock(spec=Project)
        project.contract_no = "CONTRACT-001"
        project.contract_date = date.today()
        project.contract_amount = Decimal("100000")

        # 没有对应的合同记录或合同未签订
        can_advance, target_stage, missing = check_s3_to_s4_transition(
            db_session, project
        )

        # 应该返回不能推进
        assert can_advance == False
        assert any("合同" in m for m in missing)

    def test_transition_contract_signed(self, db_session: Session):
        """测试合同已签订时的流转检查"""
        # 查找一个有已签订合同的项目
        project = db_session.query(Project).filter(
            Project.contract_no.isnot(None)
        ).first()

        if not project:
            pytest.skip("No project with contract available")

        # 检查是否有对应的已签订合同
        contract = db_session.query(Contract).filter(
            Contract.contract_code == project.contract_no,
            Contract.status == "SIGNED"
        ).first()

        can_advance, target_stage, missing = check_s3_to_s4_transition(
            db_session, project
        )

        if contract:
            assert can_advance == True
            assert target_stage == "S4"
            assert len(missing) == 0
        else:
            assert can_advance == False


class TestS4ToS5Transition:
    """S4→S5 流转检查测试"""

    def test_transition_no_released_bom(self, db_session: Session):
        """测试没有已发布BOM时的流转检查"""
        # 使用一个没有BOM的项目ID
        can_advance, target_stage, missing = check_s4_to_s5_transition(
            db_session, project_id=999999
        )

        assert can_advance == False
        assert target_stage is None
        assert any("BOM" in m for m in missing)

    def test_transition_with_released_bom(self, db_session: Session):
        """测试有已发布BOM时的流转检查"""
        # 查找有已发布BOM的项目
        bom = db_session.query(BomHeader).filter(
            BomHeader.status == "RELEASED"
        ).first()

        if not bom or not bom.project_id:
            pytest.skip("No released BOM available")

        can_advance, target_stage, missing = check_s4_to_s5_transition(
            db_session, project_id=bom.project_id
        )

        assert can_advance == True
        assert target_stage == "S5"
        assert len(missing) == 0


class TestS5ToS6Transition:
    """S5→S6 流转检查测试"""

    def test_transition_check(self, db_session: Session):
        """测试S5→S6流转检查"""
        project = db_session.query(Project).filter(
            Project.stage == "S5"
        ).first()

        if not project:
            pytest.skip("No project in S5 stage available")

        can_advance, target_stage, missing = check_s5_to_s6_transition(
            db_session, project
        )

        # 根据物料齐套率结果
        if can_advance:
            assert target_stage == "S6"
            assert len(missing) == 0
        else:
            assert target_stage is None
            assert len(missing) > 0


class TestS7ToS8Transition:
    """S7→S8 流转检查测试"""

    def test_transition_no_fat_passed(self, db_session: Session):
        """测试没有FAT验收通过时的流转检查"""
        can_advance, target_stage, missing = check_s7_to_s8_transition(
            db_session, project_id=999999
        )

        assert can_advance == False
        assert target_stage is None
        assert any("FAT" in m for m in missing)

    def test_transition_with_fat_passed(self, db_session: Session):
        """测试FAT验收通过时的流转检查"""
        # 查找有FAT验收通过的项目
        fat_order = db_session.query(AcceptanceOrder).filter(
            AcceptanceOrder.acceptance_type == "FAT",
            AcceptanceOrder.status == "COMPLETED",
            AcceptanceOrder.overall_result == "PASSED"
        ).first()

        if not fat_order or not fat_order.project_id:
            pytest.skip("No FAT passed acceptance available")

        can_advance, target_stage, missing = check_s7_to_s8_transition(
            db_session, project_id=fat_order.project_id
        )

        assert can_advance == True
        assert target_stage == "S8"
        assert len(missing) == 0


class TestS8ToS9Transition:
    """S8→S9 流转检查测试"""

    def test_transition_no_final_acceptance(self, db_session: Session):
        """测试没有终验收通过时的流转检查"""
        project = Mock(spec=Project)
        project.id = 999999
        project.contract_amount = Decimal("100000")

        can_advance, target_stage, missing = check_s8_to_s9_transition(
            db_session, project
        )

        assert can_advance == False
        assert target_stage is None
        assert any("终验收" in m for m in missing)

    def test_transition_no_payment_plan(self, db_session: Session):
        """测试没有收款计划时的流转检查"""
        # 查找有终验收但没有收款计划的项目
        final_order = db_session.query(AcceptanceOrder).filter(
            AcceptanceOrder.acceptance_type.in_(["FINAL", "SAT"]),
            AcceptanceOrder.status == "COMPLETED",
            AcceptanceOrder.overall_result == "PASSED"
        ).first()

        if not final_order or not final_order.project_id:
            pytest.skip("No final acceptance available")

        project = db_session.query(Project).filter(
            Project.id == final_order.project_id
        ).first()

        if not project:
            pytest.skip("Project not found")

        # 检查是否有收款计划
        payment_plans = db_session.query(ProjectPaymentPlan).filter(
            ProjectPaymentPlan.project_id == project.id
        ).all()

        can_advance, target_stage, missing = check_s8_to_s9_transition(
            db_session, project
        )

        if not payment_plans:
            assert can_advance == False
            assert any("收款计划" in m for m in missing)

    def test_transition_payment_rate_below_threshold(self, db_session: Session):
        """测试回款率低于阈值时的流转检查"""
        # 创建Mock项目
        project = Mock(spec=Project)
        project.id = 999999
        project.contract_amount = Decimal("100000")

        can_advance, target_stage, missing = check_s8_to_s9_transition(
            db_session, project
        )

        # 应该不能推进（没有终验收或回款不足）
        assert can_advance == False


class TestExecuteStageTransition:
    """执行阶段流转测试"""

    def test_execute_transition_gate_not_passed(self, db_session: Session):
        """测试阶段门校验未通过时的流转"""
        project = db_session.query(Project).first()

        if not project:
            pytest.skip("No project available")

        # 尝试推进到一个不太可能满足条件的阶段
        success, result = execute_stage_transition(
            db_session,
            project,
            target_stage="S9",  # 最后阶段，条件最严格
            transition_reason="测试流转"
        )

        # 根据项目实际情况
        assert "can_advance" in result
        assert "message" in result
        assert "current_stage" in result
        assert "target_stage" in result

    def test_execute_transition_success(self, db_session: Session):
        """测试成功执行阶段流转"""
        # 查找一个可以推进的项目
        project = db_session.query(Project).filter(
            Project.stage == "S3"
        ).first()

        if not project:
            pytest.skip("No project in S3 stage available")

        # 检查是否满足S4条件
        can_advance, _, _ = check_s3_to_s4_transition(db_session, project)

        if not can_advance:
            pytest.skip("Project cannot advance to S4")

        success, result = execute_stage_transition(
            db_session,
            project,
            target_stage="S4",
            transition_reason="合同已签订"
        )

        if success:
            assert result["auto_advanced"] == True
            assert result["target_stage"] == "S4"
            assert len(result["missing_items"]) == 0

    def test_execute_transition_exception_handling(self, db_session: Session):
        """测试流转执行异常处理"""
        project = Mock(spec=Project)
        project.stage = "S3"
        project.id = 1

        # 模拟异常情况 - patch正确的导入位置
        with patch('app.api.v1.endpoints.projects.check_gate') as mock_check:
            mock_check.side_effect = Exception("测试异常")

            success, result = execute_stage_transition(
                db_session,
                project,
                target_stage="S4",
                transition_reason="测试"
            )

            assert success == False
            assert "失败" in result["message"]


class TestTransitionIntegration:
    """阶段流转集成测试"""

    def test_full_transition_flow(self, db_session: Session):
        """测试完整的阶段流转流程"""
        # 查找一个处于早期阶段的项目
        project = db_session.query(Project).filter(
            Project.stage.in_(["S1", "S2", "S3"])
        ).first()

        if not project:
            pytest.skip("No project in early stage available")

        current_stage = project.stage

        # 确定可能的下一阶段
        stage_sequence = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]
        current_index = stage_sequence.index(current_stage)

        if current_index >= len(stage_sequence) - 1:
            pytest.skip("Project already in final stage")

        next_stage = stage_sequence[current_index + 1]

        # 检查是否可以推进到下一阶段
        check_functions = {
            "S4": lambda: check_s3_to_s4_transition(db_session, project),
            "S5": lambda: check_s4_to_s5_transition(db_session, project.id),
            "S6": lambda: check_s5_to_s6_transition(db_session, project),
            "S8": lambda: check_s7_to_s8_transition(db_session, project.id),
            "S9": lambda: check_s8_to_s9_transition(db_session, project),
        }

        if next_stage in check_functions:
            can_advance, target_stage, missing = check_functions[next_stage]()

            # 验证返回格式
            assert isinstance(can_advance, bool)
            assert target_stage is None or target_stage == next_stage
            assert isinstance(missing, list)


class TestEdgeCases:
    """边界情况测试"""

    def test_null_project_values(self, db_session: Session):
        """测试项目属性为空的情况"""
        project = Mock(spec=Project)
        project.contract_no = None
        project.contract_date = None
        project.contract_amount = None

        can_advance, target_stage, missing = check_s3_to_s4_transition(
            db_session, project
        )

        assert can_advance == False
        assert len(missing) > 0

    def test_zero_contract_amount(self, db_session: Session):
        """测试合同金额为零的情况"""
        project = Mock(spec=Project)
        project.id = 999999
        project.contract_amount = Decimal("0")

        can_advance, target_stage, missing = check_s8_to_s9_transition(
            db_session, project
        )

        # 合同金额为零应该导致无法计算回款率
        assert can_advance == False

    def test_negative_project_id(self, db_session: Session):
        """测试负数项目ID的情况"""
        can_advance, target_stage, missing = check_s4_to_s5_transition(
            db_session, project_id=-1
        )

        assert can_advance == False
        assert len(missing) > 0
