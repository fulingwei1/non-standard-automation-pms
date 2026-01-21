# -*- coding: utf-8 -*-
"""
战略管理服务 - CSF 关键成功要素
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.strategy import CSF, KPI, AnnualKeyWork
from app.schemas.strategy import (
    CSFByDimensionItem,
    CSFByDimensionResponse,
    CSFCreate,
    CSFDetailResponse,
    CSFUpdate,
)


def create_csf(db: Session, data: CSFCreate) -> CSF:
    """
    创建 CSF

    Args:
        db: 数据库会话
        data: 创建数据

    Returns:
        CSF: 创建的 CSF 对象
    """
    csf = CSF(
        strategy_id=data.strategy_id,
        dimension=data.dimension,
        code=data.code,
        name=data.name,
        description=data.description,
        derivation_method=data.derivation_method,
        weight=data.weight,
        sort_order=data.sort_order,
        owner_dept_id=data.owner_dept_id,
        owner_user_id=data.owner_user_id,
    )
    db.add(csf)
    db.commit()
    db.refresh(csf)
    return csf


def get_csf(db: Session, csf_id: int) -> Optional[CSF]:
    """
    获取 CSF

    Args:
        db: 数据库会话
        csf_id: CSF ID

    Returns:
        Optional[CSF]: CSF 对象
    """
    return db.query(CSF).filter(
        CSF.id == csf_id,
        CSF.is_active == True
    ).first()


def list_csfs(
    db: Session,
    strategy_id: int,
    dimension: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[CSF], int]:
    """
    获取 CSF 列表

    Args:
        db: 数据库会话
        strategy_id: 战略 ID
        dimension: 维度筛选
        skip: 跳过数量
        limit: 限制数量

    Returns:
        tuple: (CSF 列表, 总数)
    """
    query = db.query(CSF).filter(
        CSF.strategy_id == strategy_id,
        CSF.is_active == True
    )

    if dimension:
        query = query.filter(CSF.dimension == dimension)

    total = query.count()
    items = query.order_by(CSF.dimension, CSF.sort_order).offset(skip).limit(limit).all()

    return items, total


def update_csf(db: Session, csf_id: int, data: CSFUpdate) -> Optional[CSF]:
    """
    更新 CSF

    Args:
        db: 数据库会话
        csf_id: CSF ID
        data: 更新数据

    Returns:
        Optional[CSF]: 更新后的 CSF 对象
    """
    csf = get_csf(db, csf_id)
    if not csf:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(csf, key, value)

    db.commit()
    db.refresh(csf)
    return csf


def delete_csf(db: Session, csf_id: int) -> bool:
    """
    删除 CSF（软删除）

    Args:
        db: 数据库会话
        csf_id: CSF ID

    Returns:
        bool: 是否删除成功
    """
    csf = get_csf(db, csf_id)
    if not csf:
        return False

    csf.is_active = False
    db.commit()
    return True


def get_csf_detail(db: Session, csf_id: int) -> Optional[CSFDetailResponse]:
    """
    获取 CSF 详情（包含健康度）

    Args:
        db: 数据库会话
        csf_id: CSF ID

    Returns:
        Optional[CSFDetailResponse]: CSF 详情
    """
    csf = get_csf(db, csf_id)
    if not csf:
        return None

    # 统计 KPI 和重点工作数量
    kpi_count = db.query(KPI).filter(
        KPI.csf_id == csf_id,
        KPI.is_active == True
    ).count()

    annual_work_count = db.query(AnnualKeyWork).filter(
        AnnualKeyWork.csf_id == csf_id,
        AnnualKeyWork.is_active == True
    ).count()

    # 获取健康度
    from .health_calculator import calculate_csf_health
    health_data = calculate_csf_health(db, csf_id)

    # 获取责任人和部门名称
    owner_name = None
    owner_dept_name = None

    if csf.owner_user_id:
        from app.models.user import User
        user = db.query(User).filter(User.id == csf.owner_user_id).first()
        if user:
            owner_name = user.name

    if csf.owner_dept_id:
        from app.models.organization import Department
        dept = db.query(Department).filter(Department.id == csf.owner_dept_id).first()
        if dept:
            owner_dept_name = dept.name

    return CSFDetailResponse(
        id=csf.id,
        strategy_id=csf.strategy_id,
        dimension=csf.dimension,
        code=csf.code,
        name=csf.name,
        description=csf.description,
        derivation_method=csf.derivation_method,
        weight=csf.weight,
        sort_order=csf.sort_order,
        owner_dept_id=csf.owner_dept_id,
        owner_user_id=csf.owner_user_id,
        is_active=csf.is_active,
        created_at=csf.created_at,
        updated_at=csf.updated_at,
        owner_name=owner_name,
        owner_dept_name=owner_dept_name,
        kpi_count=kpi_count,
        annual_work_count=annual_work_count,
        health_score=health_data.get("score"),
        health_level=health_data.get("level"),
        kpi_completion_rate=health_data.get("kpi_completion_rate"),
    )


def get_csfs_by_dimension(db: Session, strategy_id: int) -> List[CSFByDimensionResponse]:
    """
    按维度分组获取 CSF

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        List[CSFByDimensionResponse]: 按维度分组的 CSF 列表
    """
    from .health_calculator import calculate_csf_health

    dimension_names = {
        "FINANCIAL": "财务维度",
        "CUSTOMER": "客户维度",
        "INTERNAL": "内部运营维度",
        "LEARNING": "学习成长维度",
    }

    result = []
    for dim_code, dim_name in dimension_names.items():
        csfs = db.query(CSF).filter(
            CSF.strategy_id == strategy_id,
            CSF.dimension == dim_code,
            CSF.is_active == True
        ).order_by(CSF.sort_order).all()

        csf_items = []
        total_weight = 0
        total_health = 0
        valid_count = 0

        for csf in csfs:
            kpi_count = db.query(KPI).filter(
                KPI.csf_id == csf.id,
                KPI.is_active == True
            ).count()

            health_data = calculate_csf_health(db, csf.id)

            csf_items.append(CSFByDimensionItem(
                id=csf.id,
                code=csf.code,
                name=csf.name,
                weight=float(csf.weight or 0),
                health_score=health_data.get("score"),
                kpi_count=kpi_count,
            ))

            total_weight += float(csf.weight or 0)
            if health_data.get("score") is not None:
                total_health += health_data["score"]
                valid_count += 1

        avg_health = total_health / valid_count if valid_count > 0 else None

        result.append(CSFByDimensionResponse(
            dimension=dim_code,
            dimension_name=dim_name,
            csfs=csf_items,
            total_weight=total_weight,
            avg_health_score=avg_health,
        ))

    return result


def batch_create_csfs(
    db: Session,
    strategy_id: int,
    items: List[CSFCreate]
) -> List[CSF]:
    """
    批量创建 CSF

    Args:
        db: 数据库会话
        strategy_id: 战略 ID
        items: CSF 创建数据列表

    Returns:
        List[CSF]: 创建的 CSF 列表
    """
    created = []
    for item in items:
        item.strategy_id = strategy_id
        csf = create_csf(db, item)
        created.append(csf)
    return created
