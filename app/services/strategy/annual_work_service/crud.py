# -*- coding: utf-8 -*-
"""
年度重点工作服务 - CRUD操作
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.strategy import AnnualKeyWork, CSF
from app.schemas.strategy import (
    AnnualKeyWorkCreate,
    AnnualKeyWorkUpdate,
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
