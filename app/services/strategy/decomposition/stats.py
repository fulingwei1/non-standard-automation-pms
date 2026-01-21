# -*- coding: utf-8 -*-
"""
分解统计分析

提供分解统计数据的查询
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
