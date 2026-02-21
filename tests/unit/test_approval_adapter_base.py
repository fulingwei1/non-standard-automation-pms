# -*- coding: utf-8 -*-
"""
审批适配器基类单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch
from typing import Any, Dict, List, Optional

from app.services.approval_engine.adapters.base import ApprovalAdapter


# ==================== 测试用具体实现类 ====================

class ConcreteAdapter(ApprovalAdapter):
    """
    具体实现类，用于测试抽象基类的功能
    """
    entity_type = "test_entity"

    def __init__(self, db):
        super().__init__(db)
        # 用于记录回调调用
        self.callbacks = {
            "get_entity": [],
            "get_entity_data": [],
            "on_submit": [],
            "on_approved": [],
            "on_rejected": [],
        }

    def get_entity(self, entity_id: int) -> Any:
        """实现抽象方法"""
        self.callbacks["get_entity"].append(entity_id)
        # 模拟返回一个实体对象
        entity = MagicMock()
        entity.id = entity_id
        entity.name = f"Entity-{entity_id}"
        return entity

    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """实现抽象方法"""
        self.callbacks["get_entity_data"].append(entity_id)
        return {
            "id": entity_id,
            "amount": 5000,
            "days": 3,
            "status": "PENDING",
        }

    def on_submit(self, entity_id: int, instance):
        """实现抽象方法"""
        self.callbacks["on_submit"].append((entity_id, instance))

    def on_approved(self, entity_id: int, instance):
        """实现抽象方法"""
        self.callbacks["on_approved"].append((entity_id, instance))

    def on_rejected(self, entity_id: int, instance):
        """实现抽象方法"""
        self.callbacks["on_rejected"].append((entity_id, instance))


# ==================== 单元测试类 ====================

class TestApprovalAdapterBase(unittest.TestCase):
    """测试审批适配器基类"""

    def setUp(self):
        """初始化测试环境"""
        self.mock_db = MagicMock()
        self.adapter = ConcreteAdapter(self.mock_db)

    # ========== 基础功能测试 ==========

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.adapter.db, self.mock_db)
        self.assertEqual(self.adapter.entity_type, "test_entity")

    def test_get_entity(self):
        """测试获取实体"""
        entity = self.adapter.get_entity(123)
        self.assertEqual(entity.id, 123)
        self.assertEqual(entity.name, "Entity-123")
        self.assertEqual(self.adapter.callbacks["get_entity"], [123])

    def test_get_entity_data(self):
        """测试获取实体数据"""
        data = self.adapter.get_entity_data(456)
        self.assertEqual(data["id"], 456)
        self.assertEqual(data["amount"], 5000)
        self.assertEqual(self.adapter.callbacks["get_entity_data"], [456])

    # ========== 回调方法测试 ==========

    def test_on_submit(self):
        """测试提交回调"""
        mock_instance = MagicMock()
        mock_instance.id = 1
        self.adapter.on_submit(123, mock_instance)
        self.assertEqual(len(self.adapter.callbacks["on_submit"]), 1)
        self.assertEqual(self.adapter.callbacks["on_submit"][0][0], 123)

    def test_on_approved(self):
        """测试通过回调"""
        mock_instance = MagicMock()
        self.adapter.on_approved(123, mock_instance)
        self.assertEqual(len(self.adapter.callbacks["on_approved"]), 1)

    def test_on_rejected(self):
        """测试驳回回调"""
        mock_instance = MagicMock()
        self.adapter.on_rejected(123, mock_instance)
        self.assertEqual(len(self.adapter.callbacks["on_rejected"]), 1)

    def test_on_withdrawn(self):
        """测试撤回回调（默认实现为空）"""
        mock_instance = MagicMock()
        # 应该不抛出异常
        result = self.adapter.on_withdrawn(123, mock_instance)
        self.assertIsNone(result)

    def test_on_terminated(self):
        """测试终止回调（默认实现为空）"""
        mock_instance = MagicMock()
        # 应该不抛出异常
        result = self.adapter.on_terminated(123, mock_instance)
        self.assertIsNone(result)

    # ========== 审批人解析测试 ==========

    def test_resolve_approvers_default(self):
        """测试默认审批人解析（返回空列表）"""
        mock_node = MagicMock()
        context = {"user_id": 1}
        result = self.adapter.resolve_approvers(mock_node, context)
        self.assertEqual(result, [])

    # ========== 标题和摘要测试 ==========

    def test_generate_title_default(self):
        """测试生成默认标题"""
        title = self.adapter.generate_title(123)
        self.assertEqual(title, "test_entity审批 - 123")

    def test_generate_summary_default(self):
        """测试生成默认摘要（空字符串）"""
        summary = self.adapter.generate_summary(123)
        self.assertEqual(summary, "")

    # ========== 表单数据测试 ==========

    def test_get_form_data_default(self):
        """测试获取表单数据（默认返回entity_data）"""
        data = self.adapter.get_form_data(123)
        self.assertEqual(data["id"], 123)
        self.assertEqual(data["amount"], 5000)

    # ========== 验证测试 ==========

    def test_validate_submit_default(self):
        """测试验证提交（默认通过）"""
        is_valid, error = self.adapter.validate_submit(123)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    # ========== 抄送人测试 ==========

    def test_get_cc_user_ids_default(self):
        """测试获取抄送人（默认空列表）"""
        cc_users = self.adapter.get_cc_user_ids(123)
        self.assertEqual(cc_users, [])

    # ========== 部门负责人查询测试 ==========

    def test_get_department_manager_user_id_success(self):
        """测试根据部门名称获取负责人用户ID - 成功"""
        # Mock部门
        mock_dept = MagicMock()
        mock_dept.dept_name = "研发部"
        mock_dept.manager_id = 100
        mock_dept.is_active = True

        # Mock员工（部门经理）
        mock_manager = MagicMock()
        mock_manager.id = 100
        mock_manager.name = "张三"
        mock_manager.employee_code = "EMP001"

        # Mock用户
        mock_user = MagicMock()
        mock_user.id = 50
        mock_user.real_name = "张三"
        mock_user.is_active = True

        # 配置mock query链
        mock_dept_query = MagicMock()
        mock_employee_query = MagicMock()
        mock_user_query = MagicMock()

        # 部门查询
        mock_dept_query.filter.return_value.first.return_value = mock_dept
        # 员工查询
        mock_employee_query.filter.return_value.first.return_value = mock_manager
        # 用户查询
        mock_user_query.filter.return_value.first.return_value = mock_user

        # 配置db.query根据参数返回不同的mock
        def query_side_effect(model):
            if 'Department' in str(model):
                return mock_dept_query
            elif 'Employee' in str(model):
                return mock_employee_query
            elif 'User' in str(model):
                return mock_user_query
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        # 执行测试
        result = self.adapter.get_department_manager_user_id("研发部")
        
        # 验证结果
        self.assertEqual(result, 50)

    def test_get_department_manager_user_id_dept_not_found(self):
        """测试根据部门名称获取负责人 - 部门不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        result = self.adapter.get_department_manager_user_id("不存在的部门")
        self.assertIsNone(result)

    def test_get_department_manager_user_id_no_manager(self):
        """测试根据部门名称获取负责人 - 部门无负责人"""
        mock_dept = MagicMock()
        mock_dept.manager_id = None
        mock_dept.is_active = True

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_dept
        self.mock_db.query.return_value = mock_query

        result = self.adapter.get_department_manager_user_id("研发部")
        self.assertIsNone(result)

    def test_get_department_manager_user_id_manager_not_found(self):
        """测试根据部门名称获取负责人 - 找不到员工信息"""
        mock_dept = MagicMock()
        mock_dept.manager_id = 100
        mock_dept.is_active = True

        mock_dept_query = MagicMock()
        mock_employee_query = MagicMock()

        mock_dept_query.filter.return_value.first.return_value = mock_dept
        mock_employee_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if 'Department' in str(model):
                return mock_dept_query
            elif 'Employee' in str(model):
                return mock_employee_query
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_department_manager_user_id("研发部")
        self.assertIsNone(result)

    def test_get_department_manager_user_id_user_not_found(self):
        """测试根据部门名称获取负责人 - 找不到用户"""
        mock_dept = MagicMock()
        mock_dept.manager_id = 100
        mock_dept.is_active = True

        mock_manager = MagicMock()
        mock_manager.id = 100
        mock_manager.name = "张三"
        mock_manager.employee_code = "EMP001"

        mock_dept_query = MagicMock()
        mock_employee_query = MagicMock()
        mock_user_query = MagicMock()

        mock_dept_query.filter.return_value.first.return_value = mock_dept
        mock_employee_query.filter.return_value.first.return_value = mock_manager
        mock_user_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if 'Department' in str(model):
                return mock_dept_query
            elif 'Employee' in str(model):
                return mock_employee_query
            elif 'User' in str(model):
                return mock_user_query
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_department_manager_user_id("研发部")
        self.assertIsNone(result)

    # ========== 批量部门负责人查询测试 ==========

    def test_get_department_manager_user_ids_by_codes_success(self):
        """测试批量获取部门负责人 - 成功"""
        # Mock两个部门
        mock_dept1 = MagicMock()
        mock_dept1.dept_code = "PROD"
        mock_dept1.manager_id = 100
        mock_dept1.is_active = True

        mock_dept2 = MagicMock()
        mock_dept2.dept_code = "QA"
        mock_dept2.manager_id = 101
        mock_dept2.is_active = True

        # Mock两个员工
        mock_manager1 = MagicMock()
        mock_manager1.id = 100
        mock_manager1.name = "张三"
        mock_manager1.employee_code = "EMP001"

        mock_manager2 = MagicMock()
        mock_manager2.id = 101
        mock_manager2.name = "李四"
        mock_manager2.employee_code = "EMP002"

        # Mock两个用户
        mock_user1 = MagicMock()
        mock_user1.id = 50
        mock_user1.real_name = "张三"
        mock_user1.is_active = True

        mock_user2 = MagicMock()
        mock_user2.id = 51
        mock_user2.real_name = "李四"
        mock_user2.is_active = True

        # 配置mock query链
        mock_dept_query = MagicMock()
        mock_employee_query = MagicMock()
        mock_user_query = MagicMock()

        mock_dept_query.filter.return_value.all.return_value = [mock_dept1, mock_dept2]
        mock_employee_query.filter.return_value.all.return_value = [mock_manager1, mock_manager2]
        mock_user_query.filter.return_value.all.return_value = [mock_user1, mock_user2]

        def query_side_effect(model):
            if 'Department' in str(model):
                return mock_dept_query
            elif 'Employee' in str(model):
                return mock_employee_query
            elif 'User' in str(model):
                return mock_user_query
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        # 执行测试
        result = self.adapter.get_department_manager_user_ids_by_codes(["PROD", "QA"])
        
        # 验证结果（应该去重）
        self.assertEqual(set(result), {50, 51})

    def test_get_department_manager_user_ids_by_codes_no_depts(self):
        """测试批量获取部门负责人 - 部门不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        result = self.adapter.get_department_manager_user_ids_by_codes(["INVALID"])
        self.assertEqual(result, [])

    def test_get_department_manager_user_ids_by_codes_no_managers(self):
        """测试批量获取部门负责人 - 部门无负责人"""
        mock_dept = MagicMock()
        mock_dept.dept_code = "PROD"
        mock_dept.manager_id = None
        mock_dept.is_active = True

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_dept]
        self.mock_db.query.return_value = mock_query

        result = self.adapter.get_department_manager_user_ids_by_codes(["PROD"])
        self.assertEqual(result, [])

    def test_get_department_manager_user_ids_by_codes_deduplication(self):
        """测试批量获取部门负责人 - 去重"""
        # 两个部门有同一个负责人
        mock_dept1 = MagicMock()
        mock_dept1.dept_code = "PROD"
        mock_dept1.manager_id = 100
        mock_dept1.is_active = True

        mock_dept2 = MagicMock()
        mock_dept2.dept_code = "QA"
        mock_dept2.manager_id = 100  # 同一个负责人
        mock_dept2.is_active = True

        mock_manager = MagicMock()
        mock_manager.id = 100
        mock_manager.name = "张三"
        mock_manager.employee_code = "EMP001"

        mock_user = MagicMock()
        mock_user.id = 50
        mock_user.real_name = "张三"
        mock_user.is_active = True

        mock_dept_query = MagicMock()
        mock_employee_query = MagicMock()
        mock_user_query = MagicMock()

        mock_dept_query.filter.return_value.all.return_value = [mock_dept1, mock_dept2]
        mock_employee_query.filter.return_value.all.return_value = [mock_manager]
        mock_user_query.filter.return_value.all.return_value = [mock_user]

        def query_side_effect(model):
            if 'Department' in str(model):
                return mock_dept_query
            elif 'Employee' in str(model):
                return mock_employee_query
            elif 'User' in str(model):
                return mock_user_query
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_department_manager_user_ids_by_codes(["PROD", "QA"])
        
        # 应该只有一个用户ID
        self.assertEqual(result, [50])

    # ========== 项目销售负责人查询测试 ==========

    def test_get_project_sales_user_id_from_project(self):
        """测试获取项目销售负责人 - 从项目直接获取"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.sales_id = 100

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        self.mock_db.query.return_value = mock_query

        result = self.adapter.get_project_sales_user_id(1)
        self.assertEqual(result, 100)

    def test_get_project_sales_user_id_from_contract(self):
        """测试获取项目销售负责人 - 从合同获取"""
        # 项目没有sales_id，但有contract_id
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.sales_id = None
        mock_project.contract_id = 200

        # 合同有sales_id
        mock_contract = MagicMock()
        mock_contract.id = 200
        mock_contract.sales_id = 101

        mock_project_query = MagicMock()
        mock_contract_query = MagicMock()

        mock_project_query.filter.return_value.first.return_value = mock_project
        mock_contract_query.filter.return_value.first.return_value = mock_contract

        def query_side_effect(model):
            if 'Project' in str(model):
                return mock_project_query
            elif 'Contract' in str(model):
                return mock_contract_query
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_project_sales_user_id(1)
        self.assertEqual(result, 101)

    def test_get_project_sales_user_id_project_not_found(self):
        """测试获取项目销售负责人 - 项目不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        result = self.adapter.get_project_sales_user_id(999)
        self.assertIsNone(result)

    def test_get_project_sales_user_id_both_none(self):
        """测试获取项目销售负责人 - sales_id和contract_id都为None"""
        # 项目有属性但值都为None
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.sales_id = None
        mock_project.contract_id = None

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        self.mock_db.query.return_value = mock_query

        result = self.adapter.get_project_sales_user_id(1)
        self.assertIsNone(result)

    def test_get_project_sales_user_id_contract_not_found(self):
        """测试获取项目销售负责人 - 合同不存在"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.sales_id = None
        mock_project.contract_id = 999

        mock_project_query = MagicMock()
        mock_contract_query = MagicMock()

        mock_project_query.filter.return_value.first.return_value = mock_project
        mock_contract_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if 'Project' in str(model):
                return mock_project_query
            elif 'Contract' in str(model):
                return mock_contract_query
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_project_sales_user_id(1)
        self.assertIsNone(result)

    def test_get_project_sales_user_id_contract_no_sales(self):
        """测试获取项目销售负责人 - 合同无sales_id"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.sales_id = None
        mock_project.contract_id = 200

        mock_contract = MagicMock()
        mock_contract.id = 200
        mock_contract.sales_id = None

        mock_project_query = MagicMock()
        mock_contract_query = MagicMock()

        mock_project_query.filter.return_value.first.return_value = mock_project
        mock_contract_query.filter.return_value.first.return_value = mock_contract

        def query_side_effect(model):
            if 'Project' in str(model):
                return mock_project_query
            elif 'Contract' in str(model):
                return mock_contract_query
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_project_sales_user_id(1)
        self.assertIsNone(result)


# ==================== 抽象类测试 ====================

class TestAbstractMethods(unittest.TestCase):
    """测试抽象方法必须实现"""

    def test_cannot_instantiate_abstract_class(self):
        """测试不能直接实例化抽象类"""
        mock_db = MagicMock()
        
        # 尝试实例化抽象类应该抛出TypeError
        with self.assertRaises(TypeError) as context:
            adapter = ApprovalAdapter(mock_db)
        
        # 验证错误消息提到抽象方法
        self.assertIn("abstract", str(context.exception).lower())


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.adapter = ConcreteAdapter(self.mock_db)

    def test_empty_dept_codes_list(self):
        """测试空部门编码列表"""
        result = self.adapter.get_department_manager_user_ids_by_codes([])
        # 方法内部会执行查询，返回空列表
        self.assertEqual(result, [])

    def test_project_id_zero(self):
        """测试项目ID为0"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        result = self.adapter.get_project_sales_user_id(0)
        self.assertIsNone(result)

    def test_entity_type_empty(self):
        """测试entity_type为空时的标题生成"""
        self.adapter.entity_type = ""
        title = self.adapter.generate_title(123)
        self.assertEqual(title, "审批 - 123")

    def test_multiple_callbacks(self):
        """测试多次调用回调方法"""
        mock_instance = MagicMock()
        
        self.adapter.on_submit(1, mock_instance)
        self.adapter.on_submit(2, mock_instance)
        self.adapter.on_submit(3, mock_instance)
        
        self.assertEqual(len(self.adapter.callbacks["on_submit"]), 3)
        self.assertEqual(self.adapter.callbacks["on_submit"][0][0], 1)
        self.assertEqual(self.adapter.callbacks["on_submit"][1][0], 2)
        self.assertEqual(self.adapter.callbacks["on_submit"][2][0], 3)


if __name__ == "__main__":
    unittest.main()
