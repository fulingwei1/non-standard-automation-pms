# -*- coding: utf-8 -*-
"""
战略管理服务 - 目标分解

实现从公司战略到部门目标到个人 KPI 的层层分解
"""

import json
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

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
    items = query.order_by(
        DepartmentObjective.department_id,
        DepartmentObjective.csf_id
    ).offset(skip).limit(limit).all()

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
        PersonalKPI.is_active == True
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
    query = db.query(PersonalKPI).filter(PersonalKPI.is_active == True)

    if user_id:
        query = query.filter(PersonalKPI.user_id == user_id)
    if dept_objective_id:
        query = query.filter(PersonalKPI.dept_objective_id == dept_objective_id)
    if year:
        query = query.filter(PersonalKPI.year == year)
    if period:
        query = query.filter(PersonalKPI.period == period)

    total = query.count()
    items = query.order_by(PersonalKPI.code).offset(skip).limit(limit).all()

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


# ============================================
# 分解追溯
# ============================================

def get_decomposition_tree(
    db: Session,
    strategy_id: int
) -> DecompositionTreeResponse:
    """
    获取分解树

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        DecompositionTreeResponse: 分解树数据
    """
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.is_active == True
    ).first()

    if not strategy:
        return DecompositionTreeResponse(
            strategy_id=strategy_id,
            strategy_name="",
            nodes=[],
        )

    nodes = []

    # 获取 CSF 节点
    csfs = db.query(CSF).filter(
        CSF.strategy_id == strategy_id,
        CSF.is_active == True
    ).order_by(CSF.dimension, CSF.sort_order).all()

    for csf in csfs:
        csf_node = DecompositionTreeNode(
            id=f"csf-{csf.id}",
            type="CSF",
            code=csf.code,
            name=csf.name,
            dimension=csf.dimension,
            children=[],
        )

        # 获取 KPI 子节点
        kpis = db.query(KPI).filter(
            KPI.csf_id == csf.id,
            KPI.is_active == True
        ).all()

        for kpi in kpis:
            kpi_node = DecompositionTreeNode(
                id=f"kpi-{kpi.id}",
                type="KPI",
                code=kpi.code,
                name=kpi.name,
                parent_id=f"csf-{csf.id}",
                children=[],
            )

            # 获取部门目标子节点
            dept_objs = db.query(DepartmentObjective).filter(
                DepartmentObjective.kpi_id == kpi.id,
                DepartmentObjective.is_active == True
            ).all()

            for obj in dept_objs:
                from app.models.organization import Department
                dept = db.query(Department).filter(Department.id == obj.department_id).first()
                dept_name = dept.name if dept else f"部门{obj.department_id}"

                obj_node = DecompositionTreeNode(
                    id=f"dept-{obj.id}",
                    type="DEPT_OBJ",
                    code=f"DO-{obj.id}",
                    name=f"{dept_name}目标",
                    parent_id=f"kpi-{kpi.id}",
                    children=[],
                )

                # 获取个人 KPI 子节点
                personal_kpis = db.query(PersonalKPI).filter(
                    PersonalKPI.dept_objective_id == obj.id,
                    PersonalKPI.is_active == True
                ).all()

                for pkpi in personal_kpis:
                    from app.models.user import User
                    user = db.query(User).filter(User.id == pkpi.user_id).first()
                    user_name = user.name if user else f"用户{pkpi.user_id}"

                    pkpi_node = DecompositionTreeNode(
                        id=f"pkpi-{pkpi.id}",
                        type="PERSONAL_KPI",
                        code=pkpi.code,
                        name=f"{user_name}: {pkpi.name}",
                        parent_id=f"dept-{obj.id}",
                        children=[],
                    )
                    obj_node.children.append(pkpi_node)

                kpi_node.children.append(obj_node)

            csf_node.children.append(kpi_node)

        nodes.append(csf_node)

    return DecompositionTreeResponse(
        strategy_id=strategy_id,
        strategy_name=strategy.name,
        nodes=nodes,
    )


