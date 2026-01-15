# -*- coding: utf-8 -*-
"""
绩效融合 - 自动生成
从 performance.py 拆分
"""

# -*- coding: utf-8 -*-
"""
绩效管理 API endpoints
核心功能：多层级绩效视图、绩效对比、趋势分析、排行榜
"""

from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func, case

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.models.organization import Department, Employee
from app.models.performance import (
    PerformancePeriod, PerformanceIndicator, PerformanceResult,
    PerformanceEvaluation, PerformanceAppeal, ProjectContribution,
    PerformanceRankingSnapshot,
    # New Performance System
    MonthlyWorkSummary, PerformanceEvaluationRecord, EvaluationWeightConfig
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.performance import (
    PersonalPerformanceResponse, PerformanceTrendResponse,
    TeamPerformanceResponse, DepartmentPerformanceResponse, PerformanceRankingResponse,
    ProjectPerformanceResponse, ProjectProgressReportResponse, PerformanceCompareResponse,
    # New Performance System
    MonthlyWorkSummaryCreate, MonthlyWorkSummaryUpdate, MonthlyWorkSummaryResponse,
    MonthlyWorkSummaryListItem, PerformanceEvaluationRecordCreate,
    PerformanceEvaluationRecordUpdate, PerformanceEvaluationRecordResponse,
    EvaluationTaskItem, EvaluationTaskListResponse, EvaluationDetailResponse,
    MyPerformanceResponse, EvaluationWeightConfigCreate, EvaluationWeightConfigResponse,
    EvaluationWeightConfigListResponse
)
from app.services.performance_service import PerformanceService
from app.services.performance_integration_service import PerformanceIntegrationService

router = APIRouter()


def _check_performance_view_permission(current_user: User, target_user_id: int, db: Session) -> bool:
    """
    检查用户是否有权限查看指定用户的绩效

    规则：
    1. 可以查看自己的绩效
    2. 部门经理可以查看本部门员工的绩效
    3. 项目经理可以查看项目成员的绩效
    4. 管理员可以查看所有人的绩效

    Returns:
        bool: 是否有权限查看
    """
    if current_user.is_superuser:
        return True

    # 查看自己的绩效
    if current_user.id == target_user_id:
        return True

    # 检查是否是部门经理
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        return False

    # 检查是否有管理角色
    manager_roles = ['dept_manager', 'department_manager', '部门经理',
                     'pm', 'project_manager', '项目经理',
                     'admin', 'super_admin', '管理员']

    has_manager_role = False
    for user_role in (current_user.roles or []):
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ''
        if role_code in manager_roles or role_name in manager_roles:
            has_manager_role = True
            break

    if not has_manager_role:
        return False

    # 检查是否是同一部门
    if target_user.department_id and current_user.department_id == target_user.department_id:
        return True

    # 检查是否管理同一项目
    from app.models.project import Project
    user_projects = db.query(Project).filter(Project.pm_id == current_user.id).all()
    project_ids = [p.id for p in user_projects]

    target_projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    for project in target_projects:
        # 检查目标用户是否是项目成员
        from app.models.progress import Task
        member_task = db.query(Task).filter(
            Task.project_id == project.id,
            Task.owner_id == target_user_id
        ).first()
        if member_task:
            return True

    return False


def _get_team_members(db: Session, team_id: int) -> List[int]:
    """
    获取团队成员ID列表

    Args:
        db: 数据库会话
        team_id: 团队ID（暂时使用department_id作为team_id）

    Returns:
        List[int]: 成员ID列表
    """
    # 临时使用部门作为团队
    from app.models.organization import Department
    users = db.query(User).filter(
        User.department_id == team_id,
        User.is_active == True
    ).all()
    return [u.id for u in users]


def _get_department_members(db: Session, dept_id: int) -> List[int]:
    """
    获取部门成员ID列表

    Args:
        db: 数据库会话
        dept_id: 部门ID

    Returns:
        List[int]: 成员ID列表
    """
    users = db.query(User).filter(
        User.department_id == dept_id,
        User.is_active == True
    ).all()
    return [u.id for u in users]


def _get_evaluator_type(user: User, db: Session) -> str:
    """
    判断评价人类型（部门经理/项目经理）

    Args:
        user: 用户对象
        db: 数据库会话

    Returns:
        str: 评价人类型（DEPT_MANAGER/PROJECT_MANAGER/BOTH）
    """
    is_dept_manager = False
    is_project_manager = False

    for user_role in (user.roles or []):
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ''

        if role_code in ['dept_manager', 'department_manager', '部门经理'] or role_name in ['dept_manager', 'department_manager', '部门经理']:
            is_dept_manager = True
        if role_code in ['pm', 'project_manager', '项目经理'] or role_name in ['pm', 'project_manager', '项目经理']:
            is_project_manager = True

    if is_dept_manager and is_project_manager:
        return 'BOTH'
    elif is_dept_manager:
        return 'DEPT_MANAGER'
    elif is_project_manager:
        return 'PROJECT_MANAGER'
    else:
        return 'OTHER'


def _get_team_name(db: Session, team_id: int) -> str:
    """获取团队名称"""
    from app.models.organization import Department
    dept = db.query(Department).filter(Department.id == team_id).first()
    return dept.name if dept else f"团队{team_id}"


def _get_department_name(db: Session, dept_id: int) -> str:
    """获取部门名称"""
    from app.models.organization import Department
    dept = db.query(Department).filter(Department.id == dept_id).first()
    return dept.name if dept else f"部门{dept_id}"



from fastapi import APIRouter

router = APIRouter(
    prefix="/performance/integration",
    tags=["integration"]
)

# 共 2 个路由

# ==================== 绩效融合 API ====================

@router.get("/integrated/{user_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_integrated_performance(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    period: Optional[str] = Query(None, description="考核周期 (格式: YYYY-MM)"),
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取融合后的绩效结果
    融合公式: 综合得分 = 基础绩效得分 × 70% + 任职资格得分 × 30%
    """
    # 权限检查：只能查看自己的或下属的绩效
    if user_id != current_user.id:
        # 检查是否是当前用户的下属
        manager_roles = PerformanceService.get_user_manager_roles(db, current_user)
        if not manager_roles.get('is_dept_manager') and not manager_roles.get('is_project_manager'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看该用户的绩效"
            )

    if period:
        result = PerformanceIntegrationService.calculate_integrated_score(
            db, user_id, period
        )
    elif period_id:
        result = PerformanceIntegrationService.get_integrated_performance_for_period(
            db, user_id, period_id
        )
    else:
        # 获取最新周期
        result = PerformanceIntegrationService.get_integrated_performance_for_period(
            db, user_id, None
        )

    if not result:
        raise HTTPException(status_code=404, detail="未找到绩效数据")

    return ResponseModel(code=200, message="获取成功", data=result)


@router.post("/calculate-integrated", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def calculate_integrated_performance(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int = Query(..., description="用户ID"),
    period: str = Query(..., description="考核周期 (格式: YYYY-MM)"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算融合绩效
    仅HR和管理层可调用
    """
    # 权限检查
    manager_roles = PerformanceService.get_user_manager_roles(db, current_user)
    if not (manager_roles.get('is_dept_manager') or 
            manager_roles.get('is_project_manager') or
            current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权执行此操作"
        )

    result = PerformanceIntegrationService.calculate_integrated_score(
        db, user_id, period
    )

    if not result:
        raise HTTPException(status_code=404, detail="未找到绩效数据")

    return ResponseModel(code=200, message="计算成功", data=result)

