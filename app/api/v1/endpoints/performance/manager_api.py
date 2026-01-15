# -*- coding: utf-8 -*-
"""
新绩效-经理端 - 自动生成
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
    prefix="/performance/new/manager",
    tags=["manager_api"]
)

# 共 3 个路由

# ==================== 新绩效系统 - 经理端 API ====================

@router.get("/evaluation-tasks", response_model=EvaluationTaskListResponse, status_code=status.HTTP_200_OK)
def get_evaluation_tasks(
    *,
    db: Session = Depends(deps.get_db),
    period: Optional[str] = Query(None, description="评价周期 (YYYY-MM)"),
    status_filter: Optional[str] = Query(None, description="状态筛选: PENDING/COMPLETED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    经理查看待评价任务列表（带权限过滤）
    """
    if not period:
        period = date.today().strftime("%Y-%m")

    # 获取当前用户可管理的员工列表
    manageable_employee_ids = PerformanceService.get_manageable_employees(
        db, current_user, period
    )

    if not manageable_employee_ids:
        # 如果不是经理角色，返回空列表
        return EvaluationTaskListResponse(
            total=0,
            pending_count=0,
            completed_count=0,
            tasks=[]
        )

    # 获取待评价的工作总结（只包含可管理的员工）
    summaries = db.query(MonthlyWorkSummary).filter(
        MonthlyWorkSummary.period == period,
        MonthlyWorkSummary.employee_id.in_(manageable_employee_ids),
        MonthlyWorkSummary.status.in_(['SUBMITTED', 'EVALUATING', 'COMPLETED'])
    ).all()

    # 获取当前用户的经理角色信息
    manager_roles = PerformanceService.get_user_manager_roles(db, current_user)

    tasks = []
    total = 0
    pending_count = 0
    completed_count = 0

    for summary in summaries:
        # 检查当前用户是否已评价
        my_eval = db.query(PerformanceEvaluationRecord).filter(
            PerformanceEvaluationRecord.summary_id == summary.id,
            PerformanceEvaluationRecord.evaluator_id == current_user.id
        ).first()

        if my_eval:
            eval_status = my_eval.status
            if eval_status == 'COMPLETED':
                completed_count += 1
            else:
                pending_count += 1
        else:
            # 创建待评价记录
            eval_status = 'PENDING'
            pending_count += 1

        # 判断是否需要筛选
        if status_filter:
            if status_filter == 'PENDING' and eval_status != 'PENDING':
                continue
            if status_filter == 'COMPLETED' and eval_status != 'COMPLETED':
                continue

        # 获取员工信息
        employee = summary.employee

        # 计算截止日期（下月5号）
        year, month = map(int, summary.period.split('-'))
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        deadline = date(next_year, next_month, 5)

        # 判断评价类型和项目信息
        evaluation_type = "dept"
        project_id = None
        project_name = None

        if my_eval:
            if my_eval.evaluator_type == 'PROJECT_MANAGER':
                evaluation_type = "project"
                project_id = my_eval.project_id
                if project_id:
                    project = db.query(Project).get(project_id)
                    project_name = project.project_name if project else None

        task = EvaluationTaskItem(
            task_id=summary.id,
            employee_id=summary.employee_id,
            employee_name=employee.real_name if employee else "未知",
            employee_department=employee.department if employee else None,
            period=summary.period,
            evaluation_type=evaluation_type,
            project_id=project_id,
            project_name=project_name,
            status=eval_status,
            deadline=deadline,
            submit_date=summary.submit_date
        )
        tasks.append(task)
        total += 1

    return EvaluationTaskListResponse(
        total=total,
        pending_count=pending_count,
        completed_count=completed_count,
        tasks=tasks
    )


@router.get("/evaluation/{task_id}", response_model=EvaluationDetailResponse, status_code=status.HTTP_200_OK)
def get_evaluation_detail(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    经理查看评价详情（工作总结+历史绩效）
    """
    # 获取工作总结
    summary = db.query(MonthlyWorkSummary).filter(
        MonthlyWorkSummary.id == task_id
    ).first()

    if not summary:
        raise HTTPException(status_code=404, detail="工作总结不存在")

    # 获取员工信息
    employee = summary.employee
    employee_info = {
        "id": employee.id,
        "name": employee.real_name or employee.username,
        "department": employee.department if employee else None,
        "position": employee.position if employee else None
    }

    # 获取历史绩效（最近3个月）
    historical_performance = PerformanceService.get_historical_performance(
        db, summary.employee_id, 3
    )

    # 获取我的评价记录
    my_evaluation = db.query(PerformanceEvaluationRecord).filter(
        PerformanceEvaluationRecord.summary_id == summary.id,
        PerformanceEvaluationRecord.evaluator_id == current_user.id
    ).first()

    return EvaluationDetailResponse(
        summary=summary,
        employee_info=employee_info,
        historical_performance=historical_performance,
        my_evaluation=my_evaluation
    )


@router.post("/evaluation/{task_id}", response_model=PerformanceEvaluationRecordResponse, status_code=status.HTTP_201_CREATED)
def submit_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    evaluation_in: PerformanceEvaluationRecordCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    经理提交评价
    """
    # 获取工作总结
    summary = db.query(MonthlyWorkSummary).filter(
        MonthlyWorkSummary.id == task_id
    ).first()

    if not summary:
        raise HTTPException(status_code=404, detail="工作总结不存在")

    # 检查是否已评价
    existing_eval = db.query(PerformanceEvaluationRecord).filter(
        PerformanceEvaluationRecord.summary_id == task_id,
        PerformanceEvaluationRecord.evaluator_id == current_user.id
    ).first()

    if existing_eval and existing_eval.status == 'COMPLETED':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已完成该评价"
        )

    # 判断评价人类型（部门经理/项目经理）
    evaluator_type = _get_evaluator_type(current_user, db)

    if existing_eval:
        # 更新评价
        existing_eval.score = evaluation_in.score
        existing_eval.comment = evaluation_in.comment
        existing_eval.project_id = evaluation_in.project_id
        existing_eval.project_weight = evaluation_in.project_weight
        existing_eval.status = 'COMPLETED'
        existing_eval.evaluated_at = datetime.now()
        evaluation = existing_eval
    else:
        # 创建新评价
        evaluation = PerformanceEvaluationRecord(
            summary_id=task_id,
            evaluator_id=current_user.id,
            evaluator_type=evaluator_type,
            project_id=evaluation_in.project_id,
            project_weight=evaluation_in.project_weight,
            score=evaluation_in.score,
            comment=evaluation_in.comment,
            status='COMPLETED',
            evaluated_at=datetime.now()
        )
        db.add(evaluation)

    # 更新工作总结状态
    if summary.status == 'SUBMITTED':
        summary.status = 'EVALUATING'

    # 检查是否所有评价都已完成
    all_evals = db.query(PerformanceEvaluationRecord).filter(
        PerformanceEvaluationRecord.summary_id == task_id
    ).all()

    if all([e.status == 'COMPLETED' for e in all_evals]):
        summary.status = 'COMPLETED'

    db.commit()
    db.refresh(evaluation)

    return evaluation



