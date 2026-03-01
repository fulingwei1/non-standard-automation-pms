# -*- coding: utf-8 -*-
"""
绩效评价 API
提供评价任务列表查询功能
"""

import logging
from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models.organization import Department
from app.models.performance.monthly_system import (
    MonthlyWorkSummary,
    PerformanceEvaluationRecord,
)
from app.models.performance.enums import (
    EvaluatorTypeEnum,
    EvaluationStatusEnum,
    MonthlySummaryStatusEnum,
)
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.performance import EvaluationTaskItem, EvaluationTaskListResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/performance",
    tags=["performance-evaluation-tasks"]
)


def _get_department_members(db: Session, user: User) -> List[int]:
    """
    获取当前用户作为部门经理管理的员工ID列表

    通过以下方式判断:
    1. 查找 departments 表中 manager_id 指向当前用户关联的 employee
    2. 获取该部门下所有员工的 user_id
    """
    from app.models.organization import Employee

    # 先查找当前用户关联的 employee
    employee = db.query(Employee).filter(
        Employee.is_active,
        or_(
            Employee.name == user.real_name,
            Employee.employee_code == user.username
        )
    ).first()

    if not employee:
        return []

    # 查找以该员工为经理的部门
    managed_depts = db.query(Department).filter(
        Department.manager_id == employee.id,
        Department.is_active
    ).all()

    if not managed_depts:
        return []

    dept_names = [d.dept_name for d in managed_depts]

    # 获取这些部门的所有员工的 user_id
    # 通过 User 表的 department 字段匹配
    member_ids = db.query(User.id).filter(
        User.department.in_(dept_names),
        User.is_active,
        User.id != user.id  # 排除自己
    ).all()

    return [m[0] for m in member_ids]


def _get_project_member_info(db: Session, user: User) -> List[dict]:
    """
    获取当前用户作为项目经理管理的项目成员信息

    Returns:
        List[dict]: [{"project_id": ..., "project_name": ..., "member_ids": [...]}]
    """
    # 查找当前用户担任PM的活跃项目
    managed_projects = db.query(Project).filter(
        Project.pm_id == user.id,
        Project.is_active
    ).all()

    if not managed_projects:
        return []

    result = []
    for project in managed_projects:
        # 获取项目成员 (排除PM自己)
        members = db.query(ProjectMember.user_id).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id != user.id
        ).distinct().all()

        member_ids = [m[0] for m in members]
        if member_ids:
            result.append({
                "project_id": project.id,
                "project_name": project.project_name,
                "member_ids": member_ids
            })

    return result


def _build_evaluation_task(
    summary: MonthlyWorkSummary,
    evaluation_type: str,
    project_id: Optional[int] = None,
    project_name: Optional[str] = None,
    existing_eval: Optional[PerformanceEvaluationRecord] = None
) -> EvaluationTaskItem:
    """构建评价任务项"""
    return EvaluationTaskItem(
        task_id=summary.id,
        employee_id=summary.employee_id,
        employee_name=summary.employee.real_name if summary.employee else "未知",
        employee_department=summary.employee.department if summary.employee else None,
        period=summary.period,
        evaluation_type=evaluation_type,
        project_id=project_id,
        project_name=project_name,
        status="COMPLETED" if existing_eval and existing_eval.status == EvaluationStatusEnum.COMPLETED.value else "PENDING",
        deadline=None,  # 可以从配置中获取截止日期
        submit_date=summary.submit_date
    )


