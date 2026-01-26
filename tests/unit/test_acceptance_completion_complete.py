# -*- coding: utf-8 -*-
"""
验收完成服务完整测试

包含实际数据库集成和边缘场景测试
补充 test_acceptance_completion_service.py 的不足
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.acceptance import (
    AcceptanceIssue,
    AcceptanceOrder,
    AcceptanceOrderItem,
)
from app.models.project import Machine, Project
from app.services.acceptance_completion_service import (
    handle_acceptance_status_transition,
    handle_progress_integration,
    trigger_bonus_calculation,
    trigger_invoice_on_acceptance,
    trigger_warranty_period,
    update_acceptance_order_status,
    validate_required_check_items,
)


@pytest.mark.unit
@pytest.mark.integration
class TestValidateRequiredCheckItemsIntegration:
    """集成测试：使用真实数据库验证必检项"""

    def test_validate_required_items_all_passed(self, db_session: Session):
        """所有必检项已完成，不应抛出异常"""
        # 创建验收单和必检项
        project = Project(
            project_code="PJ-TEST-001",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,  # 必须设置 project_id
            machine_code="M-001",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-001",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=1,
            created_by=1,
        )
        db_session.add(order)

        # 创建已完成的必检项
        item = AcceptanceOrderItem(
            order_id=order.id,
            category_code="CAT1",
            category_name="分类1",
            item_code="ITEM-001",
            item_name="检查项1",
            is_required=True,
            result_status="PASSED",
        )
        db_session.add(item)

        db_session.commit()

        # 验证不应抛出异常
        validate_required_check_items(db_session, order.id)

    def test_validate_required_items_with_pending(self, db_session: Session):
        """存在未完成的必检项，应抛出异常"""
        from fastapi import HTTPException

        # 创建验收单和未完成的必检项
        project = Project(
            project_code="PJ-TEST-002",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-002",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-002",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=2,
            created_by=1,
        )
        db_session.add(order)

        # 创建2个未完成的必检项
        for i in range(2):
            item = AcceptanceOrderItem(
                order_id=order.id,
                category_code="CAT1",
                category_name="分类1",
                item_code=f"ITEM-00{i}",
                item_name=f"检查项{i}",
                is_required=True,
                result_status="PENDING",
            )
            db_session.add(item)

        db_session.commit()

        # 应抛出异常
        with pytest.raises(HTTPException) as exc_info:
            validate_required_check_items(db_session, order.id)

        assert exc_info.value.status_code == 400
        assert "2 个必检项" in exc_info.value.detail

    def test_validate_required_items_non_required_skipped(self, db_session: Session):
        """非必检项不应影响验证"""
        # 创建验收单
        project = Project(
            project_code="PJ-TEST-003",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-003",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-003",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=2,
            created_by=1,
        )
        db_session.add(order)

        # 创建1个必检项（已完成）和1个非必检项（未完成）
        required_item = AcceptanceOrderItem(
            order_id=order.id,
            category_code="CAT1",
            category_name="分类1",
            item_code="ITEM-001",
            item_name="必检项",
            is_required=True,
            result_status="PASSED",
        )
        optional_item = AcceptanceOrderItem(
            order_id=order.id,
            category_code="CAT1",
            category_name="分类1",
            item_code="ITEM-002",
            item_name="非必检项",
            is_required=False,
            result_status="PENDING",
        )
        db_session.add_all([required_item, optional_item])

        db_session.commit()

        # 验证不应抛出异常
        validate_required_check_items(db_session, order.id)

    def test_validate_required_items_no_items(self, db_session: Session):
        """没有检查项的情况"""
        # 创建验收单但没有任何检查项
        project = Project(
            project_code="PJ-TEST-004",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-004",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-004",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)

        db_session.commit()

        # 验证不应抛出异常
        validate_required_check_items(db_session, order.id)


@pytest.mark.unit
@pytest.mark.integration
class TestUpdateAcceptanceOrderStatusIntegration:
    """集成测试：使用真实数据库更新验收单状态"""

    def test_update_status_with_actual_end_date(self, db_session: Session):
        """验证 actual_end_date 自动设置"""
        # 创建验收单
        project = Project(
            project_code="PJ-TEST-010",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-010",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-010",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()

        # 更新状态
        update_acceptance_order_status(
            db_session,
            order,
            overall_result="PASSED",
            conclusion="验收通过",
            conditions=None,
        )

        # 验证更新
        db_session.refresh(order)
        assert order.status == "COMPLETED"
        assert order.overall_result == "PASSED"
        assert order.conclusion == "验收通过"
        assert order.conditions is None
        assert order.actual_end_date is not None

    def test_update_status_with_conditions(self, db_session: Session):
        """测试有条件通过的情况"""
        # 创建验收单
        project = Project(
            project_code="PJ-TEST-011",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-011",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-011",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()

        # 更新状态（有条件）
        conditions = "条件1: 缺件不影响功能\n条件2: 补件前不发货"
        update_acceptance_order_status(
            db_session,
            order,
            overall_result="CONDITIONAL",
            conclusion="有条件通过",
            conditions=conditions,
        )

        # 验证更新
        db_session.refresh(order)
        assert order.overall_result == "CONDITIONAL"
        assert order.conclusion == "有条件通过"
        assert order.conditions == conditions

    def test_update_status_invalid_overall_result(self, db_session: Session):
        """测试无效的验收结果值"""
        # 创建验收单
        project = Project(
            project_code="PJ-TEST-012",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-012",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-012",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()

        # 使用无效的overall_result（不会抛出异常，但会存储到数据库）
        update_acceptance_order_status(
            db_session,
            order,
            overall_result="INVALID",
            conclusion="测试",
            conditions=None,
        )

        # 验证存储（虽然无效，但数据库没有约束）
        db_session.refresh(order)
        assert order.overall_result == "INVALID"


@pytest.mark.unit
class TestTriggerInvoiceOnAcceptanceEdgeCases:
    """边缘场景测试：开票触发"""

    @patch("os.getenv", return_value="false")
    @patch("app.services.invoice_auto_service.InvoiceAutoService")
    def test_invoice_request_not_invoice(self, mock_service_class, mock_getenv):
        """AUTO_CREATE_INVOICE_ON_ACCEPTANCE=false 时只创建申请"""
        mock_db = MagicMock()
        mock_service = MagicMock()
        mock_service.check_and_create_invoice_request.return_value = {
            "success": True,
            "invoice_requests": [{"id": 1, "request_no": "REQ-001"}],
        }
        mock_service_class.return_value = mock_service

        result = trigger_invoice_on_acceptance(mock_db, 1, auto_trigger=True)

        assert result["success"] is True
        assert "invoice_requests" in result
        # 验证传递的参数
        call_args = mock_service.check_and_create_invoice_request.call_args
        assert call_args[1]["auto_create"] is False

    @patch("os.getenv", return_value="true")
    @patch("app.services.invoice_auto_service.InvoiceAutoService")
    def test_direct_invoice_creation(self, mock_service_class, mock_getenv):
        """AUTO_CREATE_INVOICE_ON_ACCEPTANCE=true 时直接创建发票"""
        mock_db = MagicMock()
        mock_service = MagicMock()
        mock_service.check_and_create_invoice_request.return_value = {
            "success": True,
            "invoice_requests": [],
        }  # empty means direct invoice created
        mock_service_class.return_value = mock_service

        result = trigger_invoice_on_acceptance(mock_db, 1, auto_trigger=True)

        assert result["success"] is True
        # 验证传递的参数
        call_args = mock_service.check_and_create_invoice_request.call_args
        assert call_args[1]["auto_create"] is True

    @patch("app.services.invoice_auto_service.InvoiceAutoService")
    def test_invoice_service_not_available(self, mock_service_class):
        """开票服务不可用时不应抛出异常"""
        mock_db = MagicMock()
        mock_service_class.side_effect = ImportError(
            "No module named 'invoice_service'"
        )

        result = trigger_invoice_on_acceptance(mock_db, 1, auto_trigger=True)

        # 应优雅地返回错误而不是抛出异常
        assert result["success"] is False
        assert "error" in result


@pytest.mark.unit
@pytest.mark.integration
class TestHandleAcceptanceStatusTransitionIntegration:
    """集成测试：验收状态联动"""

    @patch("app.services.status_transition_service.StatusTransitionService")
    def test_fat_passed_with_db_mock(self, mock_service_class, db_session: Session):
        """FAT通过测试（使用真实验收单）"""
        # 创建测试数据
        project = Project(
            project_code="PJ-TEST-020",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-020",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-020",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.flush()  # 确保 order.id 生成

        # 创建验收问题（未解决）
        from datetime import datetime
        issue = AcceptanceIssue(
            issue_no=f"AI-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            order_id=order.id,
            issue_type="FUNCTION",
            severity="MEDIUM",
            title="测试问题",
            description="问题描述",
            status="OPEN",
            is_blocking=False,
        )
        db_session.add(issue)

        db_session.commit()

        # Mock StatusTransitionService
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # 执行状态联动
        handle_acceptance_status_transition(db_session, order, "PASSED")

        # 验证调用了正确的方法
        mock_service.handle_fat_passed.assert_called_once_with(
            order.project_id, order.machine_id
        )

    @patch("app.services.status_transition_service.StatusTransitionService")
    def test_fat_failed_with_issues(self, mock_service_class, db_session: Session):
        """FAT失败，带问题描述"""
        # 创建测试数据
        project = Project(
            project_code="PJ-TEST-021",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-021",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-021",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.flush()  # 确保 order.id 生成

        # 创建多个验收问题（未解决）
        from datetime import datetime
        base_time = datetime.now().strftime('%Y%m%d%H%M%S')
        issues = [
            AcceptanceIssue(
                issue_no=f"AI-{base_time}-{i}",
                order_id=order.id,
                issue_type="FUNCTION",
                severity="HIGH",
                title=f"问题{i}",
                description=f"问题{i}描述",
                status="OPEN",
                is_blocking=True if i == 0 else False,
            )
            for i in range(3)
        ]
        db_session.add_all(issues)
        db_session.commit()

        # Mock StatusTransitionService
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # 执行状态联动
        handle_acceptance_status_transition(db_session, order, "FAILED")

        # 验证调用了失败处理
        call_args = mock_service.handle_fat_failed.call_args
        assert call_args is not None
        # 验证传递了问题描述
        descriptions = call_args[0][2]  # 第3个参数
        assert isinstance(descriptions, list)
        assert len(descriptions) > 0


@pytest.mark.unit
@pytest.mark.integration
class TestTriggerWarrantyPeriodIntegration:
    """集成测试：质保期触发"""

    def test_warranty_period_for_final_acceptance(self, db_session: Session):
        """终验收通过，应触发质保期"""
        # 创建测试数据
        project = Project(
            project_code="PJ-TEST-030",
            project_name="测试项目",
            stage="S8",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-030",
            machine_name="测试设备",
            machine_type="TEST",
            status="INSTALLATION",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-030",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FINAL",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()

        # 触发质保期
        trigger_warranty_period(db_session, order, "PASSED")

        # 验证项目状态更新
        db_session.refresh(project)
        assert project.stage == "S9"
        assert project.actual_end_date is not None

        # 验证设备状态更新
        db_session.refresh(machine)
        assert machine.stage == "S9"
        assert machine.status == "COMPLETED"

    def test_warranty_period_not_for_fat(self, db_session: Session):
        """FAT验收不应触发质保期"""
        # 创建测试数据
        project = Project(
            project_code="PJ-TEST-031",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-031",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-031",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()

        # 记录原始状态
        original_project_stage = project.stage
        original_machine_status = machine.status

        # 触发质保期（不应触发）
        trigger_warranty_period(db_session, order, "PASSED")

        # 验证状态未改变
        db_session.refresh(project)
        db_session.refresh(machine)
        assert project.stage == original_project_stage
        assert machine.status == original_machine_status

    def test_warranty_period_multiple_machines(self, db_session: Session):
        """项目有多个设备时，都应更新为质保期"""
        # 创建测试数据
        project = Project(
            project_code="PJ-TEST-032",
            project_name="测试项目",
            stage="S8",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        # 创建3个设备
        machines = [
            Machine(
                project_id=project.id,
                machine_code=f"M-032-{i}",
                machine_name=f"测试设备{i}",
                machine_type="TEST",
                status="INSTALLATION",
            )
            for i in range(3)
        ]
        db_session.add_all(machines)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-032",
            project_id=project.id,
            machine_id=machines[0].id,
            acceptance_type="FINAL",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()

        # 触发质保期
        trigger_warranty_period(db_session, order, "PASSED")

        # 验证所有设备都更新了
        db_session.refresh(project)
        assert project.stage == "S9"

        for machine in machines:
            db_session.refresh(machine)
            assert machine.stage == "S9"
            assert machine.status == "COMPLETED"


@pytest.mark.unit
@pytest.mark.integration
class TestTriggerBonusCalculationIntegration:
    """集成测试：奖金计算触发"""

    @patch("app.services.bonus.BonusCalculator")
    def test_fat_bonus_calculation(self, mock_calculator_class, db_session: Session):
        """FAT通过应触发奖金计算"""
        # 创建测试数据
        project = Project(
            project_code="PJ-TEST-040",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-040",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-040",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()

        # Mock BonusCalculator
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator

        # 触发奖金计算
        trigger_bonus_calculation(db_session, order, "PASSED")

        # 验证调用了奖金计算
        mock_calculator.trigger_acceptance_bonus_calculation.assert_called_once()

        # 验证传递的参数
        call_args = mock_calculator.trigger_acceptance_bonus_calculation.call_args
        assert call_args[0][0].id == project.id
        assert call_args[0][1].id == order.id

    @patch("app.services.bonus.BonusCalculator")
    def test_sat_bonus_calculation(self, mock_calculator_class, db_session: Session):
        """SAT通过应触发奖金计算（与FAT可能不同）"""
        # 创建测试数据
        project = Project(
            project_code="PJ-TEST-041",
            project_name="测试项目",
            stage="S8",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-041",
            machine_name="测试设备",
            machine_type="TEST",
            status="INSTALLATION",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-041",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="SAT",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()

        # Mock BonusCalculator
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator

        # 触发奖金计算
        trigger_bonus_calculation(db_session, order, "PASSED")

        # 验证调用了奖金计算
        mock_calculator.trigger_acceptance_bonus_calculation.assert_called_once()

        # SAT和FAT使用同一个方法，验证验收类型正确传递
        call_args = mock_calculator.trigger_acceptance_bonus_calculation.call_args
        assert call_args[0][1].acceptance_type == "SAT"

    @patch("app.services.bonus.BonusCalculator")
    def test_bonus_not_triggered_on_failed(
        self, mock_calculator_class, db_session: Session
    ):
        """验收失败不应触发奖金计算"""
        # 创建测试数据
        project = Project(
            project_code="PJ-TEST-042",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-042",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-042",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()

        # Mock BonusCalculator
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator

        # 验收失败，不应触发奖金计算
        trigger_bonus_calculation(db_session, order, "FAILED")

        # 验证未调用奖金计算
        mock_calculator.trigger_acceptance_bonus_calculation.assert_not_called()


@pytest.mark.unit
@pytest.mark.integration
class TestHandleProgressIntegrationIntegration:
    """集成测试：进度联动"""

    @patch("app.services.progress_integration_service.ProgressIntegrationService")
    def test_acceptance_failed_blocks_milestones(
        self, mock_service_class, db_session: Session
    ):
        """验收失败应阻塞里程碑"""
        # 创建测试数据
        project = Project(
            project_code="PJ-TEST-050",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-050",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-050",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()

        # Mock ProgressIntegrationService
        mock_service = MagicMock()
        mock_service.handle_acceptance_failed.return_value = [
            "milestone-1",
            "milestone-2",
        ]
        mock_service_class.return_value = mock_service

        # 处理验收失败
        result = handle_progress_integration(db_session, order, "FAILED")

        # 验证结果
        assert "blocked_milestones" in result
        assert len(result["blocked_milestones"]) == 2

        # 验证调用了正确的服务方法
        mock_service.handle_acceptance_failed.assert_called_once_with(order)

    @patch("app.services.progress_integration_service.ProgressIntegrationService")
    def test_acceptance_passed_unblocks_milestones(
        self, mock_service_class, db_session: Session
    ):
        """验收通过应解除里程碑阻塞"""
        # 创建测试数据
        project = Project(
            project_code="PJ-TEST-051",
            project_name="测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-051",
            machine_name="测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        order = AcceptanceOrder(
            order_no="AO-TEST-051",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()

        # Mock ProgressIntegrationService
        mock_service = MagicMock()
        mock_service.handle_acceptance_passed.return_value = ["milestone-3"]
        mock_service_class.return_value = mock_service

        # 处理验收通过
        result = handle_progress_integration(db_session, order, "PASSED")

        # 验证结果
        assert "unblocked_milestones" in result
        assert len(result["unblocked_milestones"]) == 1

        # 验证调用了正确的服务方法
        mock_service.handle_acceptance_passed.assert_called_once_with(order)


@pytest.mark.unit
@pytest.mark.integration
class TestCompleteAcceptanceWorkflow:
    """端到端测试：完整的验收流程"""

    @patch("app.services.bonus.BonusCalculator")
    @patch("app.services.progress_integration_service.ProgressIntegrationService")
    @patch("app.services.status_transition_service.StatusTransitionService")
    @patch("app.services.invoice_auto_service.InvoiceAutoService")
    def test_fat_complete_workflow(
        self,
        mock_invoice_service_class,
        mock_status_service_class,
        mock_progress_service_class,
        mock_bonus_service_class,
        db_session: Session,
    ):
        """完整的FAT验收流程"""
        # 创建完整测试数据
        project = Project(
            project_code="PJ-TEST-100",
            project_name="完整测试项目",
            stage="S6",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()  # 确保 project.id 生成

        machine = Machine(
            project_id=project.id,
            machine_code="M-100",
            machine_name="完整测试设备",
            machine_type="TEST",
            status="TESTING",
        )
        db_session.add(machine)
        db_session.flush()  # 确保 machine.id 生成

        # 创建验收单
        order = AcceptanceOrder(
            order_no="AO-TEST-100",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            status="IN_PROGRESS",
            total_items=2,
            passed_items=2,
            failed_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.flush()  # 确保 order.id 生成

        # 创建已完成的检查项
        for i in range(2):
            item = AcceptanceOrderItem(
                order_id=order.id,
                category_code="CAT1",
                category_name="分类1",
                item_code=f"ITEM-10{i}",
                item_name=f"检查项{i}",
                is_required=True,
                result_status="PASSED",
            )
            db_session.add(item)

        db_session.commit()

        # Mock 各个服务
        mock_invoice_service = MagicMock()
        mock_invoice_service.check_and_create_invoice_request.return_value = {
            "success": True,
            "invoice_requests": [],
        }
        mock_invoice_service_class.return_value = mock_invoice_service

        mock_status_service = MagicMock()
        mock_status_service_class.return_value = mock_status_service

        mock_progress_service = MagicMock()
        mock_progress_service.handle_acceptance_passed.return_value = []
        mock_progress_service_class.return_value = mock_progress_service

        mock_bonus_calculator = MagicMock()
        mock_bonus_service_class.return_value = mock_bonus_calculator

        # 执行完整流程
        # 1. 验证必检项
        validate_required_check_items(db_session, order.id)

        # 2. 更新验收单状态
        update_acceptance_order_status(
            db_session,
            order,
            overall_result="PASSED",
            conclusion="FAT验收通过",
            conditions=None,
        )

        # 3. 处理验收状态联动
        handle_acceptance_status_transition(db_session, order, "PASSED")

        # 4. 处理进度联动
        handle_progress_integration(db_session, order, "PASSED")

        # 5. 触发开票
        trigger_invoice_on_acceptance(db_session, order.id, auto_trigger=True)

        # 6. 触发奖金计算
        trigger_bonus_calculation(db_session, order, "PASSED")

        # 验证所有步骤都执行了
        db_session.refresh(order)
        assert order.status == "COMPLETED"
        assert order.overall_result == "PASSED"
        assert order.actual_end_date is not None

        # 验证各个服务被调用
        mock_status_service.handle_fat_passed.assert_called_once()
        mock_progress_service.handle_acceptance_passed.assert_called_once()
        mock_bonus_calculator.trigger_acceptance_bonus_calculation.assert_called_once()
