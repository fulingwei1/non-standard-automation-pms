# -*- coding: utf-8 -*-
"""
个人 KPI 管理

提供个人 KPI 的 CRUD 操作、评分和批量创建
"""

"""
战略管理服务 - 目标分解

实现从公司战略到部门目标到个人 KPI 的层层分解
"""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.strategy import (
    PersonalKPI,
)
from app.schemas.strategy import (
    PersonalKPICreate,
    PersonalKPIUpdate,
)


# ============================================
# 个人 KPI 管理
# ============================================

def create_personal_kpi(db: Session, data: PersonalKPICreate) -> PersonalKPI:
    """
    创建个人 KPI

    Args:
        db: 数据库会话
        data: 创建数据

    Returns:
        PersonalKPI: 创建的个人 KPI
    """
    kpi = PersonalKPI(
        user_id=data.user_id,
        dept_objective_id=data.dept_objective_id,
        source_kpi_id=data.source_kpi_id,
        source_type=data.source_type,
        year=data.year,
        period=data.period,
        code=data.code,
        name=data.name,
        description=data.description,
        unit=data.unit,
        direction=data.direction,
        target_value=data.target_value,
        weight=data.weight,
    )
    db.add(kpi)
    db.commit()
    db.refresh(kpi)
    return kpi


def get_personal_kpi(db: Session, kpi_id: int) -> Optional[PersonalKPI]:
    """
    获取个人 KPI

    Args:
        db: 数据库会话
        kpi_id: KPI ID

    Returns:
        Optional[PersonalKPI]: 个人 KPI
    """
    return db.query(PersonalKPI).filter(
        PersonalKPI.id == kpi_id,
        PersonalKPI.is_active
    ).first()


def list_personal_kpis(
    db: Session,
    user_id: Optional[int] = None,
    dept_objective_id: Optional[int] = None,
    year: Optional[int] = None,
    period: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[PersonalKPI], int]:
    """
    获取个人 KPI 列表

    Args:
        db: 数据库会话
        user_id: 用户 ID 筛选
        dept_objective_id: 部门目标 ID 筛选
        year: 年度筛选
        period: 周期筛选
        skip: 跳过数量
        limit: 限制数量

    Returns:
        tuple: (个人 KPI 列表, 总数)
    """
    query = db.query(PersonalKPI).filter(PersonalKPI.is_active)

    if user_id:
        query = query.filter(PersonalKPI.user_id == user_id)
    if dept_objective_id:
        query = query.filter(PersonalKPI.dept_objective_id == dept_objective_id)
    if year:
        query = query.filter(PersonalKPI.year == year)
    if period:
        query = query.filter(PersonalKPI.period == period)

    total = query.count()
    items = apply_pagination(query.order_by(PersonalKPI.code), skip, limit).all()

    return items, total


def update_personal_kpi(
    db: Session,
    kpi_id: int,
    data: PersonalKPIUpdate
) -> Optional[PersonalKPI]:
    """
    更新个人 KPI

    Args:
        db: 数据库会话
        kpi_id: KPI ID
        data: 更新数据

    Returns:
        Optional[PersonalKPI]: 更新后的个人 KPI
    """
    kpi = get_personal_kpi(db, kpi_id)
    if not kpi:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(kpi, key, value)

    db.commit()
    db.refresh(kpi)
    return kpi


def delete_personal_kpi(db: Session, kpi_id: int) -> bool:
    """
    删除个人 KPI（软删除）

    Args:
        db: 数据库会话
        kpi_id: KPI ID

    Returns:
        bool: 是否删除成功
    """
    kpi = get_personal_kpi(db, kpi_id)
    if not kpi:
        return False

    kpi.is_active = False
    db.commit()
    return True


def self_rating(
    db: Session,
    kpi_id: int,
    actual_value: Decimal,
    self_score: int,
    self_comment: Optional[str] = None
) -> Optional[PersonalKPI]:
    """
    员工自评

    Args:
        db: 数据库会话
        kpi_id: KPI ID
        actual_value: 实际值
        self_score: 自评分数
        self_comment: 自评说明

    Returns:
        Optional[PersonalKPI]: 更新后的个人 KPI
    """
    kpi = get_personal_kpi(db, kpi_id)
    if not kpi:
        return None

    kpi.actual_value = actual_value
    kpi.self_score = self_score
    kpi.self_comment = self_comment
    kpi.status = "SELF_RATED"

    db.commit()
    db.refresh(kpi)
    return kpi


def manager_rating(
    db: Session,
    kpi_id: int,
    manager_score: int,
    manager_comment: Optional[str] = None
) -> Optional[PersonalKPI]:
    """
    主管评分

    Args:
        db: 数据库会话
        kpi_id: KPI ID
        manager_score: 主管评分
        manager_comment: 主管评语

    Returns:
        Optional[PersonalKPI]: 更新后的个人 KPI
    """
    kpi = get_personal_kpi(db, kpi_id)
    if not kpi:
        return None

    kpi.manager_score = manager_score
    kpi.manager_comment = manager_comment
    kpi.status = "MANAGER_RATED"

    # 计算最终得分（主管评分）
    kpi.final_score = manager_score

    db.commit()
    db.refresh(kpi)
    return kpi


def batch_create_personal_kpis(
    db: Session,
    items: List[PersonalKPICreate]
) -> List[PersonalKPI]:
    """
    批量创建个人 KPI

    Args:
        db: 数据库会话
        items: KPI 创建数据列表

    Returns:
        List[PersonalKPI]: 创建的个人 KPI 列表
    """
    created = []
    for item in items:
        kpi = create_personal_kpi(db, item)
        created.append(kpi)
    return created


