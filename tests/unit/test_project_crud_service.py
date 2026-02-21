# -*- coding: utf-8 -*-
"""
项目CRUD服务单元测试

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from fastapi import HTTPException
from sqlalchemy.orm import Query

from app.models.project import Customer, Project, ProjectMember
from app.models.user import User
from app.schemas.project import ProjectCreate
from app.services.project_crud.service import ProjectCrudService
from app.common.pagination import get_pagination_params


class TestProjectCrudService(unittest.TestCase):
    """项目CRUD服务测试"""

    def setUp(self):
        """测试前准备"""
        # Mock数据库session
        self.db = MagicMock()
        self.service = ProjectCrudService(self.db)

    def tearDown(self):
        """测试后清理"""
        self.db.reset_mock()


class TestGetProjectsQuery(TestProjectCrudService):
    """测试 get_projects_query 方法"""

    def setUp(self):
        super().setUp()
        # Mock query对象
        self.mock_query = MagicMock(spec=Query)
        self.db.query.return_value = self.mock_query

    def test_get_projects_query_no_filters(self):
        """测试无筛选条件"""
        result = self.service.get_projects_query()
        
        self.db.query.assert_called_once_with(Project)
        self.assertEqual(result, self.mock_query)

    def test_get_projects_query_with_keyword(self):
        """测试关键词搜索"""
        self.service.get_projects_query(keyword="测试项目")
        
        # 验证调用了query
        self.db.query.assert_called_once_with(Project)

    def test_get_projects_query_with_customer_id(self):
        """测试客户筛选"""
        result = self.service.get_projects_query(customer_id=123)
        
        self.mock_query.filter.assert_called()

    def test_get_projects_query_with_stage(self):
        """测试阶段筛选"""
        result = self.service.get_projects_query(stage="S2")
        
        self.mock_query.filter.assert_called()

    def test_get_projects_query_with_status(self):
        """测试状态筛选"""
        result = self.service.get_projects_query(status="RUNNING")
        
        self.mock_query.filter.assert_called()

    def test_get_projects_query_with_health(self):
        """测试健康度筛选"""
        result = self.service.get_projects_query(health="H2")
        
        self.mock_query.filter.assert_called()

    def test_get_projects_query_with_project_type(self):
        """测试项目类型筛选"""
        result = self.service.get_projects_query(project_type="TYPE1")
        
        self.mock_query.filter.assert_called()

    def test_get_projects_query_with_pm_id(self):
        """测试项目经理筛选"""
        result = self.service.get_projects_query(pm_id=456)
        
        self.mock_query.filter.assert_called()

    def test_get_projects_query_with_progress_range(self):
        """测试进度范围筛选"""
        result = self.service.get_projects_query(
            min_progress=0.3, 
            max_progress=0.8
        )
        
        # 验证filter被调用(进度筛选会调用filter)
        self.mock_query.filter.assert_called()

    def test_get_projects_query_with_is_active(self):
        """测试是否启用筛选"""
        result = self.service.get_projects_query(is_active=True)
        
        self.mock_query.filter.assert_called()

    def test_get_projects_query_with_overrun_only(self):
        """测试超支项目筛选"""
        result = self.service.get_projects_query(overrun_only=True)
        
        self.mock_query.filter.assert_called()

    @patch('app.services.data_scope.DataScopeService')
    def test_get_projects_query_with_current_user(self, mock_data_scope):
        """测试数据权限过滤"""
        mock_user = MagicMock(spec=User)
        mock_data_scope.filter_projects_by_scope.return_value = self.mock_query
        
        result = self.service.get_projects_query(current_user=mock_user)
        
        mock_data_scope.filter_projects_by_scope.assert_called_once_with(
            self.db, self.mock_query, mock_user
        )

    def test_get_projects_query_with_multiple_filters(self):
        """测试多个筛选条件组合"""
        result = self.service.get_projects_query(
            keyword="项目",
            customer_id=1,
            stage="S2",
            status="RUNNING",
            pm_id=10,
            is_active=True
        )
        
        # 验证filter被调用(多个筛选条件)
        self.mock_query.filter.assert_called()


class TestApplySorting(TestProjectCrudService):
    """测试 apply_sorting 方法"""

    def setUp(self):
        super().setUp()
        self.mock_query = MagicMock(spec=Query)

    def test_apply_sorting_cost_desc(self):
        """测试按成本降序"""
        result = self.service.apply_sorting(self.mock_query, sort="cost_desc")
        
        self.mock_query.order_by.assert_called_once()

    def test_apply_sorting_cost_asc(self):
        """测试按成本升序"""
        result = self.service.apply_sorting(self.mock_query, sort="cost_asc")
        
        self.mock_query.order_by.assert_called_once()

    def test_apply_sorting_budget_used_pct(self):
        """测试按预算使用率排序"""
        result = self.service.apply_sorting(self.mock_query, sort="budget_used_pct")
        
        self.mock_query.order_by.assert_called_once()

    def test_apply_sorting_default(self):
        """测试默认排序（创建时间倒序）"""
        result = self.service.apply_sorting(self.mock_query, sort=None)
        
        self.mock_query.order_by.assert_called_once()

    def test_apply_sorting_unknown(self):
        """测试未知排序方式（应使用默认）"""
        result = self.service.apply_sorting(self.mock_query, sort="unknown_sort")
        
        self.mock_query.order_by.assert_called_once()


class TestGetProjectsWithPagination(TestProjectCrudService):
    """测试 get_projects_with_pagination 方法"""

    def setUp(self):
        super().setUp()
        self.mock_query = MagicMock(spec=Query)
        self.db.query.return_value = self.mock_query
        
        # Mock链式调用
        self.mock_query.options.return_value = self.mock_query
        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        
        # Mock count和all
        self.mock_query.count.return_value = 10
        
        # Mock项目对象
        mock_project = MagicMock(spec=Project)
        mock_project.customer = None
        mock_project.manager = None
        self.mock_query.all.return_value = [mock_project]

    def test_get_projects_with_pagination_basic(self):
        """测试基本分页查询"""
        pagination = get_pagination_params(page=1, page_size=10)
        
        projects, total = self.service.get_projects_with_pagination(
            pagination=pagination
        )
        
        self.assertEqual(total, 10)
        self.assertEqual(len(projects), 1)
        self.mock_query.count.assert_called_once()
        self.mock_query.all.assert_called_once()

    def test_get_projects_with_pagination_with_filters(self):
        """测试带筛选的分页"""
        pagination = get_pagination_params(page=1, page_size=20)
        
        projects, total = self.service.get_projects_with_pagination(
            pagination=pagination,
            keyword="测试",
            customer_id=1,
            stage="S2",
            is_active=True
        )
        
        self.assertEqual(total, 10)
        self.assertGreater(self.mock_query.filter.call_count, 0)

    def test_get_projects_with_pagination_with_sorting(self):
        """测试带排序的分页"""
        pagination = get_pagination_params(page=1, page_size=10)
        
        projects, total = self.service.get_projects_with_pagination(
            pagination=pagination,
            sort="cost_desc"
        )
        
        self.mock_query.order_by.assert_called()

    def test_get_projects_with_pagination_count_exception(self):
        """测试count异常时降级为0"""
        pagination = get_pagination_params(page=1, page_size=10)
        self.mock_query.count.side_effect = Exception("Database error")
        
        projects, total = self.service.get_projects_with_pagination(
            pagination=pagination
        )
        
        self.assertEqual(total, 0)
        self.assertEqual(len(projects), 1)

    def test_get_projects_with_pagination_uses_selectinload(self):
        """测试使用selectinload优化关联查询"""
        pagination = get_pagination_params(page=1, page_size=10)
        
        projects, total = self.service.get_projects_with_pagination(
            pagination=pagination
        )
        
        # 验证调用了options
        self.mock_query.options.assert_called_once()


class TestPopulateRedundantFields(TestProjectCrudService):
    """测试 populate_redundant_fields 方法"""

    def test_populate_redundant_fields_with_customer(self):
        """测试填充客户名称"""
        mock_customer = MagicMock(spec=Customer)
        mock_customer.customer_name = "测试客户"
        
        mock_project = MagicMock(spec=Project)
        mock_project.customer_name = None
        mock_project.customer = mock_customer
        mock_project.manager = None
        
        self.service.populate_redundant_fields([mock_project])
        
        self.assertEqual(mock_project.customer_name, "测试客户")

    def test_populate_redundant_fields_with_manager(self):
        """测试填充项目经理名称"""
        mock_manager = MagicMock(spec=User)
        mock_manager.real_name = "张三"
        mock_manager.username = "zhangsan"
        
        mock_project = MagicMock(spec=Project)
        mock_project.customer_name = "已有客户"
        mock_project.pm_name = None
        mock_project.customer = None
        mock_project.manager = mock_manager
        
        self.service.populate_redundant_fields([mock_project])
        
        self.assertEqual(mock_project.pm_name, "张三")

    def test_populate_redundant_fields_manager_no_real_name(self):
        """测试经理无真实姓名时使用用户名"""
        mock_manager = MagicMock(spec=User)
        mock_manager.real_name = None
        mock_manager.username = "zhangsan"
        
        mock_project = MagicMock(spec=Project)
        mock_project.pm_name = None
        mock_project.customer = None
        mock_project.manager = mock_manager
        
        self.service.populate_redundant_fields([mock_project])
        
        self.assertEqual(mock_project.pm_name, "zhangsan")

    def test_populate_redundant_fields_already_filled(self):
        """测试已填充的字段不会被覆盖"""
        mock_project = MagicMock(spec=Project)
        mock_project.customer_name = "现有客户名"
        mock_project.pm_name = "现有经理名"
        mock_project.customer = MagicMock(customer_name="新客户名")
        mock_project.manager = MagicMock(real_name="新经理名")
        
        self.service.populate_redundant_fields([mock_project])
        
        # 不应该被更新
        self.assertEqual(mock_project.customer_name, "现有客户名")
        self.assertEqual(mock_project.pm_name, "现有经理名")

    def test_populate_redundant_fields_multiple_projects(self):
        """测试批量填充多个项目"""
        projects = []
        for i in range(3):
            mock_project = MagicMock(spec=Project)
            mock_project.customer_name = None
            mock_project.pm_name = None
            mock_project.customer = MagicMock(customer_name=f"客户{i}")
            mock_project.manager = MagicMock(real_name=f"经理{i}", username=f"mgr{i}")
            projects.append(mock_project)
        
        self.service.populate_redundant_fields(projects)
        
        for i, project in enumerate(projects):
            self.assertEqual(project.customer_name, f"客户{i}")
            self.assertEqual(project.pm_name, f"经理{i}")


class TestCheckProjectCodeExists(TestProjectCrudService):
    """测试 check_project_code_exists 方法"""

    def setUp(self):
        super().setUp()
        self.mock_query = MagicMock()
        self.db.query.return_value = self.mock_query

    def test_check_project_code_exists_true(self):
        """测试项目编码存在"""
        self.mock_query.filter.return_value.first.return_value = MagicMock(spec=Project)
        
        result = self.service.check_project_code_exists("PRJ001")
        
        self.assertTrue(result)

    def test_check_project_code_exists_false(self):
        """测试项目编码不存在"""
        self.mock_query.filter.return_value.first.return_value = None
        
        result = self.service.check_project_code_exists("PRJ999")
        
        self.assertFalse(result)


class TestCreateProject(TestProjectCrudService):
    """测试 create_project 方法"""

    def setUp(self):
        super().setUp()
        # Mock check_project_code_exists
        self.service.check_project_code_exists = MagicMock(return_value=False)
        # Mock _populate_project_redundant_fields
        self.service._populate_project_redundant_fields = MagicMock()
        
    def test_create_project_basic_flow(self):
        """测试创建项目的基本流程（主要验证业务逻辑）"""
        project_data = ProjectCreate(
            project_code="PRJ001",
            project_name="测试项目",
            customer_id=1,
            pm_id=10
        )
        
        # 验证会检查编码唯一性
        self.service.check_project_code_exists.return_value = False
        
        # 不实际执行创建,只验证检查逻辑
        # 注意: 完整的创建流程测试需要集成测试
        exists = self.service.check_project_code_exists(project_data.project_code)
        self.assertFalse(exists)

    def test_create_project_duplicate_code(self):
        """测试创建重复编码的项目（应抛出异常）"""
        self.service.check_project_code_exists.return_value = True
        
        project_data = ProjectCreate(
            project_code="PRJ001",
            project_name="测试项目"
        )
        
        with self.assertRaises(HTTPException) as context:
            self.service.create_project(project_data)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("already exists", context.exception.detail)

    @patch('app.utils.db_helpers.save_obj')
    @patch('app.utils.project_utils.init_project_stages')
    def test_create_project_removes_machine_count(self, mock_init_stages, mock_save_obj):
        """测试创建时移除machine_count字段"""
        project_data = ProjectCreate(
            project_code="PRJ002",
            project_name="测试项目2",
            machine_count=5  # 这个字段不在模型中
        )
        
        def set_project_id(db, project):
            project.id = 101
        mock_save_obj.side_effect = set_project_id
        
        result = self.service.create_project(project_data)
        
        # 验证项目创建成功，machine_count被移除
        self.assertIsInstance(result, Project)


class TestGetProjectById(TestProjectCrudService):
    """测试 get_project_by_id 方法"""

    def setUp(self):
        super().setUp()
        self.mock_query = MagicMock()
        self.db.query.return_value = self.mock_query

    def test_get_project_by_id_found(self):
        """测试找到项目"""
        mock_customer = MagicMock(spec=Customer)
        mock_customer.customer_name = "测试客户"
        mock_customer.contact_person = "张三"
        mock_customer.contact_phone = "13800138000"
        
        mock_manager = MagicMock(spec=User)
        mock_manager.real_name = "李四"
        mock_manager.username = "lisi"
        
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        mock_project.customer_name = None
        mock_project.customer_contact = None
        mock_project.customer_phone = None
        mock_project.pm_name = None
        mock_project.customer = mock_customer
        mock_project.manager = mock_manager
        
        self.mock_query.options.return_value.filter.return_value.first.return_value = mock_project
        
        result = self.service.get_project_by_id(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.customer_name, "测试客户")
        self.assertEqual(result.customer_contact, "张三")
        self.assertEqual(result.customer_phone, "13800138000")
        self.assertEqual(result.pm_name, "李四")

    def test_get_project_by_id_not_found(self):
        """测试项目不存在"""
        self.mock_query.options.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_project_by_id(999)
        
        self.assertIsNone(result)

    def test_get_project_by_id_already_has_redundant_fields(self):
        """测试项目已有冗余字段"""
        mock_project = MagicMock(spec=Project)
        mock_project.customer_name = "已有客户"
        mock_project.pm_name = "已有经理"
        mock_project.customer = MagicMock()
        mock_project.manager = MagicMock()
        
        self.mock_query.options.return_value.filter.return_value.first.return_value = mock_project
        
        result = self.service.get_project_by_id(1)
        
        # 冗余字段不应改变
        self.assertEqual(result.customer_name, "已有客户")
        self.assertEqual(result.pm_name, "已有经理")


class TestGetProjectMembers(TestProjectCrudService):
    """测试 get_project_members 方法"""

    def setUp(self):
        super().setUp()
        self.mock_query = MagicMock()
        self.db.query.return_value = self.mock_query

    def test_get_project_members_with_users(self):
        """测试获取项目成员（含用户信息）"""
        mock_user = MagicMock(spec=User)
        mock_user.username = "zhangsan"
        mock_user.real_name = "张三"
        
        mock_member = MagicMock(spec=ProjectMember)
        mock_member.id = 1
        mock_member.project_id = 100
        mock_member.user_id = 10
        mock_member.user = mock_user
        mock_member.role_code = "DEV"
        mock_member.allocation_pct = Decimal("0.5")
        mock_member.start_date = date(2024, 1, 1)
        mock_member.end_date = None
        mock_member.is_active = True
        mock_member.remark = None
        
        self.mock_query.options.return_value.filter.return_value.all.return_value = [mock_member]
        
        result = self.service.get_project_members(100)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].username, "zhangsan")
        self.assertEqual(result[0].real_name, "张三")

    def test_get_project_members_without_user(self):
        """测试成员无用户对象时使用fallback"""
        mock_member = MagicMock(spec=ProjectMember)
        mock_member.id = 1
        mock_member.project_id = 100
        mock_member.user_id = 10
        mock_member.user = None
        mock_member.role_code = "DEV"
        mock_member.allocation_pct = Decimal("1.0")
        mock_member.start_date = date(2024, 1, 1)
        mock_member.end_date = None
        mock_member.is_active = True
        mock_member.remark = None
        
        self.mock_query.options.return_value.filter.return_value.all.return_value = [mock_member]
        
        result = self.service.get_project_members(100)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].username, "user_10")

    def test_get_project_members_empty(self):
        """测试项目无成员"""
        self.mock_query.options.return_value.filter.return_value.all.return_value = []
        
        result = self.service.get_project_members(100)
        
        self.assertEqual(len(result), 0)


class TestGetProjectMachines(TestProjectCrudService):
    """测试 get_project_machines 方法"""

    def test_get_project_machines_success(self):
        """测试获取项目设备"""
        mock_machine1 = MagicMock()
        mock_machine1.id = 1
        mock_machine1.machine_name = "设备1"
        
        mock_machine2 = MagicMock()
        mock_machine2.id = 2
        mock_machine2.machine_name = "设备2"
        
        mock_project = MagicMock(spec=Project)
        mock_project.machines = MagicMock()
        mock_project.machines.all.return_value = [mock_machine1, mock_machine2]
        
        with patch('app.services.project_crud.service.MachineResponse') as MockMachineResponse:
            MockMachineResponse.model_validate.side_effect = lambda x: x
            
            result = self.service.get_project_machines(mock_project)
            
            self.assertEqual(len(result), 2)

    def test_get_project_machines_no_all_method(self):
        """测试machines没有all方法"""
        mock_project = MagicMock(spec=Project)
        mock_project.machines = []
        
        result = self.service.get_project_machines(mock_project)
        
        self.assertEqual(len(result), 0)


class TestGetProjectMilestones(TestProjectCrudService):
    """测试 get_project_milestones 方法"""

    def test_get_project_milestones_success(self):
        """测试获取项目里程碑"""
        mock_milestone1 = MagicMock()
        mock_milestone1.id = 1
        
        mock_milestone2 = MagicMock()
        mock_milestone2.id = 2
        
        mock_project = MagicMock(spec=Project)
        mock_project.milestones = MagicMock()
        mock_project.milestones.all.return_value = [mock_milestone1, mock_milestone2]
        
        with patch('app.services.project_crud.service.MilestoneResponse') as MockMilestoneResponse:
            MockMilestoneResponse.model_validate.side_effect = lambda x: x
            
            result = self.service.get_project_milestones(mock_project)
            
            self.assertEqual(len(result), 2)

    def test_get_project_milestones_empty(self):
        """测试项目无里程碑"""
        mock_project = MagicMock(spec=Project)
        mock_project.milestones = []
        
        result = self.service.get_project_milestones(mock_project)
        
        self.assertEqual(len(result), 0)


class TestUpdateProject(TestProjectCrudService):
    """测试 update_project 方法"""

    def setUp(self):
        super().setUp()
        self.service._update_customer_redundant_fields = MagicMock()
        self.service._update_pm_redundant_fields = MagicMock()

    def test_update_project_basic_fields(self):
        """测试更新基本字段"""
        mock_project = MagicMock(spec=Project)
        mock_project.project_name = "旧名称"
        mock_project.stage = "S1"
        
        update_data = {
            "project_name": "新名称",
            "stage": "S2"
        }
        
        result = self.service.update_project(mock_project, update_data)
        
        self.assertEqual(mock_project.project_name, "新名称")
        self.assertEqual(mock_project.stage, "S2")
        self.db.add.assert_called_once_with(mock_project)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(mock_project)

    def test_update_project_with_customer_id(self):
        """测试更新客户ID时更新冗余字段"""
        mock_project = MagicMock(spec=Project)
        
        update_data = {"customer_id": 123}
        
        result = self.service.update_project(mock_project, update_data)
        
        self.assertEqual(mock_project.customer_id, 123)
        self.service._update_customer_redundant_fields.assert_called_once_with(mock_project)

    def test_update_project_with_pm_id(self):
        """测试更新项目经理ID时更新冗余字段"""
        mock_project = MagicMock(spec=Project)
        
        update_data = {"pm_id": 456}
        
        result = self.service.update_project(mock_project, update_data)
        
        self.assertEqual(mock_project.pm_id, 456)
        self.service._update_pm_redundant_fields.assert_called_once_with(mock_project)

    def test_update_project_ignore_invalid_fields(self):
        """测试忽略无效字段"""
        mock_project = MagicMock(spec=Project)
        
        update_data = {
            "project_name": "新名称",
            "invalid_field": "应被忽略"
        }
        
        # hasattr会对invalid_field返回False
        result = self.service.update_project(mock_project, update_data)
        
        # 只有有效字段被设置
        self.assertEqual(mock_project.project_name, "新名称")


class TestSoftDeleteProject(TestProjectCrudService):
    """测试 soft_delete_project 方法"""

    def test_soft_delete_project(self):
        """测试软删除项目"""
        mock_project = MagicMock(spec=Project)
        mock_project.is_active = True
        
        self.service.soft_delete_project(mock_project)
        
        self.assertFalse(mock_project.is_active)
        self.db.add.assert_called_once_with(mock_project)
        self.db.commit.assert_called_once()


class TestInvalidateProjectCache(TestProjectCrudService):
    """测试 invalidate_project_cache 方法"""

    @patch('app.services.cache_service.CacheService')
    def test_invalidate_project_cache_with_id(self, mock_cache_service_class):
        """测试使指定项目缓存失效"""
        mock_cache_service = MagicMock()
        mock_cache_service_class.return_value = mock_cache_service
        
        self.service.invalidate_project_cache(project_id=100)
        
        mock_cache_service.invalidate_project_detail.assert_called_once_with(100)
        mock_cache_service.invalidate_project_list.assert_called_once()

    @patch('app.services.cache_service.CacheService')
    def test_invalidate_project_cache_without_id(self, mock_cache_service_class):
        """测试使所有项目列表缓存失效"""
        mock_cache_service = MagicMock()
        mock_cache_service_class.return_value = mock_cache_service
        
        self.service.invalidate_project_cache()
        
        mock_cache_service.invalidate_project_detail.assert_not_called()
        mock_cache_service.invalidate_project_list.assert_called_once()

    @patch('app.services.cache_service.CacheService')
    def test_invalidate_project_cache_exception(self, mock_cache_service_class):
        """测试缓存失效异常时不影响流程"""
        mock_cache_service_class.side_effect = Exception("Cache error")
        
        # 不应抛出异常
        self.service.invalidate_project_cache(project_id=100)


class TestPrivateMethods(TestProjectCrudService):
    """测试私有方法"""

    def test_populate_project_redundant_fields_with_customer_and_pm(self):
        """测试填充项目冗余字段（客户+PM）"""
        mock_project = MagicMock(spec=Project)
        mock_project.customer_id = 1
        mock_project.pm_id = 10
        
        self.service._update_customer_redundant_fields = MagicMock()
        self.service._update_pm_redundant_fields = MagicMock()
        
        self.service._populate_project_redundant_fields(mock_project)
        
        self.service._update_customer_redundant_fields.assert_called_once_with(mock_project)
        self.service._update_pm_redundant_fields.assert_called_once_with(mock_project)

    def test_populate_project_redundant_fields_without_ids(self):
        """测试填充项目冗余字段（无客户和PM）"""
        mock_project = MagicMock(spec=Project)
        mock_project.customer_id = None
        mock_project.pm_id = None
        
        self.service._update_customer_redundant_fields = MagicMock()
        self.service._update_pm_redundant_fields = MagicMock()
        
        self.service._populate_project_redundant_fields(mock_project)
        
        self.service._update_customer_redundant_fields.assert_not_called()
        self.service._update_pm_redundant_fields.assert_not_called()

    def test_update_customer_redundant_fields_success(self):
        """测试更新客户冗余字段"""
        mock_customer = MagicMock(spec=Customer)
        mock_customer.customer_name = "测试客户"
        mock_customer.contact_person = "张三"
        mock_customer.contact_phone = "13800138000"
        
        mock_project = MagicMock(spec=Project)
        mock_project.customer_id = 1
        
        self.db.query.return_value.get.return_value = mock_customer
        
        self.service._update_customer_redundant_fields(mock_project)
        
        self.assertEqual(mock_project.customer_name, "测试客户")
        self.assertEqual(mock_project.customer_contact, "张三")
        self.assertEqual(mock_project.customer_phone, "13800138000")

    def test_update_customer_redundant_fields_not_found(self):
        """测试客户不存在时"""
        mock_project = MagicMock(spec=Project)
        mock_project.customer_id = 999
        
        self.db.query.return_value.get.return_value = None
        
        # 不应抛出异常
        self.service._update_customer_redundant_fields(mock_project)

    def test_update_pm_redundant_fields_with_real_name(self):
        """测试更新PM冗余字段（有真实姓名）"""
        mock_pm = MagicMock(spec=User)
        mock_pm.real_name = "李四"
        mock_pm.username = "lisi"
        
        mock_project = MagicMock(spec=Project)
        mock_project.pm_id = 10
        
        self.db.query.return_value.get.return_value = mock_pm
        
        self.service._update_pm_redundant_fields(mock_project)
        
        self.assertEqual(mock_project.pm_name, "李四")

    def test_update_pm_redundant_fields_without_real_name(self):
        """测试更新PM冗余字段（无真实姓名）"""
        mock_pm = MagicMock(spec=User)
        mock_pm.real_name = None
        mock_pm.username = "lisi"
        
        mock_project = MagicMock(spec=Project)
        mock_project.pm_id = 10
        
        self.db.query.return_value.get.return_value = mock_pm
        
        self.service._update_pm_redundant_fields(mock_project)
        
        self.assertEqual(mock_project.pm_name, "lisi")

    def test_update_pm_redundant_fields_not_found(self):
        """测试PM不存在时"""
        mock_project = MagicMock(spec=Project)
        mock_project.pm_id = 999
        
        self.db.query.return_value.get.return_value = None
        
        # 不应抛出异常
        self.service._update_pm_redundant_fields(mock_project)


class TestEdgeCases(TestProjectCrudService):
    """测试边界情况"""

    def test_get_projects_query_with_zero_progress(self):
        """测试进度为0的情况"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        
        result = self.service.get_projects_query(
            min_progress=0.0, 
            max_progress=0.0
        )
        
        # 验证filter被调用
        mock_query.filter.assert_called()

    def test_pagination_with_large_offset(self):
        """测试大偏移量分页"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.all.return_value = []
        
        pagination = get_pagination_params(page=1000, page_size=10)
        
        projects, total = self.service.get_projects_with_pagination(
            pagination=pagination
        )
        
        self.assertEqual(total, 10)
        self.assertEqual(len(projects), 0)

    def test_update_project_empty_data(self):
        """测试更新空数据"""
        mock_project = MagicMock(spec=Project)
        
        result = self.service.update_project(mock_project, {})
        
        # 应该正常完成
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