def trace_to_strategy(
    db: Session,
    personal_kpi_id: int
) -> Optional[TraceToStrategyResponse]:
    """
    从个人 KPI 追溯到战略

    Args:
        db: 数据库会话
        personal_kpi_id: 个人 KPI ID

    Returns:
        Optional[TraceToStrategyResponse]: 追溯链路
    """
    pkpi = get_personal_kpi(db, personal_kpi_id)
    if not pkpi:
        return None

    # 获取用户信息
    from app.models.user import User
    user = db.query(User).filter(User.id == pkpi.user_id).first()
    user_name = user.name if user else None

    # 获取部门目标
    dept_obj = None
    dept_name = None
    if pkpi.dept_objective_id:
        dept_obj = db.query(DepartmentObjective).filter(
            DepartmentObjective.id == pkpi.dept_objective_id
        ).first()
        if dept_obj and dept_obj.department_id:
            from app.models.organization import Department
            dept = db.query(Department).filter(Department.id == dept_obj.department_id).first()
            dept_name = dept.name if dept else None

    # 获取公司 KPI
    company_kpi = None
    if pkpi.source_kpi_id:
        company_kpi = db.query(KPI).filter(KPI.id == pkpi.source_kpi_id).first()
    elif dept_obj and dept_obj.kpi_id:
        company_kpi = db.query(KPI).filter(KPI.id == dept_obj.kpi_id).first()

    # 获取 CSF
    csf = None
    if company_kpi:
        csf = db.query(CSF).filter(CSF.id == company_kpi.csf_id).first()

    # 获取战略
    strategy = None
    if csf:
        strategy = db.query(Strategy).filter(Strategy.id == csf.strategy_id).first()

    return TraceToStrategyResponse(
        personal_kpi_id=pkpi.id,
        personal_kpi_name=pkpi.name,
        user_id=pkpi.user_id,
        user_name=user_name,
        dept_objective_id=pkpi.dept_objective_id,
        department_name=dept_name,
        company_kpi_id=company_kpi.id if company_kpi else None,
        company_kpi_name=company_kpi.name if company_kpi else None,
        csf_id=csf.id if csf else None,
        csf_name=csf.name if csf else None,
        csf_dimension=csf.dimension if csf else None,
        strategy_id=strategy.id if strategy else None,
        strategy_name=strategy.name if strategy else None,
    )


# ============================================
# 统计分析
# ============================================

def get_decomposition_stats(
    db: Session,
    strategy_id: int,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    获取分解统计

    Args:
        db: 数据库会话
        strategy_id: 战略 ID
        year: 年度

    Returns:
        Dict: 统计数据
    """
    if year is None:
        year = date.today().year

    # 统计 CSF 数量
    csf_count = db.query(CSF).filter(
        CSF.strategy_id == strategy_id,
        CSF.is_active == True
    ).count()

    # 统计 KPI 数量
    kpi_count = db.query(KPI).join(CSF).filter(
        CSF.strategy_id == strategy_id,
        CSF.is_active == True,
        KPI.is_active == True
    ).count()

    # 统计部门目标数量
    dept_obj_count = db.query(DepartmentObjective).filter(
        DepartmentObjective.strategy_id == strategy_id,
        DepartmentObjective.year == year,
        DepartmentObjective.is_active == True
    ).count()

    # 统计个人 KPI 数量
    personal_kpi_count = db.query(PersonalKPI).join(DepartmentObjective).filter(
        DepartmentObjective.strategy_id == strategy_id,
        DepartmentObjective.year == year,
        DepartmentObjective.is_active == True,
        PersonalKPI.is_active == True
    ).count()

    # 统计各部门分解情况
    dept_stats: Dict[int, Dict[str, int]] = {}
    dept_objs = db.query(DepartmentObjective).filter(
        DepartmentObjective.strategy_id == strategy_id,
        DepartmentObjective.year == year,
        DepartmentObjective.is_active == True
    ).all()

    for obj in dept_objs:
        dept_id = obj.department_id
        if dept_id not in dept_stats:
            dept_stats[dept_id] = {"objectives": 0, "personal_kpis": 0}
        dept_stats[dept_id]["objectives"] += 1

        pkpi_count = db.query(PersonalKPI).filter(
            PersonalKPI.dept_objective_id == obj.id,
            PersonalKPI.is_active == True
        ).count()
        dept_stats[dept_id]["personal_kpis"] += pkpi_count

    return {
        "year": year,
        "csf_count": csf_count,
        "kpi_count": kpi_count,
        "dept_objective_count": dept_obj_count,
        "personal_kpi_count": personal_kpi_count,
        "decomposition_rate": personal_kpi_count / kpi_count * 100 if kpi_count > 0 else 0,
        "department_stats": dept_stats,
    }
