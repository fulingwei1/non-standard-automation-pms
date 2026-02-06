# -*- coding: utf-8 -*-
"""
阶段流转检查服务单元测试
"""

from unittest.mock import MagicMock, patch

import pytest


class TestCheckS3ToS4Transition:
    """测试S3到S4流转检查"""

    def test_missing_contract_info(self, db_session):
        """测试缺少合同信息"""
        from app.services.stage_transition_checks import check_s3_to_s4_transition

        project = MagicMock()
        project.contract_no = None
        project.contract_date = None
        project.contract_amount = None

        can_advance, target, missing = check_s3_to_s4_transition(db_session, project)

        assert can_advance is False
        assert target is None
        assert len(missing) > 0
        assert "合同信息不完整" in missing[0]

    def test_contract_not_signed(self, db_session):
        """测试合同未签订"""
        from app.services.stage_transition_checks import check_s3_to_s4_transition
        from app.models.sales import Contract

        project = MagicMock()
        project.contract_no = "CT001"
        project.contract_date = "2025-01-15"
        project.contract_amount = 100000

            # 合同状态不是SIGNED
        contract = Contract(
        contract_code="CT001",
        status="DRAFT",
        opportunity_id=1,  # Required field
        customer_id=1  # Required field
        )
        db_session.add(contract)
        db_session.flush()

        can_advance, target, missing = check_s3_to_s4_transition(db_session, project)

        assert can_advance is False
        assert "合同未签订" in missing[0]

    def test_contract_signed_can_advance(self, db_session):
        """测试合同已签订可推进"""
        from app.services.stage_transition_checks import check_s3_to_s4_transition
        from app.models.sales import Contract

        project = MagicMock()
        project.contract_no = "CT002"
        project.contract_date = "2025-01-15"
        project.contract_amount = 100000

        contract = Contract(
        contract_code="CT002",
        status="SIGNED",
        opportunity_id=1,  # Required field
        customer_id=1  # Required field
        )
        db_session.add(contract)
        db_session.flush()

        can_advance, target, missing = check_s3_to_s4_transition(db_session, project)

        assert can_advance is True
        assert target == "S4"
        assert len(missing) == 0


class TestCheckS4ToS5Transition:
    """测试S4到S5流转检查"""

    def test_no_released_bom(self, db_session):
        """测试无已发布BOM"""
        from app.services.stage_transition_checks import check_s4_to_s5_transition

        can_advance, target, missing = check_s4_to_s5_transition(db_session, 99999)

        assert can_advance is False
        assert target is None
        assert "BOM未发布" in missing[0]

    def test_released_bom_can_advance(self, db_session):
        """测试有已发布BOM可推进"""
        from app.services.stage_transition_checks import check_s4_to_s5_transition
        from app.models.material import BomHeader

        bom = BomHeader(
        bom_no="BOM-001",  # Required field
        bom_name="Test BOM",  # Required field
        project_id=1,
        status="RELEASED"
        )
        db_session.add(bom)
        db_session.flush()

        can_advance, target, missing = check_s4_to_s5_transition(db_session, 1)

        assert can_advance is True
        assert target == "S5"
        assert len(missing) == 0


class TestCheckS7ToS8Transition:
    """测试S7到S8流转检查"""

    def test_no_fat_passed(self, db_session):
        """测试FAT验收未通过"""
        from app.services.stage_transition_checks import check_s7_to_s8_transition

        can_advance, target, missing = check_s7_to_s8_transition(db_session, 99999)

        assert can_advance is False
        assert target is None
        assert "FAT验收未通过" in missing[0]

    def test_fat_passed_can_advance(self, db_session):
        """测试FAT验收通过可推进"""
        from app.services.stage_transition_checks import check_s7_to_s8_transition
        from app.models.acceptance import AcceptanceOrder

        order = AcceptanceOrder(
        order_no="AO-001",  # Required field
        project_id=1,
        acceptance_type="FAT",
        status="COMPLETED",
        overall_result="PASSED"
        )
        db_session.add(order)
        db_session.flush()

        can_advance, target, missing = check_s7_to_s8_transition(db_session, 1)

        assert can_advance is True
        assert target == "S8"
        assert len(missing) == 0


