# -*- coding: utf-8 -*-
"""
外协订单审批适配器增强单元测试

测试覆盖：
- get_entity
- get_entity_data
- on_submit / on_approved / on_rejected / on_withdrawn
- generate_title / generate_summary
- validate_submit
- get_cc_user_ids
- 辅助方法 (get_department_manager_user_id 等)

目标覆盖率: 70%+
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date, datetime
from decimal import Decimal

from app.services.approval_engine.adapters.outsourcing import OutsourcingOrderApprovalAdapter


@pytest.fixture
def db_mock():
    """数据库 session mock"""
    return MagicMock()


@pytest.fixture
def adapter(db_mock):
    """适配器实例"""
    return OutsourcingOrderApprovalAdapter(db_mock)


@pytest.fixture
def sample_order():
    """示例外协订单"""
    order = MagicMock()
    order.id = 1
    order.order_no = "OUT-2024-001"
    order.order_title = "机架焊接加工"
    order.order_type = "WELDING"
    order.order_description = "机架主体焊接加工"
    order.status = "DRAFT"
    order.total_amount = Decimal("50000.00")
    order.tax_rate = Decimal("0.13")
    order.tax_amount = Decimal("6500.00")
    order.amount_with_tax = Decimal("56500.00")
    order.required_date = date(2024, 3, 15)
    order.estimated_date = date(2024, 3, 10)
    order.actual_date = None
    order.payment_status = "UNPAID"
    order.paid_amount = Decimal("0.00")
    order.contract_no = "CON-2024-001"
    order.project_id = 10
    order.machine_id = 20
    order.vendor_id = 5
    order.created_by = 100
    return order


@pytest.fixture
def sample_instance():
    """示例审批实例"""
    instance = MagicMock()
    instance.id = 50
    instance.status = "APPROVED"
    instance.template_id = 5
    return instance


# ==================== 测试 get_entity ====================

class TestGetEntity:
    """测试 get_entity 方法"""

    def test_get_entity_found(self, adapter, db_mock, sample_order):
        """测试成功获取订单"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        result = adapter.get_entity(1)

        assert result == sample_order
        db_mock.query.assert_called_once()

    def test_get_entity_not_found(self, adapter, db_mock):
        """测试订单不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None

        result = adapter.get_entity(999)

        assert result is None

    def test_get_entity_zero_id(self, adapter, db_mock):
        """测试 ID 为 0 的情况"""
        db_mock.query.return_value.filter.return_value.first.return_value = None

        result = adapter.get_entity(0)

        assert result is None


# ==================== 测试 get_entity_data ====================

class TestGetEntityData:
    """测试 get_entity_data 方法"""

    def test_get_entity_data_not_found(self, adapter, db_mock):
        """测试订单不存在时返回空字典"""
        db_mock.query.return_value.filter.return_value.first.return_value = None

        result = adapter.get_entity_data(999)

        assert result == {}

    def test_get_entity_data_basic_info(self, adapter, db_mock, sample_order):
        """测试基础订单信息"""
        # Mock 订单查询
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        # Mock 订单明细数量
        db_mock.query.return_value.filter.return_value.count.return_value = 3

        result = adapter.get_entity_data(1)

        assert result["order_no"] == "OUT-2024-001"
        assert result["order_title"] == "机架焊接加工"
        assert result["order_type"] == "WELDING"
        assert result["status"] == "DRAFT"
        assert result["total_amount"] == 50000.0
        assert result["tax_rate"] == 0.13
        assert result["amount_with_tax"] == 56500.0
        assert result["item_count"] == 3
        assert result["vendor_id"] == 5
        assert result["project_id"] == 10

    def test_get_entity_data_with_project_info(self, adapter, db_mock, sample_order):
        """测试包含项目信息"""
        # Mock 订单
        db_mock.query.return_value.filter.return_value.first.side_effect = [
            sample_order,  # 第一次调用：获取订单
            MagicMock(project_code="PRJ-001", project_name="测试项目", status="IN_PROGRESS"),  # 第二次：项目
            None,  # 第三次：设备查询（无设备）
            None,  # 第四次：外协商查询（无外协商）
        ]
        
        # Mock 明细数量
        db_mock.query.return_value.filter.return_value.count.return_value = 2

        result = adapter.get_entity_data(1)

        assert result["project_code"] == "PRJ-001"
        assert result["project_name"] == "测试项目"
        assert result["project_status"] == "IN_PROGRESS"

    def test_get_entity_data_with_machine_info(self, adapter, db_mock, sample_order):
        """测试包含设备信息"""
        machine = MagicMock()
        machine.machine_code = "MC-001"
        machine.machine_name = "焊接机1号"
        
        db_mock.query.return_value.filter.return_value.first.side_effect = [
            sample_order,  # 第一次：订单
            None,  # 第二次：项目查询（无项目）
            machine,  # 第三次：设备查询
            None,  # 第四次：外协商查询（无外协商）
        ]
        db_mock.query.return_value.filter.return_value.count.return_value = 1

        result = adapter.get_entity_data(1)

        assert result["machine_code"] == "MC-001"
        assert result["machine_name"] == "焊接机1号"

    def test_get_entity_data_with_vendor_info(self, adapter, db_mock, sample_order):
        """测试包含外协商信息"""
        vendor = MagicMock()
        vendor.vendor_name = "XX焊接厂"
        vendor.vendor_code = "VEN-001"
        
        db_mock.query.return_value.filter.return_value.first.side_effect = [
            sample_order,
            None,  # 项目
            None,  # 设备
            vendor,  # 外协商
        ]
        db_mock.query.return_value.filter.return_value.count.return_value = 4

        result = adapter.get_entity_data(1)

        assert result["vendor_name"] == "XX焊接厂"
        assert result["vendor_code"] == "VEN-001"

    def test_get_entity_data_without_optional_fields(self, adapter, db_mock):
        """测试没有可选字段的订单"""
        order = MagicMock()
        order.order_no = "OUT-2024-002"
        order.order_title = None
        order.order_type = "MACHINING"
        order.order_description = None
        order.status = "DRAFT"
        order.total_amount = None
        order.tax_rate = None
        order.tax_amount = None
        order.amount_with_tax = None
        order.required_date = None
        order.estimated_date = None
        order.actual_date = None
        order.payment_status = "UNPAID"
        order.paid_amount = None
        order.contract_no = None
        order.project_id = None
        order.machine_id = None
        order.vendor_id = None
        order.created_by = 1

        db_mock.query.return_value.filter.return_value.first.return_value = order
        db_mock.query.return_value.filter.return_value.count.return_value = 0

        result = adapter.get_entity_data(999)

        assert result["total_amount"] == 0
        assert result["tax_rate"] == 0
        assert result["amount_with_tax"] == 0
        assert result["required_date"] is None
        assert result["item_count"] == 0

    def test_get_entity_data_with_dates(self, adapter, db_mock, sample_order):
        """测试日期字段格式化"""
        sample_order.required_date = date(2024, 3, 15)
        sample_order.estimated_date = date(2024, 3, 10)
        sample_order.actual_date = date(2024, 3, 20)

        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 1

        result = adapter.get_entity_data(1)

        assert result["required_date"] == "2024-03-15"
        assert result["estimated_date"] == "2024-03-10"
        assert result["actual_date"] == "2024-03-20"


# ==================== 测试状态回调方法 ====================

class TestStatusCallbacks:
    """测试状态变更回调"""

    def test_on_submit_success(self, adapter, db_mock, sample_order, sample_instance):
        """测试提交审批回调"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        adapter.on_submit(1, sample_instance)

        assert sample_order.status == "PENDING_APPROVAL"
        db_mock.flush.assert_called_once()

    def test_on_submit_order_not_found(self, adapter, db_mock, sample_instance):
        """测试提交时订单不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None

        adapter.on_submit(999, sample_instance)

        db_mock.flush.assert_not_called()

    def test_on_approved_success(self, adapter, db_mock, sample_order, sample_instance):
        """测试审批通过回调"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        adapter.on_approved(1, sample_instance)

        assert sample_order.status == "APPROVED"
        db_mock.flush.assert_called_once()

    def test_on_approved_order_not_found(self, adapter, db_mock, sample_instance):
        """测试审批通过时订单不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None

        adapter.on_approved(999, sample_instance)

        db_mock.flush.assert_not_called()

    def test_on_rejected_success(self, adapter, db_mock, sample_order, sample_instance):
        """测试审批驳回回调"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        adapter.on_rejected(1, sample_instance)

        assert sample_order.status == "REJECTED"
        db_mock.flush.assert_called_once()

    def test_on_rejected_order_not_found(self, adapter, db_mock, sample_instance):
        """测试驳回时订单不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None

        adapter.on_rejected(999, sample_instance)

        db_mock.flush.assert_not_called()

    def test_on_withdrawn_success(self, adapter, db_mock, sample_order, sample_instance):
        """测试撤回审批回调"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        adapter.on_withdrawn(1, sample_instance)

        assert sample_order.status == "DRAFT"
        db_mock.flush.assert_called_once()

    def test_on_withdrawn_order_not_found(self, adapter, db_mock, sample_instance):
        """测试撤回时订单不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None

        adapter.on_withdrawn(999, sample_instance)

        db_mock.flush.assert_not_called()


# ==================== 测试 generate_title ====================

class TestGenerateTitle:
    """测试生成审批标题"""

    def test_generate_title_with_order_title(self, adapter, db_mock, sample_order):
        """测试包含订单标题的情况"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        result = adapter.generate_title(1)

        assert result == "外协订单审批 - OUT-2024-001 - 机架焊接加工"

    def test_generate_title_without_order_title(self, adapter, db_mock, sample_order):
        """测试没有订单标题的情况"""
        sample_order.order_title = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        result = adapter.generate_title(1)

        assert result == "外协订单审批 - OUT-2024-001"

    def test_generate_title_order_not_found(self, adapter, db_mock):
        """测试订单不存在时的标题"""
        db_mock.query.return_value.filter.return_value.first.return_value = None

        result = adapter.generate_title(999)

        assert result == "外协订单审批 - 999"

    def test_generate_title_empty_order_no(self, adapter, db_mock, sample_order):
        """测试订单号为空的情况"""
        sample_order.order_no = ""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        result = adapter.generate_title(1)

        assert result == "外协订单审批 -  - 机架焊接加工"


