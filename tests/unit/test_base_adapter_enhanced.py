# -*- coding: utf-8 -*-
"""
审批适配器基类增强单元测试

测试覆盖：
- 初始化和基础属性
- 抽象方法子类实现
- 回调方法（on_withdrawn, on_terminated）
- 审批人解析（resolve_approvers）
- 标题和摘要生成
- 表单数据获取
- 提交验证
- 抄送人列表
- 部门负责人查询（单个、批量）
- 项目销售负责人查询
- 边界条件和异常处理
"""

import unittest
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch, call

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalNodeDefinition
from app.services.approval_engine.adapters.base import ApprovalAdapter


# ==================== 测试用具体适配器 ====================

class ConcreteAdapter(ApprovalAdapter):
    """用于测试的具体适配器实现"""
    
    entity_type = "TestEntity"
    
    def __init__(self, db: Session):
        super().__init__(db)
        # 用于追踪回调调用
        self.callbacks_called = []
    
    def get_entity(self, entity_id: int) -> Any:
        """获取业务实体"""
        entity = Mock()
        entity.id = entity_id
        entity.name = f"Entity_{entity_id}"
        entity.status = "draft"
        return entity
    
    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """获取业务实体数据"""
        entity = self.get_entity(entity_id)
        return {
            "id": entity.id,
            "name": entity.name,
            "status": entity.status,
            "amount": 10000,
            "department": "Engineering"
        }
    
    def on_submit(self, entity_id: int, instance: ApprovalInstance):
        """审批提交时的回调"""
        self.callbacks_called.append(("on_submit", entity_id, instance.id))
    
    def on_approved(self, entity_id: int, instance: ApprovalInstance):
        """审批通过时的回调"""
        self.callbacks_called.append(("on_approved", entity_id, instance.id))
    
    def on_rejected(self, entity_id: int, instance: ApprovalInstance):
        """审批驳回时的回调"""
        self.callbacks_called.append(("on_rejected", entity_id, instance.id))


# ==================== 测试类 ====================