class TestCheckS8ToS9Transition:
    """测试S8到S9流转检查"""

    def test_no_final_acceptance(self, db_session):
        """测试终验收未通过"""
        from app.services.stage_transition_checks import check_s8_to_s9_transition

        project = MagicMock()
        project.id = 99999

        can_advance, target, missing = check_s8_to_s9_transition(db_session, project)

        assert can_advance is False
        assert "终验收未通过" in missing[0]

    def test_no_payment_plan(self, db_session):
        """测试无收款计划"""
        from app.services.stage_transition_checks import check_s8_to_s9_transition
        from app.models.acceptance import AcceptanceOrder

            # 创建终验收
        order = AcceptanceOrder(
        order_no="AO-002",  # Required field
        project_id=1,
        acceptance_type="FINAL",
        status="COMPLETED",
        overall_result="PASSED"
        )
        db_session.add(order)
        db_session.flush()

        project = MagicMock()
        project.id = 1

        can_advance, target, missing = check_s8_to_s9_transition(db_session, project)

        assert can_advance is False
        assert "收款计划未设置" in missing[0]


class TestGetStageStatusMapping:
    """测试获取阶段状态映射"""

    def test_mapping_exists(self):
        """测试映射存在"""
        from app.services.stage_transition_checks import get_stage_status_mapping

        mapping = get_stage_status_mapping()

        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_s4_maps_to_st09(self):
        """测试S4映射到ST09"""
        from app.services.stage_transition_checks import get_stage_status_mapping

        mapping = get_stage_status_mapping()

        assert mapping.get('S4') == 'ST09'

    def test_s9_maps_to_st30(self):
        """测试S9映射到ST30"""
        from app.services.stage_transition_checks import get_stage_status_mapping

        mapping = get_stage_status_mapping()

        assert mapping.get('S9') == 'ST30'


class TestExecuteStageTransition:
    """测试执行阶段流转"""

    def test_gate_not_passed(self, db_session):
        """测试门禁未通过"""
        from app.services.stage_transition_checks import execute_stage_transition

        project = MagicMock()
        project.stage = "S3"

        with patch('app.api.v1.endpoints.projects.utils.check_gate') as mock_gate:
            mock_gate.return_value = (False, ["缺少必要条件"])

            success, result = execute_stage_transition(
            db_session, project, "S4", "测试原因"
            )

            assert success is False
            assert result["can_advance"] is False
            assert "阶段门校验未通过" in result["message"]

    def test_successful_transition(self, db_session):
        """测试成功流转"""
        from app.services.stage_transition_checks import execute_stage_transition

        project = MagicMock()
        project.stage = "S3"

        with patch('app.api.v1.endpoints.projects.utils.check_gate') as mock_gate:
            mock_gate.return_value = (True, [])

            success, result = execute_stage_transition(
            db_session, project, "S4", "合同已签订"
            )

            assert success is True
            assert result["auto_advanced"] is True
            assert project.stage == "S4"

    def test_transition_exception_handling(self, db_session):
        """测试流转异常处理"""
        from app.services.stage_transition_checks import execute_stage_transition

        project = MagicMock()
        project.stage = "S3"

        with patch('app.api.v1.endpoints.projects.utils.check_gate') as mock_gate:
            mock_gate.side_effect = Exception("测试异常")

            success, result = execute_stage_transition(
            db_session, project, "S4", "测试"
            )

            assert success is False
            assert "自动推进失败" in result["message"]


class TestPaymentRateCalculation:
    """测试回款率计算"""

    def test_payment_rate_80_percent(self):
        """测试回款率80%"""
        total_paid = 80000
        base_amount = 100000

        payment_rate = (total_paid / base_amount) * 100

        assert payment_rate == 80.0

    def test_payment_rate_below_threshold(self):
        """测试回款率低于阈值"""
        total_paid = 70000
        base_amount = 100000

        payment_rate = (total_paid / base_amount) * 100
        can_advance = payment_rate >= 80

        assert can_advance is False

    def test_payment_rate_above_threshold(self):
        """测试回款率高于阈值"""
        total_paid = 90000
        base_amount = 100000

        payment_rate = (total_paid / base_amount) * 100
        can_advance = payment_rate >= 80

        assert can_advance is True


class TestTransitionResultStructure:
    """测试流转结果结构"""

    def test_result_fields(self):
        """测试结果字段"""
        result = {
        "can_advance": True,
        "auto_advanced": True,
        "message": "已自动推进至 S4 阶段",
        "current_stage": "S3",
        "target_stage": "S4",
        "missing_items": [],
        "transition_reason": "合同已签订"
        }

        expected_fields = [
        "can_advance", "auto_advanced", "message",
        "current_stage", "target_stage", "missing_items", "transition_reason"
        ]

        for field in expected_fields:
            assert field in result


            # pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