# ==================== 测试 generate_summary ====================

class TestGenerateSummary:
    """测试生成审批摘要"""

    def test_generate_summary_complete_info(self, adapter, db_mock, sample_order):
        """测试完整信息的摘要"""
        vendor = MagicMock()
        vendor.vendor_name = "XX焊接厂"
        
        project = MagicMock()
        project.project_name = "测试项目"
        
        machine = MagicMock()
        machine.machine_code = "MC-001"

        db_mock.query.return_value.filter.return_value.first.side_effect = [
            sample_order,
            vendor,
            project,
            machine,
        ]
        db_mock.query.return_value.filter.return_value.count.return_value = 3

        result = adapter.generate_summary(1)

        assert "OUT-2024-001" in result
        assert "XX焊接厂" in result
        assert "WELDING" in result
        assert "¥56,500.00" in result
        assert "明细行数: 3" in result
        assert "2024-03-15" in result
        assert "测试项目" in result
        assert "MC-001" in result

    def test_generate_summary_order_not_found(self, adapter, db_mock):
        """测试订单不存在时返回空字符串"""
        db_mock.query.return_value.filter.return_value.first.return_value = None

        result = adapter.generate_summary(999)

        assert result == ""

    def test_generate_summary_without_vendor(self, adapter, db_mock, sample_order):
        """测试没有外协商的情况"""
        sample_order.vendor_id = None
        
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 2

        result = adapter.generate_summary(1)

        assert "未指定" in result

    def test_generate_summary_without_amount(self, adapter, db_mock, sample_order):
        """测试没有金额的情况"""
        sample_order.amount_with_tax = None
        
        db_mock.query.return_value.filter.return_value.first.side_effect = [
            sample_order,  # 第一次：获取订单
            MagicMock(vendor_name="测试外协商"),  # 第二次：外协商
            None,  # 第三次：项目查询（无项目）
            None,  # 第四次：设备查询（无设备）
        ]
        db_mock.query.return_value.filter.return_value.count.return_value = 1

        result = adapter.generate_summary(1)

        assert "未填写" in result

    def test_generate_summary_without_optional_info(self, adapter, db_mock, sample_order):
        """测试没有可选信息（项目、设备等）"""
        sample_order.required_date = None
        sample_order.project_id = None
        sample_order.machine_id = None

        db_mock.query.return_value.filter.return_value.first.side_effect = [
            sample_order,
            MagicMock(vendor_name="外协商A"),
        ]
        db_mock.query.return_value.filter.return_value.count.return_value = 5

        result = adapter.generate_summary(1)

        # 不应包含日期、项目、设备信息
        parts = result.split(" | ")
        assert len(parts) == 5  # 订单号、外协商、类型、金额、明细数


