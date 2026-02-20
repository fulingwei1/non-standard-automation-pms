# -*- coding: utf-8 -*-
"""
外协订单审批适配器增强测试
补充覆盖核心业务逻辑和异常场景,提升覆盖率到60%+
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime

from app.services.approval_engine.adapters.outsourcing import OutsourcingOrderApprovalAdapter


@pytest.fixture
def db_mock():
    """数据库mock"""
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
    order.order_title = "加工订单-机架焊接"
    order.order_type = "WELDING"
    order.order_description = "机架焊接加工"
    order.status = "DRAFT"
    order.total_amount = 50000.00
    order.tax_rate = 0.13
    order.tax_amount = 6500.00
    order.amount_with_tax = 56500.00
    order.required_date = date(2024, 3, 15)
    order.estimated_date = date(2024, 3, 10)
    order.actual_date = None
    order.payment_status = "UNPAID"
    order.paid_amount = 0.0
    order.contract_no = "CON-001"
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


class TestGetEntity:
    """测试获取实体"""
    
    def test_get_entity_found(self, adapter, db_mock, sample_order):
        """测试找到订单"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        result = adapter.get_entity(1)
        
        assert result == sample_order
    
    def test_get_entity_not_found(self, adapter, db_mock):
        """测试订单不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        result = adapter.get_entity(999)
        
        assert result is None


class TestGetEntityData:
    """测试获取实体数据"""
    
    def test_get_entity_data_not_found(self, adapter, db_mock):
        """测试订单不存在时返回空字典"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        result = adapter.get_entity_data(999)
        
        assert result == {}
    
    def test_get_entity_data_with_complete_info(self, adapter, db_mock, sample_order):
        """测试包含完整信息的订单数据"""
        # Mock项目
        project = MagicMock()
        project.project_code = "PRJ-001"
        project.project_name = "测试项目"
        project.status = "IN_PROGRESS"
        
        # Mock设备
        machine = MagicMock()
        machine.machine_code = "MC-001"
        machine.machine_name = "焊接机器人"
        
        # Mock供应商
        vendor = MagicMock()
        vendor.vendor_name = "XX焊接公司"
        vendor.vendor_code = "VD-001"
        
        # 准备查询链
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'OutsourcingOrder':
                mock_query.filter.return_value.first.return_value = sample_order
            elif model.__name__ == 'OutsourcingOrderItem':
                mock_query.filter.return_value.count.return_value = 3
            elif model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = project
            elif model.__name__ == 'Machine':
                mock_query.filter.return_value.first.return_value = machine
            elif model.__name__ == 'Vendor':
                mock_query.filter.return_value.first.return_value = vendor
            return mock_query
        
        db_mock.query.side_effect = query_side_effect
        
        result = adapter.get_entity_data(1)
        
        # 验证基本信息
        assert result["order_no"] == "OUT-2024-001"
        assert result["order_type"] == "WELDING"
        assert result["total_amount"] == 50000.00
        assert result["amount_with_tax"] == 56500.00
        assert result["item_count"] == 3
        
        # 验证关联信息
        assert result["project_code"] == "PRJ-001"
        assert result["project_name"] == "测试项目"
        assert result["machine_code"] == "MC-001"
        assert result["vendor_name"] == "XX焊接公司"
    
    def test_get_entity_data_without_relations(self, adapter, db_mock, sample_order):
        """测试无关联对象的订单数据"""
        sample_order.project_id = None
        sample_order.machine_id = None
        sample_order.vendor_id = None
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'OutsourcingOrder':
                mock_query.filter.return_value.first.return_value = sample_order
            elif model.__name__ == 'OutsourcingOrderItem':
                mock_query.filter.return_value.count.return_value = 0
            return mock_query
        
        db_mock.query.side_effect = query_side_effect
        
        result = adapter.get_entity_data(1)
        
        assert result["item_count"] == 0
        assert "project_code" not in result
        assert "machine_code" not in result


