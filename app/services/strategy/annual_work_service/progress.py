# -*- coding: utf-8 -*-
"""
年度重点工作服务 - 进度管理
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.strategy import AnnualKeyWork, AnnualKeyWorkProjectLink
from app.schemas.strategy import AnnualKeyWorkProgressUpdate

from .crud import get_annual_work


def update_progress(
    db: Session,
    work_id: int,
    data: AnnualKeyWorkProgressUpdate
) -> Optional[AnnualKeyWork]:
    """
    更新进度

    Args:
        db: 数据库会话
        work_id: 重点工作 ID
        data: 进度更新数据

    Returns:
        Optional[AnnualKeyWork]: 更新后的年度重点工作
    """
    work = get_annual_work(db, work_id)
    if not work:
        return None

    work.progress_percent = data.progress_percent
    if data.progress_description:
        work.progress_description = data.progress_description

    # 根据进度自动更新状态
    if data.progress_percent >= 100:
        work.status = "COMPLETED"
    elif data.progress_percent > 0:
        work.status = "IN_PROGRESS"

    db.commit()
    db.refresh(work)
    return work


def calculate_progress_from_projects(db: Session, work_id: int) -> Optional[Decimal]:
    """
    根据关联项目计算进度

    Args:
        db: 数据库会话
        work_id: 重点工作 ID

    Returns:
        Optional[Decimal]: 加权进度
    """
    links = db.query(AnnualKeyWorkProjectLink).filter(
        AnnualKeyWorkProjectLink.annual_work_id == work_id,
        AnnualKeyWorkProjectLink.is_active == True
    ).all()

    if not links:
        return None

    total_weight = Decimal(0)
    weighted_progress = Decimal(0)

    for link in links:
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == link.project_id).first()
        if project and project.progress is not None:
            weight = link.contribution_weight or Decimal(1)
            total_weight += weight
            weighted_progress += Decimal(str(project.progress)) * weight

    if total_weight == 0:
        return None

    return weighted_progress / total_weight


def sync_progress_from_projects(db: Session, work_id: int) -> Optional[AnnualKeyWork]:
    """
    从关联项目同步进度

    Args:
        db: 数据库会话
        work_id: 重点工作 ID

    Returns:
        Optional[AnnualKeyWork]: 更新后的重点工作
    """
    progress = calculate_progress_from_projects(db, work_id)
    if progress is None:
        return None

    work = get_annual_work(db, work_id)
    if not work:
        return None

    work.progress_percent = progress
    work.progress_description = "从关联项目自动同步"

    # 根据进度自动更新状态
    if progress >= 100:
        work.status = "COMPLETED"
    elif progress > 0:
        work.status = "IN_PROGRESS"

    db.commit()
    db.refresh(work)
    return work
