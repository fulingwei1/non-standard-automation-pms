# -*- coding: utf-8 -*-
"""
战略管理服务 - 年度重点工作
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.strategy import AnnualKeyWork, AnnualKeyWorkProjectLink, CSF
from app.schemas.strategy import (
    AnnualKeyWorkCreate,
    AnnualKeyWorkDetailResponse,
    AnnualKeyWorkProgressUpdate,
    AnnualKeyWorkUpdate,
    ProjectLinkItem,
)


def create_annual_work(db: Session, data: AnnualKeyWorkCreate) -> AnnualKeyWork:
    """
    创建年度重点工作

    Args:
        db: 数据库会话
        data: 创建数据

    Returns:
        AnnualKeyWork: 创建的年度重点工作
    """
    work = AnnualKeyWork(
        csf_id=data.csf_id,
        code=data.code,
        name=data.name,
        description=data.description,
        voc_source=data.voc_source,
        pain_point=data.pain_point,
        solution=data.solution,
        year=data.year,
        priority=data.priority,
        start_date=data.start_date,
        end_date=data.end_date,
        owner_dept_id=data.owner_dept_id,
        owner_user_id=data.owner_user_id,
    )
    db.add(work)
    db.commit()
    db.refresh(work)
    return work


def get_annual_work(db: Session, work_id: int) -> Optional[AnnualKeyWork]:
    """
    获取年度重点工作

    Args:
        db: 数据库会话
        work_id: 重点工作 ID

    Returns:
        Optional[AnnualKeyWork]: 年度重点工作
    """
    return db.query(AnnualKeyWork).filter(
        AnnualKeyWork.id == work_id,
        AnnualKeyWork.is_active == True
    ).first()


def list_annual_works(
    db: Session,
    csf_id: Optional[int] = None,
    strategy_id: Optional[int] = None,
    year: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[AnnualKeyWork], int]:
    """
    获取年度重点工作列表

    Args:
        db: 数据库会话
        csf_id: CSF ID 筛选
        strategy_id: 战略 ID 筛选
        year: 年度筛选
        status: 状态筛选
        skip: 跳过数量
        limit: 限制数量

    Returns:
        tuple: (重点工作列表, 总数)
    """
    query = db.query(AnnualKeyWork).filter(AnnualKeyWork.is_active == True)

    if csf_id:
        query = query.filter(AnnualKeyWork.csf_id == csf_id)

    if strategy_id:
        query = query.join(CSF).filter(
            CSF.strategy_id == strategy_id,
            CSF.is_active == True
        )

    if year:
        query = query.filter(AnnualKeyWork.year == year)

    if status:
        query = query.filter(AnnualKeyWork.status == status)

    total = query.count()
    items = query.order_by(
        AnnualKeyWork.priority,
        AnnualKeyWork.code
    ).offset(skip).limit(limit).all()

    return items, total


def update_annual_work(
    db: Session,
    work_id: int,
    data: AnnualKeyWorkUpdate
) -> Optional[AnnualKeyWork]:
    """
    更新年度重点工作

    Args:
        db: 数据库会话
        work_id: 重点工作 ID
        data: 更新数据

    Returns:
        Optional[AnnualKeyWork]: 更新后的年度重点工作
    """
    work = get_annual_work(db, work_id)
    if not work:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(work, key, value)

    db.commit()
    db.refresh(work)
    return work


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


def delete_annual_work(db: Session, work_id: int) -> bool:
    """
    删除年度重点工作（软删除）

    Args:
        db: 数据库会话
        work_id: 重点工作 ID

    Returns:
        bool: 是否删除成功
    """
    work = get_annual_work(db, work_id)
    if not work:
        return False

    work.is_active = False
    db.commit()
    return True


def get_annual_work_detail(db: Session, work_id: int) -> Optional[AnnualKeyWorkDetailResponse]:
    """
    获取年度重点工作详情

    Args:
        db: 数据库会话
        work_id: ��点工作 ID

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


# ============================================
# 项目关联管理
# ============================================

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


# ============================================
# 统计分析
# ============================================

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
