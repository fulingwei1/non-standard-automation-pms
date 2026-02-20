# -*- coding: utf-8 -*-
"""
项目CRUD服务层单元测试

测试覆盖：
1. 项目查询构建
2. 排序逻辑
3. 分页查询
4. 冗余字段填充
5. 项目编码唯一性检查
6. 项目创建
7. 项目更新
8. 软删除
9. 缓存失效
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

from app.services.project_crud import ProjectCrudService
from app.models.project import Project, Customer
from app.models.user import User
from app.schemas.project import ProjectCreate


class TestProjectCrudService(unittest.TestCase):
    """ProjectCrudService 单元测试"""

    def setUp(self):
        """初始化测试环境"""
        self.db_mock = MagicMock()
        self.service = ProjectCrudService(self.db_mock)

    def test_get_projects_query_basic(self):
        """测试基础查询构建"""
        # Arrange
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock

        # Act
        result = self.service.get_projects_query()

        # Assert
        self.db_mock.query.assert_called_once_with(Project)
        self.assertEqual(result, query_mock)

    def test_get_projects_query_with_filters(self):
        """测试带筛选条件的查询构建"""
        # Arrange
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value = query_mock

        # Act
        result = self.service.get_projects_query(
            customer_id=1,
            stage="S1",
            status="ST01",
            health="H1",
            is_active=True
        )

        # Assert
        self.db_mock.query.assert_called_once_with(Project)
        # 验证filter被调用了多次
        self.assertGreater(query_mock.filter.call_count, 0)

    def test_get_projects_query_with_overrun_filter(self):
        """测试超支项目筛选"""
        # Arrange
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value = query_mock

        # Act
        result = self.service.get_projects_query(overrun_only=True)

        # Assert
        # 验证超支筛选条件被应用
        query_mock.filter.assert_called()

    def test_apply_sorting_cost_desc(self):
        """测试成本降序排序"""
        # Arrange
        query_mock = MagicMock()

        # Act
        result = self.service.apply_sorting(query_mock, sort="cost_desc")

        # Assert
        query_mock.order_by.assert_called_once()

    def test_apply_sorting_budget_used_pct(self):
        """测试预算使用率排序"""
        # Arrange
        query_mock = MagicMock()

        # Act
        result = self.service.apply_sorting(query_mock, sort="budget_used_pct")

        # Assert
        query_mock.order_by.assert_called_once()

    def test_apply_sorting_default(self):
        """测试默认排序（创建时间倒序）"""
        # Arrange
        query_mock = MagicMock()

        # Act
        result = self.service.apply_sorting(query_mock, sort=None)

        # Assert
        query_mock.order_by.assert_called_once()

    def test_populate_redundant_fields(self):
        """测试冗余字段填充"""
        # Arrange
        customer_mock = MagicMock()
        customer_mock.customer_name = "测试客户"
        
        manager_mock = MagicMock()
        manager_mock.real_name = "张三"
        manager_mock.username = "zhangsan"

        project1 = MagicMock()
        project1.customer_name = None
        project1.customer = customer_mock
        project1.pm_name = None
        project1.manager = manager_mock

        project2 = MagicMock()
        project2.customer_name = "已有客户"
        project2.customer = None
        project2.pm_name = "已有PM"
        project2.manager = None

        projects = [project1, project2]

        # Act
        self.service.populate_redundant_fields(projects)

        # Assert
        self.assertEqual(project1.customer_name, "测试客户")
        self.assertEqual(project1.pm_name, "张三")
        self.assertEqual(project2.customer_name, "已有客户")  # 不覆盖
        self.assertEqual(project2.pm_name, "已有PM")  # 不覆盖

    def test_check_project_code_exists_true(self):
        """测试项目编码存在"""
        # Arrange
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = MagicMock()  # 存在项目

        # Act
        result = self.service.check_project_code_exists("PRJ001")

        # Assert
        self.assertTrue(result)

    def test_check_project_code_exists_false(self):
        """测试项目编码不存在"""
        # Arrange
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = None  # 不存在项目

        # Act
        result = self.service.check_project_code_exists("PRJ999")

        # Assert
        self.assertFalse(result)

    @patch('app.services.project_crud.service.save_obj')
    @patch('app.utils.project_utils.init_project_stages')
    def test_create_project_success(self, mock_init_stages, mock_save_obj):
        """测试成功创建项目"""
        # Arrange
        project_in = ProjectCreate(
            project_code="PRJ001",
            project_name="测试项目",
            customer_id=1,
            pm_id=2,
            budget_amount=100000.0,
        )

        # Mock 项目编码检查（不存在）
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = None

        # Mock 客户查询
        customer_mock = MagicMock()
        customer_mock.customer_name = "测试客户"
        customer_mock.contact_person = "联系人"
        customer_mock.contact_phone = "12345678"
        self.db_mock.query.return_value.get.return_value = customer_mock

        # 第二次query(User)调用应该返回PM
        pm_mock = MagicMock()
        pm_mock.real_name = "项目经理"
        pm_mock.username = "pm_user"

        def query_side_effect(model):
            if model == Project:
                return query_mock
            elif model == Customer:
                mock_customer_query = MagicMock()
                mock_customer_query.get.return_value = customer_mock
                return mock_customer_query
            elif model == User:
                mock_user_query = MagicMock()
                mock_user_query.get.return_value = pm_mock
                return mock_user_query

        self.db_mock.query.side_effect = query_side_effect

        # Act
        result = self.service.create_project(project_in)

        # Assert
        self.assertIsInstance(result, Project)
        self.assertEqual(result.project_code, "PRJ001")
        self.assertEqual(result.project_name, "测试项目")
        mock_save_obj.assert_called_once()
        mock_init_stages.assert_called_once()

    def test_create_project_duplicate_code(self):
        """测试创建项目时编码已存在（应抛出异常）"""
        # Arrange
        project_in = ProjectCreate(
            project_code="PRJ001",
            project_name="测试项目",
            customer_id=1,
            pm_id=2,
            budget_amount=100000.0,
        )

        # Mock 项目编码检查（已存在）
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = MagicMock()  # 存在项目

        # Act & Assert
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as context:
            self.service.create_project(project_in)
        
        self.assertEqual(context.exception.status_code, 400)

    def test_update_project(self):
        """测试更新项目"""
        # Arrange
        project_mock = MagicMock()
        project_mock.id = 1
        project_mock.project_name = "旧项目名"
        
        update_data = {
            "project_name": "新项目名",
            "budget_amount": 200000.0,
        }

        # Act
        result = self.service.update_project(project_mock, update_data)

        # Assert
        self.db_mock.add.assert_called_once_with(project_mock)
        self.db_mock.commit.assert_called_once()
        self.db_mock.refresh.assert_called_once_with(project_mock)

    def test_update_project_with_customer_id_change(self):
        """测试更新项目时修改客户ID（应更新冗余字段）"""
        # Arrange
        project_mock = MagicMock()
        project_mock.customer_id = 2
        
        customer_mock = MagicMock()
        customer_mock.customer_name = "新客户"
        customer_mock.contact_person = "新联系人"
        customer_mock.contact_phone = "99999999"
        
        self.db_mock.query.return_value.get.return_value = customer_mock

        update_data = {"customer_id": 2}

        # Act
        result = self.service.update_project(project_mock, update_data)

        # Assert
        self.db_mock.query.assert_called()

    def test_soft_delete_project(self):
        """测试软删除项目"""
        # Arrange
        project_mock = MagicMock()
        project_mock.id = 1
        project_mock.is_active = True

        # Act
        self.service.soft_delete_project(project_mock)

        # Assert
        self.assertFalse(project_mock.is_active)
        self.db_mock.add.assert_called_once_with(project_mock)
        self.db_mock.commit.assert_called_once()

    @patch('app.services.project_crud.service.CacheService')
    def test_invalidate_project_cache_with_id(self, mock_cache_service_class):
        """测试使项目缓存失效（指定项目ID）"""
        # Arrange
        cache_service_mock = MagicMock()
        mock_cache_service_class.return_value = cache_service_mock

        # Act
        self.service.invalidate_project_cache(project_id=1)

        # Assert
        cache_service_mock.invalidate_project_detail.assert_called_once_with(1)
        cache_service_mock.invalidate_project_list.assert_called_once()

    @patch('app.services.project_crud.service.CacheService')
    def test_invalidate_project_cache_without_id(self, mock_cache_service_class):
        """测试使项目列表缓存失效（不指定项目ID）"""
        # Arrange
        cache_service_mock = MagicMock()
        mock_cache_service_class.return_value = cache_service_mock

        # Act
        self.service.invalidate_project_cache()

        # Assert
        cache_service_mock.invalidate_project_detail.assert_not_called()
        cache_service_mock.invalidate_project_list.assert_called_once()

    def test_get_project_by_id_found(self):
        """测试根据ID获取项目（找到）"""
        # Arrange
        project_mock = MagicMock()
        project_mock.id = 1
        project_mock.customer_name = None
        project_mock.pm_name = None
        
        customer_mock = MagicMock()
        customer_mock.customer_name = "客户A"
        project_mock.customer = customer_mock
        
        manager_mock = MagicMock()
        manager_mock.real_name = "经理B"
        project_mock.manager = manager_mock

        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.options.return_value.filter.return_value.first.return_value = project_mock

        # Act
        result = self.service.get_project_by_id(1)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.customer_name, "客户A")
        self.assertEqual(result.pm_name, "经理B")

    def test_get_project_by_id_not_found(self):
        """测试根据ID获取项目（未找到）"""
        # Arrange
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.options.return_value.filter.return_value.first.return_value = None

        # Act
        result = self.service.get_project_by_id(999)

        # Assert
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