class TestApprovalAdapterBase(unittest.TestCase):
    """审批适配器基类测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.db = MagicMock(spec=Session)
        self.adapter = ConcreteAdapter(self.db)
    
    def tearDown(self):
        """测试后置清理"""
        self.db.reset_mock()


class TestInitialization(TestApprovalAdapterBase):
    """测试初始化"""
    
    def test_init_stores_db_session(self):
        """测试初始化存储数据库会话"""
        self.assertIs(self.adapter.db, self.db)
    
    def test_init_sets_entity_type(self):
        """测试初始化设置实体类型"""
        self.assertEqual(self.adapter.entity_type, "TestEntity")
    
    def test_base_adapter_entity_type_is_empty(self):
        """测试基类的实体类型为空"""
        self.assertEqual(ApprovalAdapter.entity_type, "")


class TestAbstractMethodImplementation(TestApprovalAdapterBase):
    """测试抽象方法的实现"""
    
    def test_get_entity_returns_entity_object(self):
        """测试获取实体返回实体对象"""
        entity = self.adapter.get_entity(123)
        self.assertEqual(entity.id, 123)
        self.assertEqual(entity.name, "Entity_123")
    
    def test_get_entity_data_returns_dict(self):
        """测试获取实体数据返回字典"""
        data = self.adapter.get_entity_data(456)
        self.assertIsInstance(data, dict)
        self.assertEqual(data["id"], 456)
        self.assertEqual(data["name"], "Entity_456")
        self.assertEqual(data["department"], "Engineering")
    
    def test_on_submit_callback_is_called(self):
        """测试提交回调被调用"""
        instance = Mock(spec=ApprovalInstance)
        instance.id = 1001
        
        self.adapter.on_submit(789, instance)
        
        self.assertIn(("on_submit", 789, 1001), self.adapter.callbacks_called)
    
    def test_on_approved_callback_is_called(self):
        """测试通过回调被调用"""
        instance = Mock(spec=ApprovalInstance)
        instance.id = 1002
        
        self.adapter.on_approved(890, instance)
        
        self.assertIn(("on_approved", 890, 1002), self.adapter.callbacks_called)
    
    def test_on_rejected_callback_is_called(self):
        """测试驳回回调被调用"""
        instance = Mock(spec=ApprovalInstance)
        instance.id = 1003
        
        self.adapter.on_rejected(901, instance)
        
        self.assertIn(("on_rejected", 901, 1003), self.adapter.callbacks_called)


class TestOptionalCallbacks(TestApprovalAdapterBase):
    """测试可选回调方法"""
    
    def test_on_withdrawn_default_implementation(self):
        """测试撤回回调的默认实现（不抛出异常）"""
        instance = Mock(spec=ApprovalInstance)
        instance.id = 2001
        
        # 默认实现应该不做任何事情，不抛出异常
        try:
            self.adapter.on_withdrawn(111, instance)
        except Exception as e:
            self.fail(f"on_withdrawn should not raise exception: {e}")
    
    def test_on_terminated_default_implementation(self):
        """测试终止回调的默认实现（不抛出异常）"""
        instance = Mock(spec=ApprovalInstance)
        instance.id = 2002
        
        # 默认实现应该不做任何事情，不抛出异常
        try:
            self.adapter.on_terminated(222, instance)
        except Exception as e:
            self.fail(f"on_terminated should not raise exception: {e}")


class TestResolveApprovers(TestApprovalAdapterBase):
    """测试审批人解析"""
    
    def test_resolve_approvers_returns_empty_list_by_default(self):
        """测试默认返回空列表"""
        node = Mock(spec=ApprovalNodeDefinition)
        context = {"amount": 5000}
        
        result = self.adapter.resolve_approvers(node, context)
        
        self.assertEqual(result, [])
        self.assertIsInstance(result, list)
    
    def test_resolve_approvers_with_empty_context(self):
        """测试空上下文"""
        node = Mock(spec=ApprovalNodeDefinition)
        result = self.adapter.resolve_approvers(node, {})
        self.assertEqual(result, [])
    
    def test_resolve_approvers_with_none_node(self):
        """测试节点为None的情况"""
        result = self.adapter.resolve_approvers(None, {"key": "value"})
        self.assertEqual(result, [])


class TestGenerateTitle(TestApprovalAdapterBase):
    """测试标题生成"""
    
    def test_generate_title_default_format(self):
        """测试默认标题格式"""
        title = self.adapter.generate_title(12345)
        self.assertEqual(title, "TestEntity审批 - 12345")
    
    def test_generate_title_with_different_entity_ids(self):
        """测试不同实体ID生成不同标题"""
        title1 = self.adapter.generate_title(100)
        title2 = self.adapter.generate_title(200)
        
        self.assertNotEqual(title1, title2)
        self.assertIn("100", title1)
        self.assertIn("200", title2)
    
    def test_generate_title_with_zero_id(self):
        """测试ID为0的情况"""
        title = self.adapter.generate_title(0)
        self.assertEqual(title, "TestEntity审批 - 0")


class TestGenerateSummary(TestApprovalAdapterBase):
    """测试摘要生成"""
    
    def test_generate_summary_returns_empty_string_by_default(self):
        """测试默认返回空字符串"""
        summary = self.adapter.generate_summary(999)
        self.assertEqual(summary, "")
    
    def test_generate_summary_with_different_entity_ids(self):
        """测试不同实体ID生成相同摘要（默认实现）"""
        summary1 = self.adapter.generate_summary(100)
        summary2 = self.adapter.generate_summary(200)
        
        self.assertEqual(summary1, summary2)
        self.assertEqual(summary1, "")


class TestGetFormData(TestApprovalAdapterBase):
    """测试表单数据获取"""
    
    def test_get_form_data_returns_entity_data(self):
        """测试默认返回实体数据"""
        form_data = self.adapter.get_form_data(777)
        
        self.assertIsInstance(form_data, dict)
        self.assertEqual(form_data["id"], 777)
        self.assertEqual(form_data["department"], "Engineering")
    
    def test_get_form_data_matches_get_entity_data(self):
        """测试表单数据与实体数据一致"""
        entity_id = 888
        form_data = self.adapter.get_form_data(entity_id)
        entity_data = self.adapter.get_entity_data(entity_id)
        
        self.assertEqual(form_data, entity_data)


class TestValidateSubmit(TestApprovalAdapterBase):
    """测试提交验证"""
    
    def test_validate_submit_returns_true_by_default(self):
        """测试默认返回True"""
        valid, error = self.adapter.validate_submit(123)
        
        self.assertTrue(valid)
        self.assertIsNone(error)
    
    def test_validate_submit_returns_tuple(self):
        """测试返回元组"""
        result = self.adapter.validate_submit(456)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
    
    def test_validate_submit_with_different_entity_ids(self):
        """测试不同实体ID验证结果一致（默认实现）"""
        valid1, error1 = self.adapter.validate_submit(100)
        valid2, error2 = self.adapter.validate_submit(200)
        
        self.assertEqual(valid1, valid2)
        self.assertEqual(error1, error2)


class TestGetCCUserIds(TestApprovalAdapterBase):
    """测试抄送人列表"""
    
    def test_get_cc_user_ids_returns_empty_list_by_default(self):
        """测试默认返回空列表"""
        cc_users = self.adapter.get_cc_user_ids(999)
        
        self.assertEqual(cc_users, [])
        self.assertIsInstance(cc_users, list)
    
    def test_get_cc_user_ids_with_different_entity_ids(self):
        """测试不同实体ID返回相同结果（默认实现）"""
        cc_users1 = self.adapter.get_cc_user_ids(100)
        cc_users2 = self.adapter.get_cc_user_ids(200)
        
        self.assertEqual(cc_users1, cc_users2)


class TestGetDepartmentManagerUserId(TestApprovalAdapterBase):
    """测试获取部门负责人用户ID"""
    
    @patch('app.models.user.User')
    @patch('app.models.organization.Employee')
    @patch('app.models.organization.Department')
    def test_get_department_manager_with_valid_department(self, mock_dept_cls, mock_employee_cls, mock_user_cls):
        """测试有效部门返回负责人ID"""
        # 构造真实数据对象
        dept = Mock()
        dept.dept_name = "Engineering"
        dept.manager_id = 10
        dept.is_active = True
        
        manager = Mock()
        manager.id = 10
        manager.name = "张三"
        manager.employee_code = "E001"
        
        user = Mock()
        user.id = 100
        user.real_name = "张三"
        user.is_active = True
        
        # Mock查询链
        self.db.query.return_value.filter.return_value.first.side_effect = [dept, manager, user]
        
        result = self.adapter.get_department_manager_user_id("Engineering")
        
        self.assertEqual(result, 100)
    
    @patch('app.models.organization.Department')
    def test_get_department_manager_department_not_found(self, mock_dept_cls):
        """测试部门不存在返回None"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter.get_department_manager_user_id("NonExistent")
        
        self.assertIsNone(result)
    
    @patch('app.models.organization.Department')
    def test_get_department_manager_no_manager_assigned(self, mock_dept_cls):
        """测试部门没有负责人返回None"""
        dept = Mock()
        dept.dept_name = "Engineering"
        dept.manager_id = None
        dept.is_active = True
        
        self.db.query.return_value.filter.return_value.first.return_value = dept
        
        result = self.adapter.get_department_manager_user_id("Engineering")
        
        self.assertIsNone(result)
    
    @patch('app.models.organization.Employee')
    @patch('app.models.organization.Department')
    def test_get_department_manager_employee_not_found(self, mock_dept_cls, mock_employee_cls):
        """测试员工记录不存在返回None"""
        dept = Mock()
        dept.dept_name = "Engineering"
        dept.manager_id = 10
        dept.is_active = True
        
        self.db.query.return_value.filter.return_value.first.side_effect = [dept, None]
        
        result = self.adapter.get_department_manager_user_id("Engineering")
        
        self.assertIsNone(result)
    
    @patch('app.models.user.User')
    @patch('app.models.organization.Employee')
    @patch('app.models.organization.Department')
    def test_get_department_manager_user_not_found(self, mock_dept_cls, mock_employee_cls, mock_user_cls):
        """测试用户记录不存在返回None"""
        dept = Mock()
        dept.dept_name = "Engineering"
        dept.manager_id = 10
        dept.is_active = True
        
        manager = Mock()
        manager.id = 10
        manager.name = "张三"
        manager.employee_code = "E001"
        
        self.db.query.return_value.filter.return_value.first.side_effect = [dept, manager, None]
        
        result = self.adapter.get_department_manager_user_id("Engineering")
        
        self.assertIsNone(result)


