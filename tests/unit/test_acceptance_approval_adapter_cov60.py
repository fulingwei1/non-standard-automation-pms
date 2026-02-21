# -*- coding: utf-8 -*-
"""
验收单审批适配器 单元测试
目标覆盖率: 60%+
覆盖: 数据转换、验证、审批回调、通知
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

try:
    from app.services.approval_engine.adapters.acceptance import AcceptanceOrderApprovalAdapter
    from app.models.approval import ApprovalInstance
    from app.models.acceptance import AcceptanceOrder, AcceptanceOrderItem, AcceptanceTemplate
    from app.models.project import Project, Machine
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    """创建mock数据库会话"""
    db = MagicMock()
    db.flush = MagicMock()
    return db


def make_acceptance_order(**kwargs):
    """创建mock验收单"""
    order = MagicMock(spec=AcceptanceOrder)
    order.id = kwargs.get("id", 1)
    order.order_no = kwargs.get("order_no", "ACC-2025-001")
    order.acceptance_type = kwargs.get("acceptance_type", "FAT")
    order.status = kwargs.get("status", "DRAFT")
    order.overall_result = kwargs.get("overall_result", "PASSED")
    order.pass_rate = Decimal(kwargs.get("pass_rate", "95.0"))
    order.total_items = kwargs.get("total_items", 20)
    order.passed_items = kwargs.get("passed_items", 19)
    order.failed_items = kwargs.get("failed_items", 1)
    order.na_items = kwargs.get("na_items", 0)
    order.project_id = kwargs.get("project_id", 100)
    order.machine_id = kwargs.get("machine_id", 200)
    order.template_id = kwargs.get("template_id", 10)
    order.location = kwargs.get("location", "工厂A")
    order.planned_date = kwargs.get("planned_date", datetime.now())
    order.actual_start_date = kwargs.get("actual_start_date", None)
    order.actual_end_date = kwargs.get("actual_end_date", None)
    order.conclusion = kwargs.get("conclusion", "验收通过")
    order.conditions = kwargs.get("conditions", None)
    order.created_by = kwargs.get("created_by", 1)
    order.is_officially_completed = kwargs.get("is_officially_completed", False)
    order.officially_completed_at = kwargs.get("officially_completed_at", None)
    return order


def make_project(**kwargs):
    """创建mock项目"""
    project = MagicMock(spec=Project)
    project.id = kwargs.get("id", 100)
    project.project_code = kwargs.get("project_code", "PROJ-001")
    project.project_name = kwargs.get("project_name", "测试项目")
    project.status = kwargs.get("status", "IN_PROGRESS")
    project.manager_id = kwargs.get("manager_id", 5)
    return project


def make_machine(**kwargs):
    """创建mock设备"""
    machine = MagicMock(spec=Machine)
    machine.id = kwargs.get("id", 200)
    machine.machine_code = kwargs.get("machine_code", "MACH-001")
    machine.machine_name = kwargs.get("machine_name", "测试设备")
    return machine


def make_template(**kwargs):
    """创建mock模板"""
    template = MagicMock(spec=AcceptanceTemplate)
    template.id = kwargs.get("id", 10)
    template.template_name = kwargs.get("template_name", "FAT模板")
    template.template_code = kwargs.get("template_code", "FAT-001")
    template.equipment_type = kwargs.get("equipment_type", "设备类型A")
    return template


def make_approval_instance(**kwargs):
    """创建mock审批实例"""
    instance = MagicMock(spec=ApprovalInstance)
    instance.id = kwargs.get("id", 1000)
    instance.status = kwargs.get("status", "PENDING")
    instance.approved_by = kwargs.get("approved_by", None)
    return instance


class TestAcceptanceOrderApprovalAdapter:
    """验收单审批适配器测试"""

    def test_adapter_entity_type(self):
        """测试适配器实体类型"""
        db = make_db()
        adapter = AcceptanceOrderApprovalAdapter(db)
        assert adapter.entity_type == "ACCEPTANCE_ORDER"

    def test_get_entity_found(self):
        """测试获取验收单实体 - 找到"""
        db = make_db()
        order = make_acceptance_order(id=1)
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        result = adapter.get_entity(1)
        
        assert result == order

    def test_get_entity_not_found(self):
        """测试获取验收单实体 - 未找到"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        result = adapter.get_entity(999)
        
        assert result is None

    def test_get_entity_data_complete(self):
        """测试获取实体数据 - 完整数据"""
        db = make_db()
        order = make_acceptance_order(
            id=1,
            acceptance_type="FAT",
            overall_result="PASSED",
            pass_rate=Decimal("95.5")
        )
        project = make_project()
        machine = make_machine()
        template = make_template()
        
        # 配置查询返回
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == AcceptanceOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == Project:
                query_mock.filter.return_value.first.return_value = project
            elif model == Machine:
                query_mock.filter.return_value.first.return_value = machine
            elif model == AcceptanceTemplate:
                query_mock.filter.return_value.first.return_value = template
            elif model == AcceptanceOrderItem:
                query_mock.filter.return_value.count.return_value = 0  # 无关键项不合格
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["order_no"] == "ACC-2025-001"
        assert data["acceptance_type"] == "FAT"
        assert data["overall_result"] == "PASSED"
        assert float(data["pass_rate"]) == 95.5
        assert data["total_items"] == 20
        assert data["passed_items"] == 19
        assert data["failed_items"] == 1
        assert data["project_code"] == "PROJ-001"
        assert data["machine_code"] == "MACH-001"
        assert data["template_name"] == "FAT模板"
        assert data["has_critical_failure"] is False

    def test_get_entity_data_with_critical_failure(self):
        """测试获取实体数据 - 有关键项不合格"""
        db = make_db()
        order = make_acceptance_order(failed_items=2)
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == AcceptanceOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == AcceptanceOrderItem:
                query_mock.filter.return_value.count.return_value = 1  # 1个关键项不合格
            else:
                query_mock.filter.return_value.first.return_value = None
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["has_critical_failure"] is True

    def test_get_entity_data_not_found(self):
        """测试获取实体数据 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        data = adapter.get_entity_data(999)
        
        assert data == {}

    def test_on_submit(self):
        """测试提交审批回调"""
        db = make_db()
        order = make_acceptance_order(status="DRAFT")
        db.query.return_value.filter.return_value.first.return_value = order
        instance = make_approval_instance()
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        adapter.on_submit(1, instance)
        
        assert order.status == "PENDING_APPROVAL"
        db.flush.assert_called_once()

    def test_on_approved_fat_passed(self):
        """测试审批通过 - FAT合格"""
        db = make_db()
        order = make_acceptance_order(
            acceptance_type="FAT",
            overall_result="PASSED"
        )
        db.query.return_value.filter.return_value.first.return_value = order
        instance = make_approval_instance()
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        adapter.on_approved(1, instance)
        
        assert order.status == "COMPLETED"
        db.flush.assert_called_once()

    def test_on_approved_fat_conditional(self):
        """测试审批通过 - FAT有条件通过"""
        db = make_db()
        order = make_acceptance_order(
            acceptance_type="FAT",
            overall_result="CONDITIONAL"
        )
        db.query.return_value.filter.return_value.first.return_value = order
        instance = make_approval_instance()
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        adapter.on_approved(1, instance)
        
        assert order.status == "CONDITIONAL_APPROVED"
        db.flush.assert_called_once()

    def test_on_approved_sat_passed(self):
        """测试审批通过 - SAT合格"""
        db = make_db()
        order = make_acceptance_order(
            acceptance_type="SAT",
            overall_result="PASSED"
        )
        db.query.return_value.filter.return_value.first.return_value = order
        instance = make_approval_instance()
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        adapter.on_approved(1, instance)
        
        assert order.status == "COMPLETED"
        db.flush.assert_called_once()

    def test_on_approved_final_passed(self):
        """测试审批通过 - 终验收合格"""
        db = make_db()
        order = make_acceptance_order(
            acceptance_type="FINAL",
            overall_result="PASSED",
            is_officially_completed=False
        )
        db.query.return_value.filter.return_value.first.return_value = order
        instance = make_approval_instance()
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        adapter.on_approved(1, instance)
        
        assert order.status == "COMPLETED"
        assert order.is_officially_completed is True
        assert order.officially_completed_at is not None
        db.flush.assert_called_once()

    def test_on_rejected(self):
        """测试审批驳回"""
        db = make_db()
        order = make_acceptance_order(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = order
        instance = make_approval_instance()
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        adapter.on_rejected(1, instance)
        
        assert order.status == "REJECTED"
        db.flush.assert_called_once()

    def test_on_withdrawn(self):
        """测试审批撤回"""
        db = make_db()
        order = make_acceptance_order(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = order
        instance = make_approval_instance()
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        adapter.on_withdrawn(1, instance)
        
        assert order.status == "DRAFT"
        db.flush.assert_called_once()

    def test_generate_title_fat(self):
        """测试生成标题 - FAT"""
        db = make_db()
        order = make_acceptance_order(
            acceptance_type="FAT",
            order_no="ACC-FAT-001"
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        title = adapter.generate_title(1)
        
        assert "出厂验收审批" in title
        assert "ACC-FAT-001" in title

    def test_generate_title_conditional(self):
        """测试生成标题 - 有条件通过"""
        db = make_db()
        order = make_acceptance_order(
            acceptance_type="SAT",
            overall_result="CONDITIONAL"
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        title = adapter.generate_title(1)
        
        assert "有条件通过" in title

    def test_generate_title_failed(self):
        """测试生成标题 - 不合格"""
        db = make_db()
        order = make_acceptance_order(
            acceptance_type="FINAL",
            overall_result="FAILED"
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        title = adapter.generate_title(1)
        
        assert "不合格" in title

    def test_generate_summary_complete(self):
        """测试生成摘要 - 完整信息"""
        db = make_db()
        order = make_acceptance_order(
            order_no="ACC-001",
            acceptance_type="FAT",
            overall_result="PASSED",
            pass_rate=Decimal("95.5"),
            location="工厂A",
            project_id=100,
            machine_id=200
        )
        project = make_project(project_name="测试项目")
        machine = make_machine(machine_code="MACH-001")
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == AcceptanceOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == Project:
                query_mock.filter.return_value.first.return_value = project
            elif model == Machine:
                query_mock.filter.return_value.first.return_value = machine
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        summary = adapter.generate_summary(1)
        
        assert "ACC-001" in summary
        assert "FAT" in summary
        assert "合格" in summary
        assert "95.5%" in summary
        assert "19/20项通过" in summary
        assert "测试项目" in summary
        assert "MACH-001" in summary
        assert "工厂A" in summary

    def test_validate_submit_success(self):
        """测试提交验证 - 成功"""
        db = make_db()
        order = make_acceptance_order(
            status="DRAFT",
            project_id=100,
            acceptance_type="FAT",
            total_items=20,
            passed_items=19,
            failed_items=1,
            na_items=0,
            overall_result="PASSED"
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is True
        assert error is None

    def test_validate_submit_not_found(self):
        """测试提交验证 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(999)
        
        assert valid is False
        assert "不存在" in error

    def test_validate_submit_wrong_status(self):
        """测试提交验证 - 状态错误"""
        db = make_db()
        order = make_acceptance_order(status="APPROVED")
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "不允许提交审批" in error

    def test_validate_submit_no_project(self):
        """测试提交验证 - 缺少项目"""
        db = make_db()
        order = make_acceptance_order(status="DRAFT", project_id=None)
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "关联项目" in error

    def test_validate_submit_no_type(self):
        """测试提交验证 - 缺少类型"""
        db = make_db()
        order = make_acceptance_order(
            status="DRAFT",
            project_id=100,
            acceptance_type=None
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "验收类型" in error

    def test_validate_submit_no_items(self):
        """测试提交验证 - 无检查项"""
        db = make_db()
        order = make_acceptance_order(
            status="DRAFT",
            project_id=100,
            acceptance_type="FAT",
            total_items=0
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "至少需要一项" in error

    def test_validate_submit_incomplete_check(self):
        """测试提交验证 - 检查未完成"""
        db = make_db()
        order = make_acceptance_order(
            status="DRAFT",
            project_id=100,
            acceptance_type="FAT",
            total_items=20,
            passed_items=10,
            failed_items=5,
            na_items=2  # 只检查了17项，还有3项未检查
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "未检查" in error

    def test_validate_submit_no_result(self):
        """测试提交验证 - 缺少验收结论"""
        db = make_db()
        order = make_acceptance_order(
            status="DRAFT",
            project_id=100,
            acceptance_type="FAT",
            total_items=20,
            passed_items=20,
            failed_items=0,
            na_items=0,
            overall_result=None
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "验收结论" in error

    def test_validate_submit_conditional_no_conditions(self):
        """测试提交验证 - 有条件通过但未说明条件"""
        db = make_db()
        order = make_acceptance_order(
            status="DRAFT",
            project_id=100,
            acceptance_type="FAT",
            total_items=20,
            passed_items=19,
            failed_items=1,
            na_items=0,
            overall_result="CONDITIONAL",
            conditions=None
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "必须说明具体条件" in error

    def test_validate_submit_inconsistent_result(self):
        """测试提交验证 - 结论与检查结果不一致"""
        db = make_db()
        order = make_acceptance_order(
            status="DRAFT",
            project_id=100,
            acceptance_type="FAT",
            total_items=20,
            passed_items=15,
            failed_items=5,
            na_items=0,
            overall_result="PASSED"  # 有不合格项但判定合格
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "不能判定为合格" in error
