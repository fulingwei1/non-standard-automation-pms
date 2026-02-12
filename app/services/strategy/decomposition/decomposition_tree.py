# -*- coding: utf-8 -*-
"""
分解追溯

提供分解树查询和从个人 KPI 追溯到战略的功能
"""

"""
战略管理服务 - 目标分解

实现从公司战略到部门目标到个人 KPI 的层层分解
"""

from typing import Optional

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
    TraceToStrategyResponse,
)


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
        Strategy.is_active
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
        CSF.is_active
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
            KPI.is_active
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
                DepartmentObjective.is_active
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
                    PersonalKPI.is_active
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


