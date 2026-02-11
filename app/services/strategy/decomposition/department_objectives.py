# -*- coding: utf-8 -*-
"""
部门目标管理

提供部门目标的 CRUD 操作和详情查询
"""

"""
战略管理服务 - 目标分解

实现从公司战略到部门目标到个人 KPI 的层层分解
"""

import json
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.strategy import (
    CSF,
    KPI,
    DepartmentObjective,
    PersonalKPI,
    Strategy,
)
from app.schemas.strategy import (
    DecompositionTreeNode,
    DecompositionTreeResponse,
    DepartmentObjectiveCreate,
    DepartmentObjectiveDetailResponse,
    DepartmentObjectiveUpdate,
    PersonalKPICreate,
    PersonalKPIUpdate,
    TraceToStrategyResponse,
)



# ============================================
# 部门目标管理
# ============================================

def create_department_objective(
    db: Session,
    data: DepartmentObjectiveCreate
) -> DepartmentObjective:
    """
    创建部门目标

    Args:
        db: 数据库会话
        data: 创建数据

    Returns:
        DepartmentObjective: 创建的部门目标
    """
    obj = DepartmentObjective(
        strategy_id=data.strategy_id,
        department_id=data.department_id,
        csf_id=data.csf_id,
        kpi_id=data.kpi_id,
        year=data.year,
        objectives=json.dumps(data.objectives, ensure_ascii=False) if data.objectives else None,
        key_results=data.key_results,
        target_value=data.target_value,
        weight=data.weight,
        owner_user_id=data.owner_user_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_department_objective(
    db: Session,
    objective_id: int
) -> Optional[DepartmentObjective]:
    """
    获取部门目标

    Args:
        db: 数据库会话
        objective_id: 目标 ID

    Returns:
        Optional[DepartmentObjective]: 部门目标
    """
    return db.query(DepartmentObjective).filter(
        DepartmentObjective.id == objective_id,
        DepartmentObjective.is_active == True
    ).first()


def list_department_objectives(
    db: Session,
    strategy_id: Optional[int] = None,
    department_id: Optional[int] = None,
    year: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[DepartmentObjective], int]:
    """
    获取部门目标列表

    Args:
        db: 数据库会话
        strategy_id: 战略 ID 筛选
        department_id: 部门 ID 筛选
        year: 年度筛选
        skip: 跳过数量
        limit: 限制数量

    Returns:
        tuple: (部门目标列表, 总数)
    """
    query = db.query(DepartmentObjective).filter(DepartmentObjective.is_active == True)

    if strategy_id:
        query = query.filter(DepartmentObjective.strategy_id == strategy_id)
    if department_id:
        query = query.filter(DepartmentObjective.department_id == department_id)
    if year:
        query = query.filter(DepartmentObjective.year == year)

    total = query.count()
    items = apply_pagination(query.order_by(
        DepartmentObjective.department_id,
        DepartmentObjective.csf_id
    ), skip, limit).all()

    return items, total


def update_department_objective(
    db: Session,
    objective_id: int,
    data: DepartmentObjectiveUpdate
) -> Optional[DepartmentObjective]:
    """
    更新部门目标

    Args:
        db: 数据库会话
        objective_id: 目标 ID
        data: 更新数据

    Returns:
        Optional[DepartmentObjective]: 更新后的部门目标
    """
    obj = get_department_objective(db, objective_id)
    if not obj:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # 处理 JSON 字段
    if "objectives" in update_data and update_data["objectives"]:
        update_data["objectives"] = json.dumps(update_data["objectives"], ensure_ascii=False)

    for key, value in update_data.items():
        setattr(obj, key, value)

    db.commit()
    db.refresh(obj)
    return obj


def delete_department_objective(db: Session, objective_id: int) -> bool:
    """
    删除部门目标（软删除）

    Args:
        db: 数据库会话
        objective_id: 目标 ID

    Returns:
        bool: 是否删除成功
    """
    obj = get_department_objective(db, objective_id)
    if not obj:
        return False

    obj.is_active = False
    db.commit()
    return True


def get_department_objective_detail(
    db: Session,
    objective_id: int
) -> Optional[DepartmentObjectiveDetailResponse]:
    """
    获取部门目标详情

    Args:
        db: 数据库会话
        objective_id: 目标 ID

    Returns:
        Optional[DepartmentObjectiveDetailResponse]: 部门目标详情
    """
    obj = get_department_objective(db, objective_id)
    if not obj:
        return None

    # 获取部门名称
    dept_name = None
    if obj.department_id:
        from app.models.organization import Department
        dept = db.query(Department).filter(Department.id == obj.department_id).first()
        if dept:
            dept_name = dept.name

    # 获取责任人名称
    owner_name = None
    if obj.owner_user_id:
        from app.models.user import User
        user = db.query(User).filter(User.id == obj.owner_user_id).first()
        if user:
            owner_name = user.name

    # 获取关联的 CSF 和 KPI 名称
    csf_name = None
    kpi_name = None
    if obj.csf_id:
        csf = db.query(CSF).filter(CSF.id == obj.csf_id).first()
        if csf:
            csf_name = csf.name
    if obj.kpi_id:
        kpi = db.query(KPI).filter(KPI.id == obj.kpi_id).first()
        if kpi:
            kpi_name = kpi.name

    # 统计个人 KPI 数量
    personal_kpi_count = db.query(PersonalKPI).filter(
        PersonalKPI.dept_objective_id == objective_id,
        PersonalKPI.is_active == True
    ).count()

    return DepartmentObjectiveDetailResponse(
        id=obj.id,
        strategy_id=obj.strategy_id,
        department_id=obj.department_id,
        csf_id=obj.csf_id,
        kpi_id=obj.kpi_id,
        year=obj.year,
        objectives=json.loads(obj.objectives) if obj.objectives else None,
        key_results=obj.key_results,
        target_value=obj.target_value,
        current_value=obj.current_value,
        weight=obj.weight,
        status=obj.status,
        owner_user_id=obj.owner_user_id,
        is_active=obj.is_active,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
        department_name=dept_name,
        owner_name=owner_name,
        csf_name=csf_name,
        kpi_name=kpi_name,
        personal_kpi_count=personal_kpi_count,
    )


