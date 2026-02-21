# -*- coding: utf-8 -*-
"""
全面测试 app/services/project/core_service.py
目标：60%+ 覆盖率，18-26个测试用例
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock, call

try:
    from app.services.project.core_service import ProjectCoreService
    from app.schemas.engineer import MyProjectListResponse, MyProjectResponse, TaskStatsResponse
    from app.schemas.common import PaginatedResponse
    from app.schemas.project import ProjectListResponse
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


# ===================================================================
# Fixtures
# ===================================================================
@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def mock_user():
    """模拟当前用户"""
    user = MagicMock()
    user.id = 1
    user.username = "test_user"
    user.real_name = "Test User"
    return user


@pytest.fixture
def service(mock_db):
    """创建服务实例，patch DataScopeService 避免导入问题"""
    with patch("app.services.project.core_service.DataScopeService"):
        return ProjectCoreService(db=mock_db)


@pytest.fixture
def mock_project():
    """创建模拟项目对象"""
    project = MagicMock()
    project.id = 100
    project.project_code = "PRJ001"
    project.project_name = "Test Project"
    project.customer_name = "Test Customer"
    project.stage = "S2"
    project.status = "ST02"
    project.health = "H2"
    project.progress_pct = 50.0
    project.pm_id = 10
    project.pm_name = "Project Manager"
    # 使用 date 而非 datetime，满足 Pydantic 验证要求
    project.planned_start_date = datetime.now().date()
    project.planned_end_date = (datetime.now() + timedelta(days=30)).date()
    project.updated_at = datetime.now()
    project.is_active = True
    project.dept_id = 5
    project.created_by = 10
    return project


# ===================================================================
# 1. 初始化测试 (1个)
# ===================================================================
def test_init_stores_db_session(mock_db):
    """测试服务初始化时正确存储 db 会话"""
    with patch("app.services.project.core_service.DataScopeService"):
        service = ProjectCoreService(db=mock_db)
        assert service.db is mock_db


# ===================================================================
# 2. 基础查询与分页 (4个)
# ===================================================================
def test_base_query_filters_active_projects(service, mock_db):
    """测试 _base_query 过滤 is_active=True 的项目"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    
    result = service._base_query()
    
    # 验证调用了 Project 模型查询
    mock_db.query.assert_called_once()
    # 验证应用了 filter（虽然无法直接验证 filter 条件）
    mock_query.filter.assert_called_once()


def test_get_scoped_query_applies_data_scope(service, mock_db, mock_user):
    """测试 get_scoped_query 应用数据权限过滤"""
    mock_query = MagicMock()
    mock_db.query.return_value.filter.return_value = mock_query
    
    with patch("app.services.project.core_service.DataScopeService") as MockScope:
        filtered_query = MagicMock()
        MockScope.filter_projects_by_scope.return_value = filtered_query
        
        result = service.get_scoped_query(mock_user)
        
        # 验证调用了 DataScopeService 过滤
        MockScope.filter_projects_by_scope.assert_called_once_with(
            mock_db, mock_query, mock_user
        )
        assert result is filtered_query


def test_paginate_returns_correct_counts():
    """测试 _paginate 返回正确的总数、页数和项目列表"""
    mock_query = MagicMock()
    mock_query.count.return_value = 45  # 总共45条记录
    
    with patch("app.services.project.core_service.get_pagination_params") as mock_paging, \
         patch("app.services.project.core_service.apply_pagination") as mock_apply:
        # 设置分页参数
        pagination = MagicMock()
        pagination.offset = 20
        pagination.limit = 20
        pagination.pages_for_total.return_value = 3  # 45条/20 = 3页
        mock_paging.return_value = pagination
        
        # 模拟返回的项目列表
        mock_projects = [MagicMock(), MagicMock()]
        mock_apply.return_value.all.return_value = mock_projects
        
        total, pages, items = ProjectCoreService._paginate(mock_query, page=2, page_size=20)
        
        assert total == 45
        assert pages == 3
        assert items == mock_projects
        mock_paging.assert_called_once_with(page=2, page_size=20)


def test_paginate_empty_results():
    """测试 _paginate 处理空结果的情况"""
    mock_query = MagicMock()
    mock_query.count.return_value = 0
    
    with patch("app.services.project.core_service.get_pagination_params") as mock_paging, \
         patch("app.services.project.core_service.apply_pagination") as mock_apply:
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 20
        pagination.pages_for_total.return_value = 0
        mock_paging.return_value = pagination
        mock_apply.return_value.all.return_value = []
        
        total, pages, items = ProjectCoreService._paginate(mock_query, page=1, page_size=20)
        
        assert total == 0
        assert pages == 0
        assert items == []


