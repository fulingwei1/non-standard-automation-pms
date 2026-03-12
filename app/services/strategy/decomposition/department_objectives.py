# -*- coding: utf-8 -*-
"""
部门目标管理

提供部门目标的 CRUD 操作和详情查询
"""

import json
from typing import List, Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.strategy import (
    DepartmentObjective,
    PersonalKPI,
)
from app.schemas.strategy import (
    DepartmentObjectiveCreate,
    DepartmentObjectiveDetailResponse,
    DepartmentObjectiveUpdate,
)

# ============================================
# 部门目标管理
# ============================================


def create_department_objective(
    db: Session, data: DepartmentObjectiveCreate
) -> DepartmentObjective:
    obj = DepartmentObjective(
        strategy_id=data.strategy_id,
        department_id=data.department_id,
        year=data.year,
        quarter=data.quarter,
        objectives=json.dumps(data.objectives, ensure_ascii=False) if data.objectives else None,
        key_results=json.dumps(data.key_results, ensure_ascii=False) if data.key_results else None,
        kpis_config=json.dumps(data.kpis_config, ensure_ascii=False) if data.kpis_config else None,
        owner_user_id=data.owner_user_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_department_objective(db: Session, objective_id: int) -> Optional[DepartmentObjective]:
    return (
        db.query(DepartmentObjective)
        .filter(DepartmentObjective.id == objective_id, DepartmentObjective.is_active)
        .first()
    )


def list_department_objectives(
    db: Session,
    strategy_id: Optional[int] = None,
    department_id: Optional[int] = None,
    year: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[DepartmentObjective], int]:
    query = db.query(DepartmentObjective).filter(DepartmentObjective.is_active)

    if strategy_id:
        query = query.filter(DepartmentObjective.strategy_id == strategy_id)
    if department_id:
        query = query.filter(DepartmentObjective.department_id == department_id)
    if year:
        query = query.filter(DepartmentObjective.year == year)

    total = query.count()
    items = apply_pagination(
        query.order_by(DepartmentObjective.department_id, DepartmentObjective.year), skip, limit
    ).all()

    return items, total


def update_department_objective(
    db: Session, objective_id: int, data: DepartmentObjectiveUpdate
) -> Optional[DepartmentObjective]:
    obj = get_department_objective(db, objective_id)
    if not obj:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # 处理 JSON 字段
    for json_field in ("objectives", "key_results", "kpis_config"):
        if json_field in update_data and update_data[json_field] is not None:
            update_data[json_field] = json.dumps(update_data[json_field], ensure_ascii=False)

    for key, value in update_data.items():
        setattr(obj, key, value)

    db.commit()
    db.refresh(obj)
    return obj


def delete_department_objective(db: Session, objective_id: int) -> bool:
    obj = get_department_objective(db, objective_id)
    if not obj:
        return False

    obj.is_active = False
    db.commit()
    return True


def _safe_json_loads(val):
    """安全解析 JSON 字符串"""
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return val


def get_department_objective_detail(
    db: Session, objective_id: int
) -> Optional[DepartmentObjectiveDetailResponse]:
    obj = get_department_objective(db, objective_id)
    if not obj:
        return None

    # 获取部门名称
    dept_name = None
    if obj.department_id:
        from app.models.organization import Department
        dept = db.query(Department).filter(Department.id == obj.department_id).first()
        if dept:
            dept_name = dept.dept_name

    # 获取责任人名称
    owner_name = None
    if obj.owner_user_id:
        from app.models.user import User
        user = db.query(User).filter(User.id == obj.owner_user_id).first()
        if user:
            owner_name = user.real_name or user.username

    # 统计个人 KPI 数量
    personal_kpi_count = (
        db.query(PersonalKPI)
        .filter(PersonalKPI.department_objective_id == objective_id, PersonalKPI.is_active)
        .count()
    )

    return DepartmentObjectiveDetailResponse(
        id=obj.id,
        strategy_id=obj.strategy_id,
        department_id=obj.department_id,
        year=obj.year,
        quarter=obj.quarter,
        objectives=_safe_json_loads(obj.objectives),
        key_results=_safe_json_loads(obj.key_results),
        kpis_config=_safe_json_loads(obj.kpis_config),
        status=obj.status or "DRAFT",
        owner_user_id=obj.owner_user_id,
        approved_by=obj.approved_by,
        approved_at=str(obj.approved_at) if obj.approved_at else None,
        is_active=obj.is_active,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
        department_name=dept_name,
        owner_name=owner_name,
        personal_kpi_count=personal_kpi_count,
    )