# ==================== 测试 validate_submit ====================

class TestValidateSubmit:
    """测试提交验证"""

    def test_validate_submit_success(self, adapter, db_mock, sample_order):
        """测试所有条件都满足"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 2

        can_submit, error = adapter.validate_submit(1)

        assert can_submit is True
        assert error is None

    def test_validate_submit_order_not_found(self, adapter, db_mock):
        """测试订单不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None

        can_submit, error = adapter.validate_submit(999)

        assert can_submit is False
        assert error == "外协订单不存在"

    def test_validate_submit_invalid_status(self, adapter, db_mock, sample_order):
        """测试无效状态"""
        sample_order.status = "APPROVED"
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        can_submit, error = adapter.validate_submit(1)

        assert can_submit is False
        assert "不允许提交审批" in error

    def test_validate_submit_missing_vendor(self, adapter, db_mock, sample_order):
        """测试缺少外协商"""
        sample_order.vendor_id = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        can_submit, error = adapter.validate_submit(1)

        assert can_submit is False
        assert error == "请选择外协商"

    def test_validate_submit_missing_project(self, adapter, db_mock, sample_order):
        """测试缺少项目"""
        sample_order.project_id = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        can_submit, error = adapter.validate_submit(1)

        assert can_submit is False
        assert error == "请关联项目"

    def test_validate_submit_missing_title(self, adapter, db_mock, sample_order):
        """测试缺少订单标题"""
        sample_order.order_title = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        can_submit, error = adapter.validate_submit(1)

        assert can_submit is False
        assert error == "请填写订单标题"

    def test_validate_submit_missing_order_type(self, adapter, db_mock, sample_order):
        """测试缺少订单类型"""
        sample_order.order_type = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order

        can_submit, error = adapter.validate_submit(1)

        assert can_submit is False
        assert error == "请选择订单类型"

    def test_validate_submit_no_items(self, adapter, db_mock, sample_order):
        """测试没有订单明细"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 0

        can_submit, error = adapter.validate_submit(1)

        assert can_submit is False
        assert error == "外协订单至少需要一条明细"

    def test_validate_submit_zero_amount(self, adapter, db_mock, sample_order):
        """测试金额为0"""
        sample_order.amount_with_tax = Decimal("0")
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 1

        can_submit, error = adapter.validate_submit(1)

        assert can_submit is False
        assert error == "订单总金额必须大于0"

    def test_validate_submit_negative_amount(self, adapter, db_mock, sample_order):
        """测试负金额"""
        sample_order.amount_with_tax = Decimal("-100")
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 1

        can_submit, error = adapter.validate_submit(1)

        assert can_submit is False
        assert error == "订单总金额必须大于0"

    def test_validate_submit_missing_required_date(self, adapter, db_mock, sample_order):
        """测试缺少要求交期"""
        sample_order.required_date = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 3

        can_submit, error = adapter.validate_submit(1)

        assert can_submit is False
        assert error == "请填写要求交期"

    def test_validate_submit_rejected_status(self, adapter, db_mock, sample_order):
        """测试从驳回状态提交"""
        sample_order.status = "REJECTED"
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 1

        can_submit, error = adapter.validate_submit(1)

        assert can_submit is True
        assert error is None


# ==================== 测试 get_cc_user_ids ====================

class TestGetCcUserIds:
    """测试获取抄送人"""

    def test_get_cc_user_ids_order_not_found(self, adapter, db_mock):
        """测试订单不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None

        result = adapter.get_cc_user_ids(999)

        assert result == []

    def test_get_cc_user_ids_no_project(self, adapter, db_mock, sample_order):
        """测试没有关联项目"""
        sample_order.project_id = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        with patch.object(adapter, 'get_department_manager_user_ids_by_codes', return_value=[]):
            with patch.object(adapter, 'get_department_manager_user_id', return_value=None):
                result = adapter.get_cc_user_ids(1)

        assert result == []

    def test_get_cc_user_ids_with_project_manager(self, adapter, db_mock, sample_order):
        """测试项目经理抄送"""
        project = MagicMock()
        project.manager_id = 200
        
        db_mock.query.return_value.filter.return_value.first.side_effect = [
            sample_order,
            project,
        ]
        
        with patch.object(adapter, 'get_department_manager_user_ids_by_codes', return_value=[]):
            with patch.object(adapter, 'get_department_manager_user_id', return_value=None):
                result = adapter.get_cc_user_ids(1)

        assert 200 in result

    def test_get_cc_user_ids_with_prod_dept_manager(self, adapter, db_mock, sample_order):
        """测试生产部门负责人抄送"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        with patch.object(adapter, 'get_department_manager_user_ids_by_codes', return_value=[300, 301]):
            result = adapter.get_cc_user_ids(1)

        assert 300 in result
        assert 301 in result

    def test_get_cc_user_ids_with_fallback_dept_name(self, adapter, db_mock, sample_order):
        """测试备用部门名称查找"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        with patch.object(adapter, 'get_department_manager_user_ids_by_codes', return_value=[]):
            with patch.object(adapter, 'get_department_manager_user_id', return_value=400):
                result = adapter.get_cc_user_ids(1)

        assert 400 in result

    def test_get_cc_user_ids_deduplication(self, adapter, db_mock, sample_order):
        """测试去重"""
        project = MagicMock()
        project.manager_id = 500
        
        db_mock.query.return_value.filter.return_value.first.side_effect = [
            sample_order,
            project,
        ]
        
        with patch.object(adapter, 'get_department_manager_user_ids_by_codes', return_value=[500, 501]):
            result = adapter.get_cc_user_ids(1)

        # 500 应该只出现一次
        assert result.count(500) == 1
        assert 501 in result


