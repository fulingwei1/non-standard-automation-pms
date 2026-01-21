# -*- coding: utf-8 -*-
"""
年度重点工作服务 - 详情和统计
"""
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.strategy import AnnualKeyWork, AnnualKeyWorkProjectLink, CSF
from app.schemas.strategy import (
    AnnualKeyWorkDetailResponse,
    ProjectLinkItem,
)

from .crud import get_annual_work


def get_annual_work_detail(db: Session, work_id: int) -> Optional[AnnualKeyWorkDetailResponse]:
    """
    获取年度重点工作详情

    Args:
        db: 数据库会话
        work_id: 重点工作 ID

    Returns:
        Optional[AnnualKeyWorkDetailResponse]: 年度重点工作详情
    """
    work = get_annual_work(db, work_id)
    if not work:
        return None

    # 获取责任人和部门名称
    owner_name = None
    owner_dept_name = None

    if work.owner_user_id:
        from app.models.user import User
        user = db.query(User).filter(User.id == work.owner_user_id).first()
        if user:
            owner_name = user.name

    if work.owner_dept_id:
        from app.models.organization import Department
        dept = db.query(Department).filter(Department.id == work.owner_dept_id).first()
        if dept:
            owner_dept_name = dept.name

    # 获取 CSF 信息
    csf = db.query(CSF).filter(CSF.id == work.csf_id).first()
    csf_name = csf.name if csf else None
    csf_dimension = csf.dimension if csf else None

    # 获取关联项目
    links = db.query(AnnualKeyWorkProjectLink).filter(
        AnnualKeyWorkProjectLink.annual_work_id == work_id,
        AnnualKeyWorkProjectLink.is_active == True
    ).all()

    linked_projects = []
    for link in links:
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == link.project_id).first()
        if project:
            linked_projects.append(ProjectLinkItem(
                project_id=project.id,
                project_code=project.code,
                project_name=project.name,
                contribution_weight=link.contribution_weight,
            ))

    # 计算关联项目进度
    linked_project_count = len(linked_projects)

    return AnnualKeyWorkDetailResponse(
        id=work.id,
        csf_id=work.csf_id,
        code=work.code,
        name=work.name,
        description=work.description,
        voc_source=work.voc_source,
        pain_point=work.pain_point,
        solution=work.solution,
        year=work.year,
        priority=work.priority,
        status=work.status,
        start_date=work.start_date,
        end_date=work.end_date,
        progress_percent=work.progress_percent,
        progress_description=work.progress_description,
        owner_dept_id=work.owner_dept_id,
        owner_user_id=work.owner_user_id,
        is_active=work.is_active,
        created_at=work.created_at,
        updated_at=work.updated_at,
        owner_name=owner_name,
        owner_dept_name=owner_dept_name,
        csf_name=csf_name,
        csf_dimension=csf_dimension,
        linked_project_count=linked_project_count,
        linked_projects=linked_projects,
    )


def get_annual_work_stats(
    db: Session,
    strategy_id: int,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    获取年度重点工作统计

    Args:
        db: 数据库会话
        strategy_id: 战略 ID
        year: 年度

    Returns:
        Dict: 统计数据
    """
    if year is None:
        year = date.today().year

    works = db.query(AnnualKeyWork).join(CSF).filter(
        CSF.strategy_id == strategy_id,
        CSF.is_active == True,
        AnnualKeyWork.year == year,
        AnnualKeyWork.is_active == True
    ).all()

    total = len(works)
    by_status = {}
    by_priority = {}
    by_dimension = {}

    total_progress = Decimal(0)

    for work in works:
        # 按状态统计
        status = work.status or "NOT_STARTED"
        by_status[status] = by_status.get(status, 0) + 1

        # 按优先级统计
        priority = work.priority or 3
        by_priority[priority] = by_priority.get(priority, 0) + 1

        # 按维度统计
        csf = db.query(CSF).filter(CSF.id == work.csf_id).first()
        if csf:
            dim = csf.dimension
            if dim not in by_dimension:
                by_dimension[dim] = {"count": 0, "progress_sum": Decimal(0)}
            by_dimension[dim]["count"] += 1
            by_dimension[dim]["progress_sum"] += work.progress_percent or Decimal(0)

        total_progress += work.progress_percent or Decimal(0)

    avg_progress = float(total_progress / total) if total > 0 else 0

    # 计算各维度平均进度
    dimension_progress = {}
    for dim, data in by_dimension.items():
        if data["count"] > 0:
            dimension_progress[dim] = float(data["progress_sum"] / data["count"])

    return {
        "year": year,
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "avg_progress": avg_progress,
        "dimension_progress": dimension_progress,
        "completed": by_status.get("COMPLETED", 0),
        "in_progress": by_status.get("IN_PROGRESS", 0),
        "not_started": by_status.get("NOT_STARTED", 0),
    }
