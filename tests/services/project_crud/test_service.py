# -*- coding: utf-8 -*-
"""
项目CRUD服务测试

覆盖范围：
- 项目查询与筛选（关键词、客户、状态、阶段、健康度、项目类型、项目经理、进度、超支）
- 排序逻辑（成本、预算使用率、默认）
- 分页功能
- CRUD操作（创建、读取、更新、软删除）
- 冗余字段维护（客户、项目经理）
- 关联数据获取（成员、设备、里程碑）
- 缓存失效
- 数据权限过滤
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from app.services.project_crud.service import ProjectCrudService
from app.models.project import Project, Customer, ProjectMember
from app.models.user import User
from app.schemas.project import ProjectCreate
from app.common.pagination import PaginationParams
from fastapi import HTTPException


class TestProjectCrudService:
    """项目CRUD服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock()
        db.query.return_value = Mock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        return ProjectCrudService(db=mock_db)

    @pytest.fixture
    def sample_customer(self):
        """示例客户"""
        return Customer(
            id=1,
            customer_name="测试客户",
            contact_person="张三",
            contact_phone="13800138000"
        )

    @pytest.fixture
    def sample_user(self):
        """示例用户"""
        return User(
            id=10,
            username="pm_wang",
            real_name="王项目经理",
        password_hash="test_hash_123"
    )

    @pytest.fixture
    def sample_project(self, sample_customer, sample_user):
        """示例项目"""
        return Project(
            id=1,
            project_code="PRJ001",
            project_name="测试项目",
            contract_no="CT2024001",
            customer_id=1,
            customer=sample_customer,
            pm_id=10,
            manager=sample_user,
            stage="设计",
            status="进行中",
            health="健康",
            project_type="研发",
            progress_pct=50.0,
            budget_amount=100000.0,
            actual_cost=60000.0,
            is_active=True,
            created_at=datetime.now()
        )

    # ==================== 查询构建测试 ====================

    def test_get_projects_query_basic(self, service, mock_db):
        """测试基础项目查询"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        result = service.get_projects_query()

        mock_db.query.assert_called_once_with(Project)
        assert result == mock_query

    def test_get_projects_query_with_keyword(self, service, mock_db):
        """测试关键词搜索"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        
        with patch('app.services.project_crud.service.apply_keyword_filter') as mock_filter:
            mock_filter.return_value = mock_query
            
            result = service.get_projects_query(keyword="测试")
            
            mock_filter.assert_called_once()
            args = mock_filter.call_args[0]
            assert args[1] == Project
            assert args[2] == "测试"
            assert "project_name" in args[3]

    def test_get_projects_query_with_customer_id(self, service, mock_db):
        """测试客户筛选"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        service.get_projects_query(customer_id=5)

        assert mock_query.filter.called

    def test_get_projects_query_with_stage(self, service, mock_db):
        """测试阶段筛选"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        service.get_projects_query(stage="设计")

        assert mock_query.filter.called

    def test_get_projects_query_with_status(self, service, mock_db):
        """测试状态筛选"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        service.get_projects_query(status="进行中")

        assert mock_query.filter.called

    def test_get_projects_query_with_health(self, service, mock_db):
        """测试健康度筛选"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        service.get_projects_query(health="风险")

        assert mock_query.filter.called

    def test_get_projects_query_with_project_type(self, service, mock_db):
        """测试项目类型筛选"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        service.get_projects_query(project_type="研发")

        assert mock_query.filter.called

    def test_get_projects_query_with_pm_id(self, service, mock_db):
        """测试项目经理筛选"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        service.get_projects_query(pm_id=10)

        assert mock_query.filter.called

    def test_get_projects_query_with_progress_range(self, service, mock_db):
        """测试进度范围筛选"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        service.get_projects_query(min_progress=30.0, max_progress=70.0)

        # 应该调用filter两次（min和max）
        assert mock_query.filter.call_count >= 2

    def test_get_projects_query_with_is_active(self, service, mock_db):
        """测试启用状态筛选"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        service.get_projects_query(is_active=True)

        assert mock_query.filter.called

    def test_get_projects_query_with_overrun_only(self, service, mock_db):
        """测试超支项目筛选"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        service.get_projects_query(overrun_only=True)

        assert mock_query.filter.called

    def test_get_projects_query_with_data_scope(self, service, mock_db):
        """测试数据权限筛选"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_user = Mock(spec=User)

        with patch('app.services.data_scope.DataScopeService') as mock_scope:
            mock_scope.filter_projects_by_scope.return_value = mock_query
            
            service.get_projects_query(current_user=mock_user)
            
            mock_scope.filter_projects_by_scope.assert_called_once()

    # ==================== 排序测试 ====================

    def test_apply_sorting_cost_desc(self, service, mock_db):
        """测试成本降序排序"""
        mock_query = Mock()
        mock_query.order_by.return_value = mock_query

        result = service.apply_sorting(mock_query, sort="cost_desc")

        assert mock_query.order_by.called
        assert result == mock_query

    def test_apply_sorting_cost_asc(self, service, mock_db):
        """测试成本升序排序"""
        mock_query = Mock()
        mock_query.order_by.return_value = mock_query

        result = service.apply_sorting(mock_query, sort="cost_asc")

        assert mock_query.order_by.called
        assert result == mock_query

    def test_apply_sorting_budget_used_pct(self, service, mock_db):
        """测试预算使用率排序"""
        mock_query = Mock()
        mock_query.order_by.return_value = mock_query

        result = service.apply_sorting(mock_query, sort="budget_used_pct")

        assert mock_query.order_by.called
        assert result == mock_query

    def test_apply_sorting_default(self, service, mock_db):
        """测试默认排序（创建时间倒序）"""
        mock_query = Mock()
        mock_query.order_by.return_value = mock_query

        result = service.apply_sorting(mock_query, sort=None)

        assert mock_query.order_by.called
        assert result == mock_query

    # ==================== 分页测试 ====================

    def test_get_projects_with_pagination_success(self, service, mock_db, sample_project):
        """测试分页查询成功"""
        pagination = PaginationParams(page=1, page_size=10, offset=0, limit=10)
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 1
        
        with patch('app.services.project_crud.service.apply_pagination') as mock_paginate:
            mock_paginate.return_value.all.return_value = [sample_project]
            
            projects, total = service.get_projects_with_pagination(pagination)
            
            assert len(projects) == 1
            assert total == 1
            assert projects[0] == sample_project

    def test_get_projects_with_pagination_count_exception(self, service, mock_db):
        """测试统计总数异常时降级处理"""
        pagination = PaginationParams(page=1, page_size=10, offset=0, limit=10)
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.side_effect = Exception("Count error")
        
        with patch('app.services.project_crud.service.apply_pagination') as mock_paginate:
            mock_paginate.return_value.all.return_value = []
            
            projects, total = service.get_projects_with_pagination(pagination)
            
            assert total == 0  # 降级为0
            assert projects == []

    # ==================== 冗余字段维护测试 ====================

    def test_populate_redundant_fields(self, service, sample_project, sample_customer, sample_user):
        """测试补充冗余字段"""
        # 清空冗余字段
        sample_project.customer_name = None
        sample_project.pm_name = None

        service.populate_redundant_fields([sample_project])

        assert sample_project.customer_name == "测试客户"
        assert sample_project.pm_name == "王项目经理"

    def test_populate_redundant_fields_no_customer(self, service, sample_project):
        """测试没有客户时不填充"""
        sample_project.customer = None
        sample_project.customer_name = None

        service.populate_redundant_fields([sample_project])

        assert sample_project.customer_name is None

    def test_populate_redundant_fields_no_manager(self, service, sample_project):
        """测试没有项目经理时不填充"""
        sample_project.manager = None
        sample_project.pm_name = None

        service.populate_redundant_fields([sample_project])

        assert sample_project.pm_name is None

    # ==================== CRUD操作测试 ====================

    def test_check_project_code_exists_true(self, service, mock_db, sample_project):
        """测试项目编码存在"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_project

        result = service.check_project_code_exists("PRJ001")

        assert result is True

    def test_check_project_code_exists_false(self, service, mock_db):
        """测试项目编码不存在"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = service.check_project_code_exists("PRJ999")

        assert result is False

    def test_create_project_success(self, service, mock_db, sample_customer, sample_user):
        """测试创建项目成功"""
        project_in = ProjectCreate(
            project_code="PRJ002",
            project_name="新项目",
            customer_id=1,
            pm_id=10,
            budget_amount=200000.0
        )

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # 编码不存在
        mock_db.query.return_value.get.side_effect = [sample_customer, sample_user]

        with patch('app.services.project_crud.service.save_obj') as mock_save:
            with patch('app.utils.project_utils.init_project_stages'):
                project = service.create_project(project_in)

                assert project.project_code == "PRJ002"
                assert project.project_name == "新项目"
                mock_save.assert_called_once()

    def test_create_project_duplicate_code(self, service, mock_db, sample_project):
        """测试创建项目时编码重复"""
        project_in = ProjectCreate(
            project_code="PRJ001",  # 已存在的编码
            project_name="重复项目",
            customer_id=1,
            pm_id=10
        )

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_project  # 编码已存在

        with pytest.raises(HTTPException) as exc_info:
            service.create_project(project_in)

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail

    def test_get_project_by_id_success(self, service, mock_db, sample_project):
        """测试根据ID获取项目成功"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_project

        project = service.get_project_by_id(1)

        assert project == sample_project
        assert project.customer_name == "测试客户"

    def test_get_project_by_id_not_found(self, service, mock_db):
        """测试项目不存在"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        project = service.get_project_by_id(999)

        assert project is None

    def test_update_project(self, service, mock_db, sample_project):
        """测试更新项目"""
        update_data = {
            "project_name": "更新后的项目名",
            "progress_pct": 75.0
        }

        updated_project = service.update_project(sample_project, update_data)

        assert updated_project.project_name == "更新后的项目名"
        assert updated_project.progress_pct == 75.0
        mock_db.add.assert_called_once_with(sample_project)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_project)

    def test_update_project_with_customer_change(self, service, mock_db, sample_project, sample_customer):
        """测试更新项目时更改客户"""
        update_data = {"customer_id": 2}
        
        new_customer = Customer(id=2, customer_name="新客户", contact_person="李四", contact_phone="13900139000")
        mock_db.query.return_value.get.return_value = new_customer

        updated_project = service.update_project(sample_project, update_data)

        assert updated_project.customer_id == 2
        assert updated_project.customer_name == "新客户"

    def test_soft_delete_project(self, service, mock_db, sample_project):
        """测试软删除项目"""
        service.soft_delete_project(sample_project)

        assert sample_project.is_active is False
        mock_db.add.assert_called_once_with(sample_project)
        mock_db.commit.assert_called_once()

    # ==================== 关联数据获取测试 ====================

    def test_get_project_members(self, service, mock_db, sample_user):
        """测试获取项目成员列表"""
        member = ProjectMember(
            id=1,
            project_id=1,
            user_id=10,
            user=sample_user,
            role_code="pm",
            allocation_pct=100.0,
            is_active=True
        )

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [member]

        members = service.get_project_members(1)

        assert len(members) == 1
        assert members[0].username == "pm_wang"
        assert members[0].role_code == "pm"

    def test_get_project_machines(self, service):
        """测试获取项目设备列表"""
        mock_project = Mock()
        mock_machine = Mock()
        
        # 模拟machines关系返回列表
        mock_project.machines.all.return_value = [mock_machine]

        with patch('app.schemas.project.MachineResponse.model_validate') as mock_validate:
            mock_validate.return_value = Mock(id=1, machine_name="设备1")
            
            machines = service.get_project_machines(mock_project)
            
            assert len(machines) == 1

    def test_get_project_milestones(self, service):
        """测试获取项目里程碑列表"""
        mock_project = Mock()
        mock_milestone = Mock()
        
        # 模拟milestones关系返回列表
        mock_project.milestones.all.return_value = [mock_milestone]

        with patch('app.schemas.project.MilestoneResponse.model_validate') as mock_validate:
            mock_validate.return_value = Mock(id=1, milestone_name="里程碑1")
            
            milestones = service.get_project_milestones(mock_project)
            
            assert len(milestones) == 1

    # ==================== 缓存管理测试 ====================

    def test_invalidate_project_cache_with_id(self, service):
        """测试使指定项目缓存失效"""
        with patch('app.services.cache_service.CacheService') as mock_cache_cls:
            mock_cache = Mock()
            mock_cache_cls.return_value = mock_cache
            
            service.invalidate_project_cache(project_id=1)
            
            mock_cache.invalidate_project_detail.assert_called_once_with(1)
            mock_cache.invalidate_project_list.assert_called_once()

    def test_invalidate_project_cache_all(self, service):
        """测试使所有项目缓存失效"""
        with patch('app.services.cache_service.CacheService') as mock_cache_cls:
            mock_cache = Mock()
            mock_cache_cls.return_value = mock_cache
            
            service.invalidate_project_cache()
            
            mock_cache.invalidate_project_detail.assert_not_called()
            mock_cache.invalidate_project_list.assert_called_once()

    def test_invalidate_project_cache_exception(self, service):
        """测试缓存失效异常时不影响主流程"""
        with patch('app.services.cache_service.CacheService') as mock_cache_cls:
            mock_cache_cls.side_effect = Exception("Cache error")
            
            # 不应该抛出异常
            service.invalidate_project_cache(project_id=1)

    # ==================== 私有方法测试 ====================

    def test_update_customer_redundant_fields(self, service, mock_db, sample_project, sample_customer):
        """测试更新客户冗余字段"""
        new_customer = Customer(
            id=2,
            customer_name="新客户公司",
            contact_person="赵六",
            contact_phone="13700137000"
        )
        mock_db.query.return_value.get.return_value = new_customer
        sample_project.customer_id = 2

        service._update_customer_redundant_fields(sample_project)

        assert sample_project.customer_name == "新客户公司"
        assert sample_project.customer_contact == "赵六"
        assert sample_project.customer_phone == "13700137000"

    def test_update_pm_redundant_fields(self, service, mock_db, sample_project):
        """测试更新项目经理冗余字段"""
        new_pm = User(id=20, username="new_pm", real_name="新经理",
        password_hash="test_hash_123"
    )
        mock_db.query.return_value.get.return_value = new_pm
        sample_project.pm_id = 20

        service._update_pm_redundant_fields(sample_project)

        assert sample_project.pm_name == "新经理"

    def test_update_pm_redundant_fields_no_realname(self, service, mock_db, sample_project):
        """测试项目经理没有真实姓名时使用用户名"""
        new_pm = User(id=20, username="username_only", real_name=None,
        password_hash="test_hash_123"
    )
        mock_db.query.return_value.get.return_value = new_pm
        sample_project.pm_id = 20

        service._update_pm_redundant_fields(sample_project)

        assert sample_project.pm_name == "username_only"