# ==================== 测试辅助方法 ====================

class TestHelperMethods:
    """测试辅助方法（从基类继承）"""

    @patch('app.models.organization.Department')
    @patch('app.models.organization.Employee')
    @patch('app.models.user.User')
    def test_get_department_manager_user_id_success(self, mock_user, mock_employee, mock_dept, adapter, db_mock):
        """测试成功获取部门负责人"""
        dept = MagicMock()
        dept.manager_id = 10
        
        employee = MagicMock()
        employee.name = "张三"
        employee.employee_code = "EMP001"
        
        user = MagicMock()
        user.id = 100
        
        db_mock.query.return_value.filter.return_value.first.side_effect = [dept, employee, user]

        result = adapter.get_department_manager_user_id("生产部")

        assert result == 100

    @patch('app.models.organization.Department')
    def test_get_department_manager_user_id_dept_not_found(self, mock_dept, adapter, db_mock):
        """测试部门不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None

        result = adapter.get_department_manager_user_id("不存在的部门")

        assert result is None

    @patch('app.models.organization.Department')
    @patch('app.models.organization.Employee')
    def test_get_department_manager_user_id_no_manager(self, mock_employee, mock_dept, adapter, db_mock):
        """测试部门没有负责人"""
        dept = MagicMock()
        dept.manager_id = None
        
        db_mock.query.return_value.filter.return_value.first.return_value = dept

        result = adapter.get_department_manager_user_id("生产部")

        assert result is None

    @patch('app.models.organization.Department')
    @patch('app.models.organization.Employee')
    @patch('app.models.user.User')
    def test_get_department_manager_user_ids_by_codes_success(self, mock_user, mock_employee, mock_dept, adapter, db_mock):
        """测试批量获取部门负责人"""
        dept1 = MagicMock()
        dept1.manager_id = 10
        
        dept2 = MagicMock()
        dept2.manager_id = 20
        
        emp1 = MagicMock()
        emp1.name = "张三"
        emp1.employee_code = "EMP001"
        
        emp2 = MagicMock()
        emp2.name = "李四"
        emp2.employee_code = "EMP002"
        
        user1 = MagicMock()
        user1.id = 100
        
        user2 = MagicMock()
        user2.id = 200

        db_mock.query.return_value.filter.return_value.all.side_effect = [
            [dept1, dept2],
            [emp1, emp2],
            [user1, user2],
        ]

        result = adapter.get_department_manager_user_ids_by_codes(['PROD', 'QA'])

        assert 100 in result
        assert 200 in result

    @patch('app.models.organization.Department')
    def test_get_department_manager_user_ids_by_codes_empty_list(self, mock_dept, adapter, db_mock):
        """测试空部门列表"""
        db_mock.query.return_value.filter.return_value.all.return_value = []

        result = adapter.get_department_manager_user_ids_by_codes([])

        assert result == []


# ==================== 属性测试 ====================

class TestAdapterProperties:
    """测试适配器属性"""

    def test_entity_type(self, adapter):
        """测试实体类型"""
        assert adapter.entity_type == "OUTSOURCING_ORDER"

    def test_db_attribute(self, adapter, db_mock):
        """测试数据库 session"""
        assert adapter.db == db_mock


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