# ===================================================================
# 3. 我的项目 - list_user_projects (5个)
# ===================================================================
def test_list_user_projects_no_projects(service, mock_db, mock_user):
    """测试用户没有项目时返回空列表"""
    service._collect_user_project_ids = MagicMock(return_value=[])
    
    result = service.list_user_projects(mock_user, page=1, page_size=20)
    
    assert isinstance(result, MyProjectListResponse)
    assert result.total == 0
    assert result.page == 1
    assert result.page_size == 20
    assert result.pages == 0
    assert result.items == []


def test_list_user_projects_with_single_project(service, mock_db, mock_user, mock_project):
    """测试用户有单个项目时正确返回"""
    service._collect_user_project_ids = MagicMock(return_value=[100])
    service._load_memberships = MagicMock(return_value={})
    service._build_task_stats = MagicMock(return_value={})
    service._get_customer_name = MagicMock(return_value="Test Customer")
    
    with patch("app.services.project.core_service.get_pagination_params") as mock_paging, \
         patch("app.services.project.core_service.apply_pagination") as mock_apply:
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 20
        pagination.pages_for_total.return_value = 1
        mock_paging.return_value = pagination
        
        # 模拟查询返回
        mock_db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 1
        mock_apply.return_value.all.return_value = [mock_project]
        
        result = service.list_user_projects(mock_user, page=1, page_size=20)
        
        assert result.total == 1
        assert result.pages == 1
        assert len(result.items) == 1


def test_list_user_projects_with_member_roles(service, mock_db, mock_user, mock_project):
    """测试用户作为成员时正确加载角色信息"""
    service._collect_user_project_ids = MagicMock(return_value=[100])
    # 模拟成员信息：用户是开发者，分配率80%
    service._load_memberships = MagicMock(return_value={
        100: {"roles": ["DEV"], "allocations": [80.0]}
    })
    service._build_task_stats = MagicMock(return_value={})
    service._get_customer_name = MagicMock(return_value="Test Customer")
    
    with patch("app.services.project.core_service.get_pagination_params") as mock_paging, \
         patch("app.services.project.core_service.apply_pagination") as mock_apply:
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 20
        pagination.pages_for_total.return_value = 1
        mock_paging.return_value = pagination
        
        mock_project.pm_id = 99  # 不是PM
        mock_db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 1
        mock_apply.return_value.all.return_value = [mock_project]
        
        result = service.list_user_projects(mock_user, page=1, page_size=20)
        
        assert len(result.items) == 1
        item = result.items[0]
        assert "DEV" in item.my_roles
        assert item.my_allocation_pct == 80


def test_list_user_projects_as_pm_without_member(service, mock_db, mock_user, mock_project):
    """测试用户是PM但不是成员时，自动添加PM角色"""
    service._collect_user_project_ids = MagicMock(return_value=[100])
    service._load_memberships = MagicMock(return_value={})  # 没有成员记录
    service._build_task_stats = MagicMock(return_value={})
    service._get_customer_name = MagicMock(return_value="Test Customer")
    
    with patch("app.services.project.core_service.get_pagination_params") as mock_paging, \
         patch("app.services.project.core_service.apply_pagination") as mock_apply:
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 20
        pagination.pages_for_total.return_value = 1
        mock_paging.return_value = pagination
        
        mock_project.pm_id = 1  # 用户是PM
        mock_db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 1
        mock_apply.return_value.all.return_value = [mock_project]
        
        result = service.list_user_projects(mock_user, page=1, page_size=20)
        
        assert len(result.items) == 1
        assert "PM" in result.items[0].my_roles


def test_list_user_projects_with_task_stats(service, mock_db, mock_user, mock_project):
    """测试正确加载任务统计信息"""
    service._collect_user_project_ids = MagicMock(return_value=[100])
    service._load_memberships = MagicMock(return_value={})
    
    # 模拟任务统计
    task_stats = TaskStatsResponse(
        total_tasks=10,
        pending_tasks=2,
        in_progress_tasks=5,
        completed_tasks=3,
        overdue_tasks=1,
        delayed_tasks=0,
        pending_approval_tasks=0
    )
    service._build_task_stats = MagicMock(return_value={100: task_stats})
    service._get_customer_name = MagicMock(return_value="Test Customer")
    
    with patch("app.services.project.core_service.get_pagination_params") as mock_paging, \
         patch("app.services.project.core_service.apply_pagination") as mock_apply:
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 20
        pagination.pages_for_total.return_value = 1
        mock_paging.return_value = pagination
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 1
        mock_apply.return_value.all.return_value = [mock_project]
        
        result = service.list_user_projects(mock_user, page=1, page_size=20)
        
        assert len(result.items) == 1
        stats = result.items[0].task_stats
        assert stats.total_tasks == 10
        assert stats.pending_tasks == 2


