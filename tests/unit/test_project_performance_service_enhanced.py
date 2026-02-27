# -*- coding: utf-8 -*-
"""
ProjectPerformanceService 完整测试套件
目标覆盖率: 60%+
测试数量: 30-40个

测试重点:
- 绩效指标计算
- 绩效评估
- 绩效跟踪
- 绩效报告
- 异常处理
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.performance import (
    PerformancePeriod,
    PerformanceResult,
    ProjectContribution,
)
from app.models.progress import Task
from app.models.project import Project
from app.models.user import User
from app.services.project_performance.service import ProjectPerformanceService


# ==================== Fixtures ====================


@pytest.fixture
def perf_service(db_session: Session):
    """创建绩效服务实例"""
    return ProjectPerformanceService()


@pytest.fixture
def test_department(db_session: Session):
    """创建测试部门"""
    dept = Department(
        dept_name="研发部",
        dept_code="RD001",
        manager_id=None,
        is_active=True,
    )
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


@pytest.fixture
def test_department_2(db_session: Session):
    """创建第二个测试部门"""
    dept = Department(
        dept_name="销售部",
        dept_code="SALES001",
        manager_id=None,
        is_active=True,
    )
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


@pytest.fixture
def regular_user(db_session: Session, test_department):
    """创建普通用户"""
    from app.core.security import get_password_hash
    
    user = User(
        username="regular_user",
        password_hash=get_password_hash("test123"),
        real_name="普通用户",
        department_id=test_department.id,
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def superuser(db_session: Session, test_department):
    """创建超级管理员"""
    from app.core.security import get_password_hash
    
    user = User(
        username="admin_user",
        password_hash=get_password_hash("admin123"),
        real_name="管理员",
        department_id=test_department.id,
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def dept_manager(db_session: Session, test_department):
    """创建部门经理"""
    from app.core.security import get_password_hash
    from app.models.user import Role, UserRole
    
    user = User(
        username="dept_manager",
        password_hash=get_password_hash("manager123"),
        real_name="部门经理",
        department_id=test_department.id,
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.flush()
    
    # 创建部门经理角色
    role = Role(
        role_code="dept_manager",
        role_name="部门经理",
        description="部门经理角色",
    )
    db_session.add(role)
    db_session.flush()
    
    # 关联用户和角色
    user_role = UserRole(
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(user_role)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def project_manager(db_session: Session, test_department):
    """创建项目经理"""
    from app.core.security import get_password_hash
    from app.models.user import Role, UserRole
    
    user = User(
        username="pm_user",
        password_hash=get_password_hash("pm123"),
        real_name="项目经理",
        department_id=test_department.id,
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.flush()
    
    # 创建项目经理角色
    role = Role(
        role_code="pm",
        role_name="项目经理",
        description="项目经理角色",
    )
    db_session.add(role)
    db_session.flush()
    
    # 关联用户和角色
    user_role = UserRole(
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(user_role)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_project(db_session: Session, project_manager):
    """创建测试项目"""
    from app.models.project import Customer
    
    customer = Customer(
        customer_code="CUST-PERF-001",
        customer_name="绩效测试客户",
        contact_person="张三",
        contact_phone="13800000000",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()
    
    project = Project(
        project_code="PROJ-PERF-001",
        project_name="绩效测试项目",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        pm_id=project_manager.id,
        stage="S2",
        status="ST02",
        health="H1",
        progress_pct=50,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_period(db_session: Session):
    """创建测试绩效周期"""
    period = PerformancePeriod(
        period_name="2024年第一季度",
        period_type="QUARTERLY",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        status="FINALIZED",
        period_code="PP-TEST-001"
    )
    db_session.add(period)
    db_session.commit()
    db_session.refresh(period)
    return period


@pytest.fixture
def test_period_active(db_session: Session):
    """创建活跃的绩效周期"""
    period = PerformancePeriod(
        period_name="2024年第二季度",
        period_type="QUARTERLY",
        start_date=date(2024, 4, 1),
        end_date=date(2024, 6, 30),
        status="ACTIVE",
        period_code="PP-TEST-001"
    )
    db_session.add(period)
    db_session.commit()
    db_session.refresh(period)
    return period


# ==================== 权限检查测试 ====================


class TestCheckPermission:
    """测试权限检查功能"""
    
    def test_superuser_can_view_all(self, perf_service, superuser, regular_user):
        """测试超级管理员可以查看所有用户的绩效"""
        result = perf_service.check_performance_view_permission(
            superuser, regular_user.id
        )
        assert result is True
    
    def test_user_can_view_own_performance(self, perf_service, regular_user):
        """测试用户可以查看自己的绩效"""
        result = perf_service.check_performance_view_permission(
            regular_user, regular_user.id
        )
        assert result is True
    
    def test_dept_manager_can_view_dept_member(
        self, perf_service, dept_manager, regular_user, test_department
    ):
        """测试部门经理可以查看本部门成员的绩效"""
        result = perf_service.check_performance_view_permission(
            dept_manager, regular_user.id
        )
        assert result is True
    
    def test_dept_manager_cannot_view_other_dept(
        self, perf_service, dept_manager, test_department_2, db_session
    ):
        """测试部门经理不能查看其他部门成员的绩效"""
        from app.core.security import get_password_hash
        
        other_user = User(
            username="other_user",
            password_hash=get_password_hash("test123"),
            real_name="其他部门用户",
            department_id=test_department_2.id,
            is_active=True,
            is_superuser=False,
        )
        db_session.add(other_user)
        db_session.commit()
        
        result = perf_service.check_performance_view_permission(
            dept_manager, other_user.id
        )
        assert result is False
    
    def test_project_manager_can_view_team_member(
        self, perf_service, project_manager, test_project, regular_user, db_session
    ):
        """测试项目经理可以查看项目成员的绩效"""
        # 创建任务，将regular_user作为项目成员
        task = Task(
            project_id=test_project.id,
            task_name="测试任务",
            owner_id=regular_user.id,
            status="IN_PROGRESS",
        )
        db_session.add(task)
        db_session.commit()
        
        result = perf_service.check_performance_view_permission(
            project_manager, regular_user.id
        )
        assert result is True
    
    def test_regular_user_cannot_view_others(
        self, perf_service, regular_user, db_session, test_department
    ):
        """测试普通用户不能查看其他用户的绩效"""
        from app.core.security import get_password_hash
        
        other_user = User(
            username="another_user",
            password_hash=get_password_hash("test123"),
            real_name="另一个用户",
            department_id=test_department.id,
            is_active=True,
            is_superuser=False,
        )
        db_session.add(other_user)
        db_session.commit()
        
        result = perf_service.check_performance_view_permission(
            regular_user, other_user.id
        )
        assert result is False
    
    def test_permission_check_with_nonexistent_user(
        self, perf_service, regular_user
    ):
        """测试查看不存在用户的权限"""
        result = perf_service.check_performance_view_permission(
            regular_user, 99999
        )
        assert result is False
    
    def test_permission_check_without_roles(
        self, perf_service, db_session, test_department
    ):
        """测试没有角色的用户权限检查"""
        from app.core.security import get_password_hash
        
        user1 = User(
            username="user1",
            password_hash=get_password_hash("test123"),
            real_name="用户1",
            department_id=test_department.id,
            is_active=True,
            is_superuser=False,
        )
        user2 = User(
            username="user2",
            password_hash=get_password_hash("test123"),
            real_name="用户2",
            department_id=test_department.id,
            is_active=True,
            is_superuser=False,
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        
        result = perf_service.check_performance_view_permission(user1, user2.id)
        assert result is False


# ==================== 团队和部门成员测试 ====================


class TestTeamAndDepartment:
    """测试团队和部门成员获取"""
    
    def test_get_team_members(
        self, perf_service, test_department, regular_user, db_session
    ):
        """测试获取团队成员列表"""
        from app.core.security import get_password_hash
        
        # 创建更多部门成员
        user2 = User(
            username="user2",
            password_hash=get_password_hash("test123"),
            real_name="用户2",
            department_id=test_department.id,
            is_active=True,
        )
        user3 = User(
            username="user3",
            password_hash=get_password_hash("test123"),
            real_name="用户3",
            department_id=test_department.id,
            is_active=True,
        )
        db_session.add_all([user2, user3])
        db_session.commit()
        
        members = perf_service.get_team_members(test_department.id)
        assert len(members) >= 3
        assert regular_user.id in members
        assert user2.id in members
        assert user3.id in members
    
    def test_get_team_members_empty_team(self, perf_service, db_session):
        """测试获取空团队的成员列表"""
        dept = Department(
            dept_name="空部门",
            dept_code="EMPTY001",
            is_active=True,
        )
        db_session.add(dept)
        db_session.commit()
        
        members = perf_service.get_team_members(dept.id)
        assert members == []
    
    def test_get_department_members(
        self, perf_service, test_department, regular_user
    ):
        """测试获取部门成员列表"""
        members = perf_service.get_department_members(test_department.id)
        assert len(members) >= 1
        assert regular_user.id in members
    
    def test_get_department_members_excludes_inactive(
        self, perf_service, test_department, db_session
    ):
        """测试部门成员列表不包含非活跃用户"""
        from app.core.security import get_password_hash
        
        inactive_user = User(
            username="inactive_user",
            password_hash=get_password_hash("test123"),
            real_name="非活跃用户",
            department_id=test_department.id,
            is_active=False,
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        members = perf_service.get_department_members(test_department.id)
        assert inactive_user.id not in members


# ==================== 评价人类型测试 ====================


class TestEvaluatorType:
    """测试评价人类型判断"""
    
    def test_dept_manager_type(self, perf_service, dept_manager):
        """测试部门经理类型识别"""
        evaluator_type = perf_service.get_evaluator_type(dept_manager)
        assert evaluator_type == "DEPT_MANAGER"
    
    def test_project_manager_type(self, perf_service, project_manager):
        """测试项目经理类型识别"""
        evaluator_type = perf_service.get_evaluator_type(project_manager)
        assert evaluator_type == "PROJECT_MANAGER"
    
    def test_both_manager_type(self, perf_service, db_session, test_department):
        """测试同时是部门经理和项目经理的用户"""
        from app.core.security import get_password_hash
        from app.models.user import Role, UserRole
        
        user = User(
            username="both_manager",
            password_hash=get_password_hash("test123"),
            real_name="双重经理",
            department_id=test_department.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()
        
        # 添加部门经理角色
        dept_role = Role(
            role_code="dept_manager",
            role_name="部门经理",
        )
        db_session.add(dept_role)
        db_session.flush()
        
        # 添加项目经理角色
        pm_role = Role(
            role_code="pm",
            role_name="项目经理",
        )
        db_session.add(pm_role)
        db_session.flush()
        
        db_session.add_all([
            UserRole(user_id=user.id, role_id=dept_role.id),
            UserRole(user_id=user.id, role_id=pm_role.id),
        ])
        db_session.commit()
        db_session.refresh(user)
        
        evaluator_type = perf_service.get_evaluator_type(user)
        assert evaluator_type == "BOTH"
    
    def test_regular_user_type(self, perf_service, regular_user):
        """测试普通用户类型识别"""
        evaluator_type = perf_service.get_evaluator_type(regular_user)
        assert evaluator_type == "OTHER"
    
    def test_evaluator_type_with_chinese_role(
        self, perf_service, db_session, test_department
    ):
        """测试中文角色名称的识别"""
        from app.core.security import get_password_hash
        from app.models.user import Role, UserRole
        
        user = User(
            username="chinese_role_user",
            password_hash=get_password_hash("test123"),
            real_name="中文角色用户",
            department_id=test_department.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()
        
        role = Role(
            role_code="manager",
            role_name="部门经理",  # 中文角色名
        )
        db_session.add(role)
        db_session.flush()
        
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(user_role)
        db_session.commit()
        db_session.refresh(user)
        
        evaluator_type = perf_service.get_evaluator_type(user)
        assert evaluator_type == "DEPT_MANAGER"


# ==================== 名称获取测试 ====================


class TestGetNames:
    """测试团队和部门名称获取"""
    
    def test_get_team_name(self, perf_service, test_department):
        """测试获取团队名称"""
        name = perf_service.get_team_name(test_department.id)
        assert name == "研发部"
    
    def test_get_team_name_nonexistent(self, perf_service):
        """测试获取不存在团队的名称"""
        name = perf_service.get_team_name(99999)
        assert name == "团队99999"
    
    def test_get_department_name(self, perf_service, test_department):
        """测试获取部门名称"""
        name = perf_service.get_department_name(test_department.id)
        assert name == "研发部"
    
    def test_get_department_name_nonexistent(self, perf_service):
        """测试获取不存在部门的名称"""
        name = perf_service.get_department_name(99999)
        assert name == "部门99999"


# ==================== 项目绩效测试 ====================


class TestProjectPerformance:
    """测试项目绩效获取"""
    
    def test_get_project_performance_success(
        self, perf_service, test_project, test_period, regular_user, db_session
    ):
        """测试成功获取项目绩效"""
        # 创建项目贡献记录
        contribution = ProjectContribution(
            period_id=test_period.id,
            project_id=test_project.id,
            user_id=regular_user.id,
            contribution_score=Decimal("85.5"),
            hours_spent=Decimal("160"),
            task_count=10,
        )
        db_session.add(contribution)
        db_session.commit()
        
        result = perf_service.get_project_performance(test_project.id, test_period.id)
        
        assert result["project_id"] == test_project.id
        assert result["project_name"] == test_project.project_name
        assert result["period_id"] == test_period.id
        assert result["member_count"] == 1
        assert len(result["members"]) == 1
        assert result["members"][0]["user_id"] == regular_user.id
        assert result["members"][0]["contribution_score"] == 85.5
        assert result["members"][0]["work_hours"] == 160.0
        assert result["members"][0]["task_count"] == 10
    
    def test_get_project_performance_nonexistent_project(
        self, perf_service, test_period
    ):
        """测试获取不存在项目的绩效"""
        with pytest.raises(ValueError, match="项目不存在"):
            perf_service.get_project_performance(99999, test_period.id)
    
    def test_get_project_performance_no_period(
        self, perf_service, test_project, db_session
    ):
        """测试没有周期时获取绩效"""
        # 删除所有finalized周期
        db_session.query(PerformancePeriod).delete()
        db_session.commit()
        
        with pytest.raises(ValueError, match="未找到考核周期"):
            perf_service.get_project_performance(test_project.id)
    
    def test_get_project_performance_multiple_members(
        self, perf_service, test_project, test_period, regular_user, db_session
    ):
        """测试多成员项目绩效"""
        from app.core.security import get_password_hash
        
        # 创建第二个用户
        user2 = User(
            username="user2",
            password_hash=get_password_hash("test123"),
            real_name="用户2",
            is_active=True,
        )
        db_session.add(user2)
        db_session.flush()
        
        # 创建两个贡献记录
        contrib1 = ProjectContribution(
            period_id=test_period.id,
            project_id=test_project.id,
            user_id=regular_user.id,
            contribution_score=Decimal("90"),
            hours_spent=Decimal("100"),
            task_count=5,
        )
        contrib2 = ProjectContribution(
            period_id=test_period.id,
            project_id=test_project.id,
            user_id=user2.id,
            contribution_score=Decimal("75"),
            hours_spent=Decimal("80"),
            task_count=4,
        )
        db_session.add_all([contrib1, contrib2])
        db_session.commit()
        
        result = perf_service.get_project_performance(test_project.id, test_period.id)
        
        assert result["member_count"] == 2
        # 验证按贡献分降序排列
        assert result["members"][0]["contribution_score"] == 90.0
        assert result["members"][1]["contribution_score"] == 75.0
    
    def test_get_project_performance_default_period(
        self, perf_service, test_project, test_period, regular_user, db_session
    ):
        """测试使用默认周期获取绩效"""
        contribution = ProjectContribution(
            period_id=test_period.id,
            project_id=test_project.id,
            user_id=regular_user.id,
            contribution_score=Decimal("80"),
            hours_spent=Decimal("120"),
            task_count=8,
        )
        db_session.add(contribution)
        db_session.commit()
        
        result = perf_service.get_project_performance(test_project.id)
        
        assert result["period_id"] == test_period.id
        assert result["member_count"] == 1


# ==================== 项目进展报告测试 ====================


class TestProjectProgressReport:
    """测试项目进展报告"""
    
    def test_get_progress_report_success(
        self, perf_service, test_project, regular_user, db_session
    ):
        """测试成功获取项目进展报告"""
        # 创建任务
        task1 = Task(
            project_id=test_project.id,
            task_name="已完成任务",
            owner_id=regular_user.id,
            status="DONE",
        )
        task2 = Task(
            project_id=test_project.id,
            task_name="进行中任务",
            owner_id=regular_user.id,
            status="IN_PROGRESS",
        )
        db_session.add_all([task1, task2])
        db_session.commit()
        
        result = perf_service.get_project_progress_report(test_project.id)
        
        assert result["project_id"] == test_project.id
        assert result["project_name"] == test_project.project_name
        assert result["report_type"] == "WEEKLY"
        assert "progress_summary" in result
        assert result["progress_summary"]["total_tasks"] == 2
        assert result["progress_summary"]["completed_tasks"] == 1
    
    def test_get_progress_report_nonexistent_project(self, perf_service):
        """测试获取不存在项目的进展报告"""
        with pytest.raises(ValueError, match="项目不存在"):
            perf_service.get_project_progress_report(99999)
    
    def test_get_progress_report_delayed_tasks(
        self, perf_service, test_project, regular_user, db_session
    ):
        """测试包含逾期任务的进展报告"""
        # 创建逾期任务
        delayed_task = Task(
            project_id=test_project.id,
            task_name="逾期任务",
            owner_id=regular_user.id,
            status="IN_PROGRESS",
            plan_end=date.today() - timedelta(days=10),
        )
        db_session.add(delayed_task)
        db_session.commit()
        
        result = perf_service.get_project_progress_report(test_project.id)
        
        assert result["progress_summary"]["on_schedule"] is False
        assert len(result["risks_and_issues"]) > 0
        assert result["risks_and_issues"][0]["type"] == "DELAYED_TASK"
        assert result["risks_and_issues"][0]["severity"] == "HIGH"
    
    def test_get_progress_report_member_contributions(
        self, perf_service, test_project, regular_user, db_session
    ):
        """测试成员贡献统计"""
        from app.core.security import get_password_hash
        
        user2 = User(
            username="user2_contrib",
            password_hash=get_password_hash("test123"),
            real_name="用户2",
            is_active=True,
        )
        db_session.add(user2)
        db_session.flush()
        
        # 创建不同成员的任务
        for i in range(3):
            task = Task(
                project_id=test_project.id,
                task_name=f"任务{i}",
                owner_id=regular_user.id,
                status="IN_PROGRESS",
            )
            db_session.add(task)
        
        task = Task(
            project_id=test_project.id,
            task_name="用户2任务",
            owner_id=user2.id,
            status="IN_PROGRESS",
        )
        db_session.add(task)
        db_session.commit()
        
        result = perf_service.get_project_progress_report(test_project.id)
        
        assert len(result["member_contributions"]) == 2
        # 验证按任务数降序
        assert result["member_contributions"][0]["task_count"] == 3
        assert result["member_contributions"][1]["task_count"] == 1
    
    def test_get_progress_report_key_achievements(
        self, perf_service, test_project, regular_user, db_session
    ):
        """测试关键成果列表"""
        # 创建多个已完成任务
        for i in range(7):
            task = Task(
                project_id=test_project.id,
                task_name=f"已完成任务{i}",
                owner_id=regular_user.id,
                status="DONE",
                description=f"任务{i}的详细描述",
            )
            db_session.add(task)
        db_session.commit()
        
        result = perf_service.get_project_progress_report(test_project.id)
        
        # 最多返回5个关键成果
        assert len(result["key_achievements"]) <= 5
    
    def test_get_progress_report_monthly(
        self, perf_service, test_project
    ):
        """测试月报类型"""
        result = perf_service.get_project_progress_report(
            test_project.id, report_type="MONTHLY"
        )
        assert result["report_type"] == "MONTHLY"
    
    def test_get_progress_report_custom_date(
        self, perf_service, test_project
    ):
        """测试自定义报告日期"""
        custom_date = date(2024, 6, 15)
        result = perf_service.get_project_progress_report(
            test_project.id, report_date=custom_date
        )
        assert result["report_date"] == custom_date


# ==================== 绩效对比测试 ====================


class TestComparePerformance:
    """测试绩效对比功能"""
    
    def test_compare_performance_success(
        self, perf_service, test_period, regular_user, db_session
    ):
        """测试成功对比绩效"""
        from app.core.security import get_password_hash
        
        # 创建第二个用户
        user2 = User(
            username="user2_compare",
            password_hash=get_password_hash("test123"),
            real_name="用户2",
            is_active=True,
        )
        db_session.add(user2)
        db_session.flush()
        
        # 创建绩效结果
        result1 = PerformanceResult(
            period_id=test_period.id,
            user_id=regular_user.id,
            total_score=Decimal("85"),
            level="EXCELLENT",
            department_name="研发部",
        )
        result2 = PerformanceResult(
            period_id=test_period.id,
            user_id=user2.id,
            total_score=Decimal("75"),
            level="QUALIFIED",
            department_name="测试部",
        )
        db_session.add_all([result1, result2])
        db_session.commit()
        
        comparison = perf_service.compare_performance(
            [regular_user.id, user2.id], test_period.id
        )
        
        assert comparison["period_id"] == test_period.id
        assert len(comparison["comparison_data"]) == 2
        assert comparison["comparison_data"][0]["score"] == 85.0
        assert comparison["comparison_data"][1]["score"] == 75.0
    
    def test_compare_performance_no_period(self, perf_service, db_session):
        """测试没有周期时对比绩效"""
        db_session.query(PerformancePeriod).delete()
        db_session.commit()
        
        with pytest.raises(ValueError, match="未找到考核周期"):
            perf_service.compare_performance([1, 2])
    
    def test_compare_performance_default_period(
        self, perf_service, test_period, regular_user, db_session
    ):
        """测试使用默认周期对比绩效"""
        result = PerformanceResult(
            period_id=test_period.id,
            user_id=regular_user.id,
            total_score=Decimal("80"),
            level="QUALIFIED",
        )
        db_session.add(result)
        db_session.commit()
        
        comparison = perf_service.compare_performance([regular_user.id])
        
        assert comparison["period_id"] == test_period.id
    
    def test_compare_performance_missing_user(
        self, perf_service, test_period, regular_user, db_session
    ):
        """测试对比时包含不存在的用户"""
        result = PerformanceResult(
            period_id=test_period.id,
            user_id=regular_user.id,
            total_score=Decimal("80"),
            level="QUALIFIED",
        )
        db_session.add(result)
        db_session.commit()
        
        # 包含一个不存在的用户ID
        comparison = perf_service.compare_performance(
            [regular_user.id, 99999], test_period.id
        )
        
        # 应该只返回存在的用户
        assert len(comparison["comparison_data"]) == 1
    
    def test_compare_performance_no_results(
        self, perf_service, test_period, regular_user
    ):
        """测试对比没有绩效结果的用户"""
        comparison = perf_service.compare_performance(
            [regular_user.id], test_period.id
        )
        
        assert len(comparison["comparison_data"]) == 1
        assert comparison["comparison_data"][0]["score"] == 0
        assert comparison["comparison_data"][0]["level"] == "QUALIFIED"
    
    def test_compare_performance_multiple_periods(
        self, perf_service, test_period, test_period_active, regular_user, db_session
    ):
        """测试在多个周期中对比绩效"""
        # 在两个周期都有结果
        result1 = PerformanceResult(
            period_id=test_period.id,
            user_id=regular_user.id,
            total_score=Decimal("80"),
            level="QUALIFIED",
        )
        result2 = PerformanceResult(
            period_id=test_period_active.id,
            user_id=regular_user.id,
            total_score=Decimal("90"),
            level="EXCELLENT",
        )
        db_session.add_all([result1, result2])
        db_session.commit()
        
        # 指定第一个周期
        comparison = perf_service.compare_performance(
            [regular_user.id], test_period.id
        )
        
        assert comparison["period_id"] == test_period.id
        assert comparison["comparison_data"][0]["score"] == 80.0


# ==================== 边界情况和异常测试 ====================


class TestEdgeCasesAndExceptions:
    """测试边界情况和异常处理"""
    
    def test_service_initialization(self, db_session):
        """测试服务初始化"""
        service = ProjectPerformanceService()
        assert service.db == db_session
    
    def test_empty_user_list_comparison(self, perf_service, test_period):
        """测试空用户列表的对比"""
        comparison = perf_service.compare_performance([], test_period.id)
        assert comparison["comparison_data"] == []
    
    def test_project_performance_zero_contribution(
        self, perf_service, test_project, test_period, regular_user, db_session
    ):
        """测试零贡献的项目绩效"""
        contribution = ProjectContribution(
            period_id=test_period.id,
            project_id=test_project.id,
            user_id=regular_user.id,
            contribution_score=Decimal("0"),
            hours_spent=Decimal("0"),
            task_count=0,
        )
        db_session.add(contribution)
        db_session.commit()
        
        result = perf_service.get_project_performance(test_project.id, test_period.id)
        
        assert result["members"][0]["contribution_score"] == 0.0
        assert result["members"][0]["work_hours"] == 0.0
        assert result["members"][0]["task_count"] == 0
    
    def test_progress_report_no_tasks(self, perf_service, test_project):
        """测试没有任务的项目进展报告"""
        result = perf_service.get_project_progress_report(test_project.id)
        
        assert result["progress_summary"]["total_tasks"] == 0
        assert result["progress_summary"]["completed_tasks"] == 0
        assert result["progress_summary"]["on_schedule"] is True
        assert result["member_contributions"] == []
        assert result["key_achievements"] == []
        assert result["risks_and_issues"] == []
