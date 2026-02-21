# -*- coding: utf-8 -*-
"""
客户服务单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行（不要mock业务方法）
3. 覆盖主要方法和边界情况
4. 所有测试必须通过
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, PropertyMock
from decimal import Decimal

from fastapi import HTTPException

from app.services.customer_service import CustomerService
from app.models.project.customer import Customer
from app.schemas.project.customer import CustomerCreate, CustomerUpdate


class TestCustomerService(unittest.TestCase):
    """测试CustomerService核心方法"""

    def setUp(self):
        """每个测试前的初始化"""
        self.mock_db = MagicMock()
        self.service = CustomerService(db=self.mock_db)

    # ========== list_customers() 测试 ==========

    def test_list_customers_basic(self):
        """测试基本的客户列表查询"""
        # 模拟查询结果 - 添加必需的默认值
        mock_customers = [
            Customer(
                id=1,
                customer_code="C001",
                customer_name="测试客户1",
                short_name="客户1",
                customer_type="企业",
                industry="IT",
                status="ACTIVE",
                credit_level="B",
            ),
            Customer(
                id=2,
                customer_code="C002",
                customer_name="测试客户2",
                short_name="客户2",
                customer_type="个人",
                industry="制造",
                status="ACTIVE",
                credit_level="B",
            ),
        ]

        # Mock repository.list 方法
        with patch.object(self.service.repository, 'list') as mock_list:
            mock_list.return_value = (mock_customers, 2)
            
            result = self.service.list_customers(page=1, page_size=20)
            
            # 验证返回结果
            self.assertEqual(len(result['items']), 2)
            self.assertEqual(result['total'], 2)
            self.assertEqual(result['page'], 1)
            self.assertEqual(result['page_size'], 20)
            self.assertEqual(result['pages'], 1)

    def test_list_customers_with_keyword(self):
        """测试带关键词搜索的客户列表"""
        mock_customers = [
            Customer(
                id=1,
                customer_code="C001",
                customer_name="阿里巴巴",
                short_name="阿里",
                status="ACTIVE",
                credit_level="B",
            )
        ]

        with patch.object(self.service.repository, 'list') as mock_list:
            mock_list.return_value = (mock_customers, 1)
            
            result = self.service.list_customers(
                page=1,
                page_size=20,
                keyword="阿里"
            )
            
            self.assertEqual(len(result['items']), 1)
            self.assertEqual(result['total'], 1)

    def test_list_customers_with_filters(self):
        """测试带过滤条件的客户列表"""
        mock_customers = [
            Customer(
                id=1,
                customer_code="C001",
                customer_name="IT公司",
                customer_type="企业",
                industry="IT",
                status="ACTIVE",
                credit_level="B",
            )
        ]

        with patch.object(self.service.repository, 'list') as mock_list:
            mock_list.return_value = (mock_customers, 1)
            
            result = self.service.list_customers(
                page=1,
                page_size=20,
                customer_type="企业",
                industry="IT",
                status="ACTIVE"
            )
            
            self.assertEqual(len(result['items']), 1)
            # 验证list方法被调用时传入了正确的filters
            call_kwargs = mock_list.call_args[1]
            self.assertIn('filters', call_kwargs)
            filters = call_kwargs['filters']
            self.assertEqual(filters.get('customer_type'), "企业")
            self.assertEqual(filters.get('industry'), "IT")
            self.assertEqual(filters.get('status'), "ACTIVE")

    def test_list_customers_empty_result(self):
        """测试空结果的客户列表"""
        with patch.object(self.service.repository, 'list') as mock_list:
            mock_list.return_value = ([], 0)
            
            result = self.service.list_customers(page=1, page_size=20)
            
            self.assertEqual(len(result['items']), 0)
            self.assertEqual(result['total'], 0)
            self.assertEqual(result['pages'], 0)

    def test_list_customers_pagination(self):
        """测试分页计算"""
        mock_customers = [Customer(
            id=i, 
            customer_code=f"C{i:03d}", 
            customer_name=f"客户{i}",
            credit_level="B",
            status="ACTIVE"
        ) for i in range(1, 21)]

        with patch.object(self.service.repository, 'list') as mock_list:
            # 总共50条记录，每页20条
            mock_list.return_value = (mock_customers[:20], 50)
            
            result = self.service.list_customers(page=1, page_size=20)
            
            self.assertEqual(result['total'], 50)
            self.assertEqual(result['page'], 1)
            self.assertEqual(result['page_size'], 20)
            self.assertEqual(result['pages'], 3)  # 50/20 向上取整 = 3

    def test_list_customers_with_all_filters(self):
        """测试同时使用所有过滤条件"""
        mock_customers = [
            Customer(
                id=1,
                customer_code="C001",
                customer_name="完整测试客户",
                customer_type="企业",
                industry="IT",
                status="ACTIVE",
                credit_level="B",
            )
        ]

        with patch.object(self.service.repository, 'list') as mock_list:
            mock_list.return_value = (mock_customers, 1)
            
            result = self.service.list_customers(
                page=2,
                page_size=10,
                keyword="测试",
                customer_type="企业",
                industry="IT",
                status="ACTIVE"
            )
            
            self.assertEqual(len(result['items']), 1)
            self.assertEqual(result['page'], 2)
            self.assertEqual(result['page_size'], 10)

    def test_list_customers_partial_filters(self):
        """测试部分过滤条件为None"""
        with patch.object(self.service.repository, 'list') as mock_list:
            mock_list.return_value = ([], 0)
            
            result = self.service.list_customers(
                customer_type="企业",
                industry=None,  # None应该被忽略
                status=None
            )
            
            call_kwargs = mock_list.call_args[1]
            filters = call_kwargs.get('filters', {})
            # None值不应该被加入filters
            self.assertIn('customer_type', filters)
            self.assertNotIn('industry', filters)
            self.assertNotIn('status', filters)

    # ========== _before_delete() 测试 ==========

    def test_before_delete_with_no_projects(self):
        """测试删除无关联项目的客户"""
        # Mock query返回0个项目
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 0
        self.mock_db.query.return_value = mock_query
        
        # 不应抛出异常
        try:
            self.service._before_delete(object_id=1)
        except HTTPException:
            self.fail("_before_delete raised HTTPException unexpectedly")

    def test_before_delete_with_projects(self):
        """测试删除有关联项目的客户（应该抛出异常）"""
        # Mock query返回3个项目
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 3
        self.mock_db.query.return_value = mock_query
        
        # 应该抛出HTTPException
        with self.assertRaises(HTTPException) as context:
            self.service._before_delete(object_id=1)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("3 个项目", context.exception.detail)
        self.assertIn("无法删除", context.exception.detail)

    def test_before_delete_with_one_project(self):
        """测试删除有1个关联项目的客户"""
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 1
        self.mock_db.query.return_value = mock_query
        
        with self.assertRaises(HTTPException) as context:
            self.service._before_delete(object_id=5)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("1 个项目", context.exception.detail)

    # ========== _after_update() 测试 ==========

    def test_after_update_with_auto_sync_enabled(self):
        """测试更新后自动同步（默认启用）"""
        mock_customer = Customer(
            id=1,
            customer_code="C001",
            customer_name="测试客户",
            credit_level="B",
            status="ACTIVE"
        )
        
        # 在_after_update内部导入，需要mock app.services.data_sync_service.DataSyncService
        with patch('app.services.data_sync_service.DataSyncService') as MockDataSyncService:
            mock_sync_instance = MagicMock()
            MockDataSyncService.return_value = mock_sync_instance
            
            result = self.service._after_update(mock_customer)
            
            # 验证DataSyncService被调用
            MockDataSyncService.assert_called_once_with(self.mock_db)
            mock_sync_instance.sync_customer_to_projects.assert_called_once_with(1)
            mock_sync_instance.sync_customer_to_contracts.assert_called_once_with(1)
            
            # 验证返回的是原对象
            self.assertEqual(result, mock_customer)

    def test_after_update_with_auto_sync_disabled(self):
        """测试禁用自动同步"""
        mock_customer = Customer(
            id=2,
            customer_code="C002",
            customer_name="测试客户2",
            credit_level="B",
            status="ACTIVE"
        )
        
        # 禁用自动同步
        self.service.set_auto_sync(False)
        
        with patch('app.services.data_sync_service.DataSyncService') as MockDataSyncService:
            result = self.service._after_update(mock_customer)
            
            # 验证DataSyncService未被调用
            MockDataSyncService.assert_not_called()
            self.assertEqual(result, mock_customer)

    def test_after_update_sync_exception_handling(self):
        """测试同步异常处理（不应影响更新操作）"""
        mock_customer = Customer(
            id=3,
            customer_code="C003",
            customer_name="测试客户3",
            credit_level="B",
            status="ACTIVE"
        )
        
        # Mock DataSyncService抛出异常
        with patch('app.services.data_sync_service.DataSyncService') as MockDataSyncService:
            mock_sync_instance = MagicMock()
            mock_sync_instance.sync_customer_to_projects.side_effect = Exception("同步失败")
            MockDataSyncService.return_value = mock_sync_instance
            
            # 不应抛出异常，应该捕获并记录日志
            result = self.service._after_update(mock_customer)
            
            # 验证返回的是原对象
            self.assertEqual(result, mock_customer)

    def test_after_update_re_enable_auto_sync(self):
        """测试重新启用自动同步"""
        mock_customer = Customer(
            id=4,
            customer_code="C004",
            customer_name="测试客户4",
            credit_level="B",
            status="ACTIVE"
        )
        
        # 先禁用再启用
        self.service.set_auto_sync(False)
        self.service.set_auto_sync(True)
        
        with patch('app.services.data_sync_service.DataSyncService') as MockDataSyncService:
            mock_sync_instance = MagicMock()
            MockDataSyncService.return_value = mock_sync_instance
            
            self.service._after_update(mock_customer)
            
            # 验证同步被调用
            mock_sync_instance.sync_customer_to_projects.assert_called_once_with(4)

    # ========== set_auto_sync() 测试 ==========

    def test_set_auto_sync_true(self):
        """测试设置自动同步为True"""
        self.service.set_auto_sync(True)
        self.assertTrue(self.service._auto_sync)

    def test_set_auto_sync_false(self):
        """测试设置自动同步为False"""
        self.service.set_auto_sync(False)
        self.assertFalse(self.service._auto_sync)

    # ========== generate_code() 测试 ==========

    def test_generate_code(self):
        """测试生成客户编码"""
        # 在generate_code内部导入，需要mock app.utils.number_generator.generate_customer_code
        with patch('app.utils.number_generator.generate_customer_code') as mock_generate:
            mock_generate.return_value = "C20260221001"
            
            result = self.service.generate_code()
            
            # 验证生成函数被调用
            mock_generate.assert_called_once_with(self.mock_db)
            self.assertEqual(result, "C20260221001")

    def test_generate_code_multiple_calls(self):
        """测试多次调用生成不同编码"""
        with patch('app.utils.number_generator.generate_customer_code') as mock_generate:
            mock_generate.side_effect = ["C20260221001", "C20260221002", "C20260221003"]
            
            code1 = self.service.generate_code()
            code2 = self.service.generate_code()
            code3 = self.service.generate_code()
            
            self.assertEqual(code1, "C20260221001")
            self.assertEqual(code2, "C20260221002")
            self.assertEqual(code3, "C20260221003")
            self.assertEqual(mock_generate.call_count, 3)

    # ========== 继承方法测试（通过BaseService）==========

    def test_service_initialization(self):
        """测试服务初始化"""
        self.assertEqual(self.service.model, Customer)
        self.assertEqual(self.service.db, self.mock_db)
        self.assertEqual(self.service.resource_name, "客户")
        self.assertIsNotNone(self.service.repository)

    def test_service_has_crud_methods(self):
        """测试服务拥有CRUD方法"""
        # 验证继承自BaseService的方法存在
        self.assertTrue(hasattr(self.service, 'get'))
        self.assertTrue(hasattr(self.service, 'list'))
        self.assertTrue(hasattr(self.service, 'create'))
        self.assertTrue(hasattr(self.service, 'update'))
        self.assertTrue(hasattr(self.service, 'delete'))
        self.assertTrue(hasattr(self.service, 'count'))

    # ========== 边界情况和异常测试 ==========

    def test_before_delete_with_many_projects(self):
        """测试删除有大量关联项目的客户"""
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 999
        self.mock_db.query.return_value = mock_query
        
        with self.assertRaises(HTTPException) as context:
            self.service._before_delete(object_id=1)
        
        self.assertIn("999 个项目", context.exception.detail)


class TestCustomerServiceIntegration(unittest.TestCase):
    """测试CustomerService与其他组件的集成"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = CustomerService(db=self.mock_db)

    def test_delete_workflow_with_projects(self):
        """测试完整的删除工作流（有项目关联）"""
        # Mock有项目关联
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 2
        self.mock_db.query.return_value = mock_query
        
        # 调用delete应该在_before_delete中抛出异常
        with patch.object(self.service.repository, 'get') as mock_get:
            mock_customer = Customer(
                id=1, 
                customer_code="C001", 
                customer_name="测试",
                credit_level="B",
                status="ACTIVE"
            )
            mock_get.return_value = mock_customer
            
            with self.assertRaises(HTTPException):
                self.service.delete(object_id=1)

    def test_update_workflow_with_sync(self):
        """测试完整的更新工作流（包含同步）"""
        mock_customer = Customer(
            id=1,
            customer_code="C001",
            customer_name="原名称",
            credit_level="B",
            status="ACTIVE"
        )
        
        update_data = CustomerUpdate(customer_name="新名称")
        
        # Mock repository方法
        with patch.object(self.service.repository, 'get') as mock_get, \
             patch.object(self.service.repository, 'update') as mock_update, \
             patch('app.services.data_sync_service.DataSyncService') as MockDataSyncService:
            
            mock_get.return_value = mock_customer
            mock_customer.customer_name = "新名称"
            mock_update.return_value = mock_customer
            
            mock_sync_instance = MagicMock()
            MockDataSyncService.return_value = mock_sync_instance
            
            result = self.service.update(object_id=1, obj_in=update_data)
            
            # 验证同步被触发
            mock_sync_instance.sync_customer_to_projects.assert_called_once()
            mock_sync_instance.sync_customer_to_contracts.assert_called_once()


if __name__ == "__main__":
    unittest.main()