# ===================================================================
# 4. 我的项目 - 辅助方法 (4个)
# ===================================================================
def test_collect_user_project_ids_member_only(service, mock_db, mock_user):
    """测试收集用户作为成员的项目ID"""
    # 模拟成员查询返回
    mock_db.query.return_value.filter.return_value.all.side_effect = [
        [(100,), (101,)],  # 成员项目
        []  # 没有拥有的项目
    ]
    
    result = service._collect_user_project_ids(mock_user)
    
    assert result == [100, 101]


def test_collect_user_project_ids_owner_only(service, mock_db, mock_user):
    """测试收集用户作为创建者/PM的项目ID"""
    mock_db.query.return_value.filter.return_value.all.side_effect = [
        [],  # 没有成员项目
        [(200,), (201,)]  # 拥有的项目
    ]
    
    result = service._collect_user_project_ids(mock_user)
    
    assert result == [200, 201]


def test_collect_user_project_ids_mixed_and_deduped(service, mock_db, mock_user):
    """测试收集并去重混合项目ID"""
    mock_db.query.return_value.filter.return_value.all.side_effect = [
        [(100,), (101,)],  # 成员项目
        [(101,), (102,)]  # 拥有的项目（101重复）
    ]
    
    result = service._collect_user_project_ids(mock_user)
    
    # 应去重并排序
    assert result == [100, 101, 102]


def test_load_memberships_empty_project_ids(service, mock_db):
    """测试空项目ID列表时返回空字典"""
    result = service._load_memberships(user_id=1, project_ids=[])
    assert result == {}


def test_load_memberships_with_multiple_roles(service, mock_db):
    """测试加载用户在多个项目中的角色和分配率"""
    # 模拟成员记录
    member1 = MagicMock()
    member1.project_id = 100
    member1.role_code = "DEV"
    member1.allocation_pct = 60.0
    
    member2 = MagicMock()
    member2.project_id = 100
    member2.role_code = "TESTER"
    member2.allocation_pct = 40.0
    
    member3 = MagicMock()
    member3.project_id = 101
    member3.role_code = "PM"
    member3.allocation_pct = 100.0
    
    mock_db.query.return_value.filter.return_value.all.return_value = [member1, member2, member3]
    
    result = service._load_memberships(user_id=1, project_ids=[100, 101])
    
    assert 100 in result
    assert result[100]["roles"] == ["DEV", "TESTER"]
    assert result[100]["allocations"] == [60.0, 40.0]
    
    assert 101 in result
    assert result[101]["roles"] == ["PM"]
    assert result[101]["allocations"] == [100.0]


def test_build_task_stats_empty_project_ids(service, mock_db):
    """测试空项目ID列表时返回空字典"""
    result = service._build_task_stats(user_id=1, project_ids=[])
    assert result == {}


def test_build_task_stats_various_statuses(service, mock_db):
    """测试构建包含各种状态任务的统计信息"""
    now = datetime.utcnow()
    
    # 创建不同状态的任务
    task1 = MagicMock()
    task1.project_id = 100
    task1.status = "PENDING"
    task1.deadline = None
    task1.is_delayed = False
    task1.approval_status = None
    
    task2 = MagicMock()
    task2.project_id = 100
    task2.status = "IN_PROGRESS"
    task2.deadline = now + timedelta(days=5)
    task2.is_delayed = False
    task2.approval_status = None
    
    task3 = MagicMock()
    task3.project_id = 100
    task3.status = "COMPLETED"
    task3.deadline = None
    task3.is_delayed = False
    task3.approval_status = None
    
    task4 = MagicMock()
    task4.project_id = 100
    task4.status = "IN_PROGRESS"
    task4.deadline = now - timedelta(days=2)  # 逾期
    task4.is_delayed = True
    task4.approval_status = None
    
    mock_db.query.return_value.filter.return_value.all.return_value = [task1, task2, task3, task4]
    
    result = service._build_task_stats(user_id=1, project_ids=[100])
    
    assert 100 in result
    stats = result[100]
    assert stats.total_tasks == 4
    assert stats.pending_tasks == 1
    assert stats.in_progress_tasks == 2
    assert stats.completed_tasks == 1
    assert stats.overdue_tasks == 1
    assert stats.delayed_tasks == 1