class TestGetDepartmentManagerUserIdsByCodes(TestApprovalAdapterBase):
    """测试批量获取部门负责人用户ID"""
    
    @patch('app.models.user.User')
    @patch('app.models.organization.Employee')
    @patch('app.models.organization.Department')
    def test_get_managers_with_valid_departments(self, mock_dept_cls, mock_employee_cls, mock_user_cls):
        """测试有效部门编码返回负责人ID列表"""
        # 构造部门数据
        dept1 = Mock()
        dept1.dept_code = "PROD"
        dept1.manager_id = 10
        dept1.is_active = True
        
        dept2 = Mock()
        dept2.dept_code = "QA"
        dept2.manager_id = 20
        dept2.is_active = True
        
        # 构造员工数据
        manager1 = Mock()
        manager1.id = 10
        manager1.name = "张三"
        manager1.employee_code = "E001"
        
        manager2 = Mock()
        manager2.id = 20
        manager2.name = "李四"
        manager2.employee_code = "E002"
        
        # 构造用户数据
        user1 = Mock()
        user1.id = 100
        user1.real_name = "张三"
        user1.is_active = True
        
        user2 = Mock()
        user2.id = 200
        user2.real_name = "李四"
        user2.is_active = True
        
        # Mock查询链 - 分别处理不同的查询
        query_mock = Mock()
        
        # 第一次查询：部门查询
        dept_filter_mock = Mock()
        dept_filter_mock.all.return_value = [dept1, dept2]
        query_mock.filter.return_value = dept_filter_mock
        
        # 第二次查询：员工查询
        emp_filter_mock = Mock()
        emp_filter_mock.all.return_value = [manager1, manager2]
        
        # 第三次查询：用户查询
        user_filter_mock = Mock()
        user_filter_mock.all.return_value = [user1, user2]
        
        # 设置query的返回值依次为这三个mock
        self.db.query.side_effect = [
            Mock(filter=lambda *args, **kwargs: dept_filter_mock),
            Mock(filter=lambda *args, **kwargs: emp_filter_mock),
            Mock(filter=lambda *args, **kwargs: user_filter_mock)
        ]
        
        result = self.adapter.get_department_manager_user_ids_by_codes(["PROD", "QA"])
        
        self.assertEqual(set(result), {100, 200})
        self.assertEqual(len(result), 2)
    
    @patch('app.models.organization.Department')
    def test_get_managers_with_empty_dept_codes(self, mock_dept_cls):
        """测试空部门编码列表返回空列表"""
        result = self.adapter.get_department_manager_user_ids_by_codes([])
        
        # 空列表会导致查询返回空结果
        self.assertEqual(result, [])
    
    @patch('app.models.organization.Department')
    def test_get_managers_no_departments_found(self, mock_dept_cls):
        """测试未找到部门返回空列表"""
        query_mock = Mock()
        filter_mock = Mock()
        filter_mock.all.return_value = []
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock
        
        result = self.adapter.get_department_manager_user_ids_by_codes(["INVALID"])
        
        self.assertEqual(result, [])
    
    @patch('app.models.organization.Employee')
    @patch('app.models.organization.Department')
    def test_get_managers_departments_without_managers(self, mock_dept_cls, mock_employee_cls):
        """测试部门没有负责人返回空列表"""
        dept = Mock()
        dept.dept_code = "PROD"
        dept.manager_id = None
        dept.is_active = True
        
        query_mock = Mock()
        filter_mock = Mock()
        filter_mock.all.return_value = [dept]
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock
        
        result = self.adapter.get_department_manager_user_ids_by_codes(["PROD"])
        
        self.assertEqual(result, [])
    
    @patch('app.models.user.User')
    @patch('app.models.organization.Employee')
    @patch('app.models.organization.Department')
    def test_get_managers_deduplication(self, mock_dept_cls, mock_employee_cls, mock_user_cls):
        """测试结果去重（同一负责人管理多个部门）"""
        # 两个部门同一个负责人
        dept1 = Mock()
        dept1.dept_code = "PROD"
        dept1.manager_id = 10
        dept1.is_active = True
        
        dept2 = Mock()
        dept2.dept_code = "QA"
        dept2.manager_id = 10
        dept2.is_active = True
        
        manager = Mock()
        manager.id = 10
        manager.name = "张三"
        manager.employee_code = "E001"
        
        user = Mock()
        user.id = 100
        user.real_name = "张三"
        user.is_active = True
        
        # Mock查询链
        self.db.query.side_effect = [
            Mock(filter=lambda *args, **kwargs: Mock(all=lambda: [dept1, dept2])),
            Mock(filter=lambda *args, **kwargs: Mock(all=lambda: [manager])),
            Mock(filter=lambda *args, **kwargs: Mock(all=lambda: [user]))
        ]
        
        result = self.adapter.get_department_manager_user_ids_by_codes(["PROD", "QA"])
        
        # 应该去重，只返回一个ID
        self.assertEqual(len(result), 1)
        self.assertIn(100, result)


