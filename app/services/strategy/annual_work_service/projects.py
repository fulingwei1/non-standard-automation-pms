# -*- coding: utf-8 -*-
"""
年度重点工作服务 - 项目关联管理
"""
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.strategy import AnnualKeyWorkProjectLink
from app.schemas.strategy import ProjectLinkItem

from .crud import get_annual_work


def link_project(
    db: Session,
    work_id: int,
    project_id: int,
    contribution_weight: Decimal = Decimal("1.0")
) -> Optional[AnnualKeyWorkProjectLink]:
    """
    关联项目

    Args:
        db: 数据库会话
        work_id: 重点工作 ID
        project_id: 项目 ID
        contribution_weight: 贡献权重

    Returns:
        Optional[AnnualKeyWorkProjectLink]: 关联记录
    """
    work = get_annual_work(db, work_id)
    if not work:
        return None

    # 检查是否已关联
    existing = db.query(AnnualKeyWorkProjectLink).filter(
        AnnualKeyWorkProjectLink.annual_work_id == work_id,
        AnnualKeyWorkProjectLink.project_id == project_id
    ).first()

    if existing:
        # 重新激活
        existing.is_active = True
        existing.contribution_weight = contribution_weight
        db.commit()
        db.refresh(existing)
        return existing

    # 创建新关联
    link = AnnualKeyWorkProjectLink(
        annual_work_id=work_id,
        project_id=project_id,
        contribution_weight=contribution_weight,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def unlink_project(db: Session, work_id: int, project_id: int) -> bool:
    """
    取消关联项目

    Args:
        db: 数据库会话
        work_id: 重点工作 ID
        project_id: 项目 ID

    Returns:
        bool: 是否成功
    """
    link = db.query(AnnualKeyWorkProjectLink).filter(
        AnnualKeyWorkProjectLink.annual_work_id == work_id,
        AnnualKeyWorkProjectLink.project_id == project_id,
        AnnualKeyWorkProjectLink.is_active == True
    ).first()

    if not link:
        return False

    link.is_active = False
    db.commit()
    return True


def get_linked_projects(db: Session, work_id: int) -> List[ProjectLinkItem]:
    """
    获取关联的项目列表

    Args:
        db: 数据库会话
        work_id: 重点工作 ID

    Returns:
        List[ProjectLinkItem]: 关联项目列表
    """
    links = db.query(AnnualKeyWorkProjectLink).filter(
        AnnualKeyWorkProjectLink.annual_work_id == work_id,
        AnnualKeyWorkProjectLink.is_active == True
    ).all()

    result = []
    for link in links:
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == link.project_id).first()
        if project:
            result.append(ProjectLinkItem(
                project_id=project.id,
                project_code=project.code,
                project_name=project.name,
                contribution_weight=link.contribution_weight,
            ))

    return result