# ===================================================================
# 5. 部门项目 (2个)
# ===================================================================
def test_list_department_projects_success(service, mock_db, mock_user, mock_project):
    """测试成功列出部门项目"""
    with patch("app.services.project.core_service.DataScopeService") as MockScope, \
         patch("app.services.project.core_service.get_pagination_params") as mock_paging, \
         patch("app.services.project.core_service.apply_pagination") as mock_apply:
        
        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        MockScope.filter_projects_by_scope.return_value.order_by.return_value = mock_query
        
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 20
        pagination.pages_for_total.return_value = 1
        mock_paging.return_value = pagination
        
        mock_query.count.return_value = 1
        mock_apply.return_value.all.return_value = [mock_project]
        
        result = service.list_department_projects(dept_id=5, current_user=mock_user, page=1, page_size=20)
        
        assert isinstance(result, PaginatedResponse)
        assert result.total == 1
        assert len(result.items) == 1


def test_list_department_projects_empty(service, mock_db, mock_user):
    """测试部门无项目时返回空列表"""
    with patch("app.services.project.core_service.DataScopeService") as MockScope, \
         patch("app.services.project.core_service.get_pagination_params") as mock_paging, \
         patch("app.services.project.core_service.apply_pagination") as mock_apply:
        
        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        MockScope.filter_projects_by_scope.return_value.order_by.return_value = mock_query
        
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 20
        pagination.pages_for_total.return_value = 0
        mock_paging.return_value = pagination
        
        mock_query.count.return_value = 0
        mock_apply.return_value.all.return_value = []
        
        result = service.list_department_projects(dept_id=5, current_user=mock_user)
        
        assert result.total == 0
        assert result.items == []


# ===================================================================
# 6. 工具方法 (4个)
# ===================================================================
def test_get_customer_name_from_project_field():
    """测试从项目字段获取客户名称"""
    project = MagicMock()
    project.customer_name = "Direct Customer Name"
    
    result = ProjectCoreService._get_customer_name(project)
    
    assert result == "Direct Customer Name"


def test_get_customer_name_from_relation():
    """测试从关联对象获取客户名称"""
    project = MagicMock()
    project.customer_name = None
    project.customer = MagicMock()
    project.customer.customer_name = "Related Customer Name"
    
    result = ProjectCoreService._get_customer_name(project)
    
    assert result == "Related Customer Name"


def test_get_customer_name_none():
    """测试无客户名称时返回 None"""
    project = MagicMock()
    project.customer_name = None
    project.customer = None
    
    result = ProjectCoreService._get_customer_name(project)
    
    assert result is None


def test_to_project_list_response_complete(mock_project):
    """测试转换完整项目信息为响应对象"""
    mock_project.customer = None  # 使用直接字段
    mock_project.manager = None  # 使用直接字段
    mock_project.salesperson_id = 20
    mock_project.te_id = 30
    
    result = ProjectCoreService._to_project_list_response(mock_project)
    
    assert isinstance(result, ProjectListResponse)
    assert result.id == 100
    assert result.project_code == "PRJ001"
    assert result.project_name == "Test Project"
    assert result.customer_name == "Test Customer"
    assert result.stage == "S2"
    assert result.health == "H2"
    assert result.progress_pct == 50.0
    assert result.pm_name == "Project Manager"
    assert result.pm_id == 10
    assert result.sales_id == 20
    assert result.te_id == 30


def test_to_project_list_response_with_relations(mock_project):
    """测试使用关联对象字段转换项目信息"""
    mock_project.customer_name = None
    mock_project.customer = MagicMock()
    mock_project.customer.customer_name = "Related Customer"
    
    mock_project.pm_name = None
    mock_project.manager = MagicMock()
    mock_project.manager.real_name = "Manager Name"
    mock_project.manager.username = "manager_user"
    
    result = ProjectCoreService._to_project_list_response(mock_project)
    
    assert result.customer_name == "Related Customer"
    assert result.pm_name == "Manager Name"


def test_get_department_found(service, mock_db):
    """测试成功获取部门对象"""
    mock_dept = MagicMock()
    mock_dept.id = 5
    mock_dept.dept_name = "Test Department"
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_dept
    
    result = service.get_department(dept_id=5)
    
    assert result is mock_dept


def test_get_department_not_found(service, mock_db):
    """测试部门不存在时返回 None"""
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    result = service.get_department(dept_id=999)
    
    assert result is None