class TestGetProjectSalesUserId(TestApprovalAdapterBase):
    """测试获取项目销售负责人用户ID"""
    
    @patch('app.models.project.Project')
    def test_get_sales_from_project_sales_id(self, mock_project_cls):
        """测试从项目的sales_id字段获取"""
        project = Mock()
        project.id = 1001
        project.sales_id = 500
        
        self.db.query.return_value.filter.return_value.first.return_value = project
        
        result = self.adapter.get_project_sales_user_id(1001)
        
        self.assertEqual(result, 500)
    
    @patch('app.models.project.Project')
    def test_get_sales_project_not_found(self, mock_project_cls):
        """测试项目不存在返回None"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter.get_project_sales_user_id(9999)
        
        self.assertIsNone(result)
    
    @patch('app.models.sales.contracts.Contract')
    @patch('app.models.project.Project')
    def test_get_sales_from_contract(self, mock_project_cls, mock_contract_cls):
        """测试从关联的销售合同获取"""
        project = Mock()
        project.id = 1001
        project.sales_id = None
        project.contract_id = 2001
        
        contract = Mock()
        contract.id = 2001
        contract.sales_id = 600
        
        self.db.query.return_value.filter.return_value.first.side_effect = [project, contract]
        
        result = self.adapter.get_project_sales_user_id(1001)
        
        self.assertEqual(result, 600)
    
    @patch('app.models.project.Project')
    def test_get_sales_no_sales_id_no_contract(self, mock_project_cls):
        """测试项目既没有sales_id也没有contract_id返回None"""
        project = Mock()
        project.id = 1001
        project.sales_id = None
        project.contract_id = None
        
        self.db.query.return_value.filter.return_value.first.return_value = project
        
        result = self.adapter.get_project_sales_user_id(1001)
        
        self.assertIsNone(result)
    
    @patch('app.models.sales.contracts.Contract')
    @patch('app.models.project.Project')
    def test_get_sales_contract_not_found(self, mock_project_cls, mock_contract_cls):
        """测试合同不存在返回None"""
        project = Mock()
        project.id = 1001
        project.sales_id = None
        project.contract_id = 2001
        
        self.db.query.return_value.filter.return_value.first.side_effect = [project, None]
        
        result = self.adapter.get_project_sales_user_id(1001)
        
        self.assertIsNone(result)
    
    @patch('app.models.sales.contracts.Contract')
    @patch('app.models.project.Project')
    def test_get_sales_contract_has_no_sales_id(self, mock_project_cls, mock_contract_cls):
        """测试合同存在但没有sales_id返回None"""
        project = Mock()
        project.id = 1001
        project.sales_id = None
        project.contract_id = 2001
        
        contract = Mock()
        contract.id = 2001
        contract.sales_id = None
        
        self.db.query.return_value.filter.return_value.first.side_effect = [project, contract]
        
        result = self.adapter.get_project_sales_user_id(1001)
        
        self.assertIsNone(result)


# ==================== 测试套件 ====================

def suite():
    """创建测试套件"""
    test_suite = unittest.TestSuite()
    
    test_suite.addTest(unittest.makeSuite(TestInitialization))
    test_suite.addTest(unittest.makeSuite(TestAbstractMethodImplementation))
    test_suite.addTest(unittest.makeSuite(TestOptionalCallbacks))
    test_suite.addTest(unittest.makeSuite(TestResolveApprovers))
    test_suite.addTest(unittest.makeSuite(TestGenerateTitle))
    test_suite.addTest(unittest.makeSuite(TestGenerateSummary))
    test_suite.addTest(unittest.makeSuite(TestGetFormData))
    test_suite.addTest(unittest.makeSuite(TestValidateSubmit))
    test_suite.addTest(unittest.makeSuite(TestGetCCUserIds))
    test_suite.addTest(unittest.makeSuite(TestGetDepartmentManagerUserId))
    test_suite.addTest(unittest.makeSuite(TestGetDepartmentManagerUserIdsByCodes))
    test_suite.addTest(unittest.makeSuite(TestGetProjectSalesUserId))
    
    return test_suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