class TestLifecycleCallbacks:
    """测试生命周期回调"""
    
    def test_on_submit(self, adapter, db_mock, sample_order, sample_instance):
        """测试提交时更新状态"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        adapter.on_submit(1, sample_instance)
        
        assert sample_order.status == "PENDING_APPROVAL"
        db_mock.flush.assert_called_once()
    
    def test_on_approved(self, adapter, db_mock, sample_order, sample_instance):
        """测试通过时更新状态"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        adapter.on_approved(1, sample_instance)
        
        assert sample_order.status == "APPROVED"
        db_mock.flush.assert_called_once()
    
    def test_on_rejected(self, adapter, db_mock, sample_order, sample_instance):
        """测试驳回时更新状态"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        adapter.on_rejected(1, sample_instance)
        
        assert sample_order.status == "REJECTED"
        db_mock.flush.assert_called_once()
    
    def test_on_withdrawn(self, adapter, db_mock, sample_order, sample_instance):
        """测试撤回时恢复草稿状态"""
        sample_order.status = "PENDING_APPROVAL"
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        adapter.on_withdrawn(1, sample_instance)
        
        assert sample_order.status == "DRAFT"
        db_mock.flush.assert_called_once()
    
    def test_callbacks_handle_none_entity(self, adapter, db_mock, sample_instance):
        """测试实体不存在时的回调处理"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        # 这些不应该抛出异常
        adapter.on_submit(999, sample_instance)
        adapter.on_approved(999, sample_instance)
        adapter.on_rejected(999, sample_instance)
        adapter.on_withdrawn(999, sample_instance)


class TestGenerateTitleAndSummary:
    """测试标题和摘要生成"""
    
    def test_generate_title_with_order(self, adapter, db_mock, sample_order):
        """测试生成包含订单信息的标题"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        title = adapter.generate_title(1)
        
        assert "外协订单审批" in title
        assert "OUT-2024-001" in title
        assert "加工订单-机架焊接" in title
    
    def test_generate_title_without_order_title(self, adapter, db_mock, sample_order):
        """测试订单无标题时的生成"""
        sample_order.order_title = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        title = adapter.generate_title(1)
        
        assert "外协订单审批 - OUT-2024-001" == title
    
    def test_generate_title_order_not_found(self, adapter, db_mock):
        """测试订单不存在时的标题"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        title = adapter.generate_title(999)
        
        assert title == "外协订单审批 - 999"
    
    def test_generate_summary_complete(self, adapter, db_mock, sample_order):
        """测试生成完整摘要"""
        # Mock供应商
        vendor = MagicMock()
        vendor.vendor_name = "XX焊接公司"
        
        # Mock项目
        project = MagicMock()
        project.project_name = "测试项目"
        
        # Mock设备
        machine = MagicMock()
        machine.machine_code = "MC-001"
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'OutsourcingOrder':
                mock_query.filter.return_value.first.return_value = sample_order
            elif model.__name__ == 'OutsourcingOrderItem':
                mock_query.filter.return_value.count.return_value = 5
            elif model.__name__ == 'Vendor':
                mock_query.filter.return_value.first.return_value = vendor
            elif model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = project
            elif model.__name__ == 'Machine':
                mock_query.filter.return_value.first.return_value = machine
            return mock_query
        
        db_mock.query.side_effect = query_side_effect
        
        summary = adapter.generate_summary(1)
        
        assert "订单编号: OUT-2024-001" in summary
        assert "外协商: XX焊接公司" in summary
        assert "订单类型: WELDING" in summary
        assert "订单金额: ¥56,500.00" in summary
        assert "明细行数: 5" in summary
        assert "要求交期: 2024-03-15" in summary
        assert "关联项目: 测试项目" in summary
        assert "关联设备: MC-001" in summary
    
    def test_generate_summary_order_not_found(self, adapter, db_mock):
        """测试订单不存在时返回空摘要"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        summary = adapter.generate_summary(999)
        
        assert summary == ""


class TestValidateSubmit:
    """测试提交验证"""
    
    def test_validate_submit_success(self, adapter, db_mock, sample_order):
        """测试验证通过"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 3
        
        valid, error = adapter.validate_submit(1)
        
        assert valid is True
        assert error is None
    
    def test_validate_submit_order_not_found(self, adapter, db_mock):
        """测试订单不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        valid, error = adapter.validate_submit(999)
        
        assert valid is False
        assert error == "外协订单不存在"
    
    def test_validate_submit_invalid_status(self, adapter, db_mock, sample_order):
        """测试无效的状态"""
        sample_order.status = "APPROVED"  # 已审批通过的不能再提交
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "不允许提交审批" in error
    
    def test_validate_submit_missing_vendor(self, adapter, db_mock, sample_order):
        """测试缺少供应商"""
        sample_order.vendor_id = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert error == "请选择外协商"
    
    def test_validate_submit_missing_project(self, adapter, db_mock, sample_order):
        """测试缺少关联项目"""
        sample_order.project_id = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert error == "请关联项目"
    
    def test_validate_submit_missing_title(self, adapter, db_mock, sample_order):
        """测试缺少订单标题"""
        sample_order.order_title = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert error == "请填写订单标题"
    
    def test_validate_submit_missing_type(self, adapter, db_mock, sample_order):
        """测试缺少订单类型"""
        sample_order.order_type = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert error == "请选择订单类型"
    
    def test_validate_submit_no_items(self, adapter, db_mock, sample_order):
        """测试没有订单明细"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 0
        
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert error == "外协订单至少需要一条明细"
    
    def test_validate_submit_invalid_amount(self, adapter, db_mock, sample_order):
        """测试无效金额"""
        sample_order.amount_with_tax = 0
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 3
        
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert error == "订单总金额必须大于0"
    
    def test_validate_submit_missing_required_date(self, adapter, db_mock, sample_order):
        """测试缺少要求交期"""
        sample_order.required_date = None
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 3
        
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert error == "请填写要求交期"
    
    def test_validate_submit_rejected_can_resubmit(self, adapter, db_mock, sample_order):
        """测试驳回后可以重新提交"""
        sample_order.status = "REJECTED"
        db_mock.query.return_value.filter.return_value.first.return_value = sample_order
        db_mock.query.return_value.filter.return_value.count.return_value = 3
        
        valid, error = adapter.validate_submit(1)
        
        assert valid is True
        assert error is None