@router.get("/evaluation-tasks", response_model=EvaluationTaskListResponse, status_code=status.HTTP_200_OK)
def get_evaluation_tasks(
    *,
    db: Session = Depends(deps.get_db),
    period: Optional[str] = Query(None, description="评价周期 (YYYY-MM)"),
    status_filter: Optional[str] = Query(None, description="状态筛选: PENDING/COMPLETED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取评价任务列表

    根据当前用户角色返回待评价任务：
    - 部门经理：返回所管理部门员工的工作总结
    - 项目经理：返回所管理项目成员的工作总结
    """
    if not period:
        period = date.today().strftime("%Y-%m")

    logger.info(f"用户 {current_user.username} 查询绩效评价，周期: {period}, 租户: {current_user.tenant_id}")

    tasks: List[EvaluationTaskItem] = []

    # 1. 查询部门经理评价任务
    dept_member_ids = _get_department_members(db, current_user)
    logger.debug(f"部门成员ID列表: {dept_member_ids}, 数量: {len(dept_member_ids)}")

    if dept_member_ids:
        # 查询这些员工已提交的工作总结（添加租户过滤）
        dept_summaries = db.query(MonthlyWorkSummary).options(
            joinedload(MonthlyWorkSummary.employee),
            joinedload(MonthlyWorkSummary.evaluations)
        ).filter(
            MonthlyWorkSummary.employee_id.in_(dept_member_ids),
            MonthlyWorkSummary.period == period,
            MonthlyWorkSummary.status.in_([
                MonthlySummaryStatusEnum.SUBMITTED.value,
                MonthlySummaryStatusEnum.EVALUATING.value
            ])
        ).all()

        logger.debug(f"部门工作总结数量: {len(dept_summaries)}")

        for summary in dept_summaries:
            # 租户隔离检查
            if hasattr(summary, 'tenant_id') and summary.tenant_id != current_user.tenant_id:
                logger.warning(f"跨租户数据访问被阻止: summary.id={summary.id}, summary.tenant_id={summary.tenant_id}, user.tenant_id={current_user.tenant_id}")
                continue

            # 检查当前用户是否已评价
            existing_eval = next(
                (e for e in summary.evaluations
                 if e.evaluator_id == current_user.id
                 and e.evaluator_type == EvaluatorTypeEnum.DEPT_MANAGER.value),
                None
            )
            task = _build_evaluation_task(
                summary,
                evaluation_type="dept",
                existing_eval=existing_eval
            )
            tasks.append(task)

    # 2. 查询项目经理评价任务
    project_info_list = _get_project_member_info(db, current_user)
    logger.debug(f"项目信息列表数量: {len(project_info_list)}")

    for project_info in project_info_list:
        project_id = project_info["project_id"]
        project_name = project_info["project_name"]
        member_ids = project_info["member_ids"]

        # 查询这些员工已提交的工作总结
        project_summaries = db.query(MonthlyWorkSummary).options(
            joinedload(MonthlyWorkSummary.employee),
            joinedload(MonthlyWorkSummary.evaluations)
        ).filter(
            MonthlyWorkSummary.employee_id.in_(member_ids),
            MonthlyWorkSummary.period == period,
            MonthlyWorkSummary.status.in_([
                MonthlySummaryStatusEnum.SUBMITTED.value,
                MonthlySummaryStatusEnum.EVALUATING.value
            ])
        ).all()

        logger.debug(f"项目 {project_name} 工作总结数量: {len(project_summaries)}")

        for summary in project_summaries:
            # 租户隔离检查
            if hasattr(summary, 'tenant_id') and summary.tenant_id != current_user.tenant_id:
                logger.warning(f"跨租户数据访问被阻止: summary.id={summary.id}")
                continue

            # 检查当前用户是否已对该项目评价
            existing_eval = next(
                (e for e in summary.evaluations
                 if e.evaluator_id == current_user.id
                 and e.evaluator_type == EvaluatorTypeEnum.PROJECT_MANAGER.value
                 and e.project_id == project_id),
                None
            )
            task = _build_evaluation_task(
                summary,
                evaluation_type="project",
                project_id=project_id,
                project_name=project_name,
                existing_eval=existing_eval
            )
            tasks.append(task)

    logger.info(f"共查询到 {len(tasks)} 条评价任务")

    # 3. 应用状态筛选
    if status_filter:
        tasks = [t for t in tasks if t.status == status_filter]
        logger.debug(f"状态筛选后: {len(tasks)} 条任务")

    # 4. 统计
    pending_count = sum(1 for t in tasks if t.status == "PENDING")
    completed_count = sum(1 for t in tasks if t.status == "COMPLETED")

    return EvaluationTaskListResponse(
        tasks=tasks,
        total=len(tasks),
        pending_count=pending_count,
        completed_count=completed_count
    )