class TestGetCcUserIds:
    """测试获取抄送人"""
    
    def test_get_cc_user_ids_with_project_manager(self, adapter, db_mock, sample_order):
        """测试包含项目经理"""
        # Mock项目
        project = MagicMock()
        project.manager_id = 200
        
        db_mock.query.return_value.filter.return_value.first.side_effect = [
            sample_order,  # 第一次查订单
            project        # 第二次查项目
        ]
        
        with patch.object(adapter, 'get_department_manager_user_ids_by_codes', return_value=[300]):
            cc_ids = adapter.get_cc_user_ids(1)
        
        assert 200 in cc_ids  # 项目经理
        assert 300 in cc_ids  # 生产部门负责人
    
    def test_get_cc_user_ids_without_project_manager(self, adapter, db_mock, sample_order):
        """测试项目无经理"""
        project = MagicMock()
        project.manager_id = None
        
        db_mock.query.return_value.filter.return_value.first.side_effect = [
            sample_order,
            project
        ]
        
        with patch.object(adapter, 'get_department_manager_user_ids_by_codes', return_value=[]):
            with patch.object(adapter, 'get_department_manager_user_id', return_value=300):
                cc_ids = adapter.get_cc_user_ids(1)
        
        assert 300 in cc_ids
    
    def test_get_cc_user_ids_no_duplicates(self, adapter, db_mock, sample_order):
        """测试去重"""
        project = MagicMock()
        project.manager_id = 200
        
        db_mock.query.return_value.filter.return_value.first.side_effect = [
            sample_order,
            project
        ]
        
        with patch.object(adapter, 'get_department_manager_user_ids_by_codes', return_value=[200, 300]):
            cc_ids = adapter.get_cc_user_ids(1)
        
        assert len(cc_ids) == len(set(cc_ids))  # 确保没有重复
    
    def test_get_cc_user_ids_order_not_found(self, adapter, db_mock):
        """测试订单不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        cc_ids = adapter.get_cc_user_ids(999)
        
        assert cc_ids == []
