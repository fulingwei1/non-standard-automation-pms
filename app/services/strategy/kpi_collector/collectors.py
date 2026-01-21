# -*- coding: utf-8 -*-
"""
KPI数据采集器 - 模块采集器
"""
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from .registry import get_collector, register_collector


@register_collector("PROJECT")
def collect_project_metrics(
    db: Session,
    metric: str,
    filters: Optional[Dict] = None,
    aggregation: str = "COUNT"
) -> Optional[Decimal]:
    """
    采集项目模块指标

    Args:
        db: 数据库会话
        metric: 指标名称
        filters: 筛选条件
        aggregation: 聚合方式

    Returns:
        Optional[Decimal]: 采集到的值
    """
    from app.models.project import Project

    filters = filters or {}

    query = db.query(Project).filter(Project.is_active == True)

    # 应用筛选条件
    if "status" in filters:
        query = query.filter(Project.status == filters["status"])
    if "year" in filters:
        query = query.filter(func.year(Project.created_at) == filters["year"])
    if "health_status" in filters:
        query = query.filter(Project.health_status == filters["health_status"])

    if metric == "PROJECT_COUNT":
        # 项目数量
        return Decimal(query.count())

    elif metric == "PROJECT_COMPLETION_RATE":
        # 项目完成率
        total = query.count()
        if total == 0:
            return Decimal(0)
        completed = query.filter(Project.status == "COMPLETED").count()
        return Decimal(str(completed / total * 100))

    elif metric == "PROJECT_ON_TIME_RATE":
        # 项目按时完成率
        completed = query.filter(Project.status == "COMPLETED").all()
        if not completed:
            return Decimal(0)
        on_time = sum(1 for p in completed if p.actual_end_date and p.planned_end_date
                      and p.actual_end_date <= p.planned_end_date)
        return Decimal(str(on_time / len(completed) * 100))

    elif metric == "PROJECT_HEALTH_RATE":
        # 项目健康率（H1 占比）
        total = query.count()
        if total == 0:
            return Decimal(0)
        healthy = query.filter(Project.health_status == "H1").count()
        return Decimal(str(healthy / total * 100))

    elif metric == "PROJECT_TOTAL_VALUE":
        # 项目总金额
        result = query.with_entities(func.sum(Project.contract_amount)).scalar()
        return Decimal(str(result or 0))

    return None


@register_collector("FINANCE")
def collect_finance_metrics(
    db: Session,
    metric: str,
    filters: Optional[Dict] = None,
    aggregation: str = "SUM"
) -> Optional[Decimal]:
    """
    采集财务模块指标

    Args:
        db: 数据库会话
        metric: 指标名称
        filters: 筛选条件
        aggregation: 聚合方式

    Returns:
        Optional[Decimal]: 采集到的值
    """
    # 财务模块待实现，返回模拟数据
    # TODO: 集成真实财务模块
    return None


@register_collector("PURCHASE")
def collect_purchase_metrics(
    db: Session,
    metric: str,
    filters: Optional[Dict] = None,
    aggregation: str = "SUM"
) -> Optional[Decimal]:
    """
    采集采购模块指标

    Args:
        db: 数据库会话
        metric: 指标名称
        filters: 筛选条件
        aggregation: 聚合方式

    Returns:
        Optional[Decimal]: 采集到的值
    """
    from app.models.purchase import PurchaseOrder

    filters = filters or {}

    query = db.query(PurchaseOrder).filter(PurchaseOrder.is_active == True)

    # 应用筛选条件
    if "year" in filters:
        query = query.filter(func.year(PurchaseOrder.created_at) == filters["year"])
    if "status" in filters:
        query = query.filter(PurchaseOrder.status == filters["status"])

    if metric == "PO_COUNT":
        # 采购订单数量
        return Decimal(query.count())

    elif metric == "PO_TOTAL_AMOUNT":
        # 采购总金额
        result = query.with_entities(func.sum(PurchaseOrder.total_amount)).scalar()
        return Decimal(str(result or 0))

    elif metric == "PO_ON_TIME_RATE":
        # 采购按时到货率
        delivered = query.filter(PurchaseOrder.status == "DELIVERED").all()
        if not delivered:
            return Decimal(0)
        on_time = sum(1 for po in delivered if po.actual_delivery_date and po.expected_delivery_date
                      and po.actual_delivery_date <= po.expected_delivery_date)
        return Decimal(str(on_time / len(delivered) * 100))

    return None


@register_collector("HR")
def collect_hr_metrics(
    db: Session,
    metric: str,
    filters: Optional[Dict] = None,
    aggregation: str = "COUNT"
) -> Optional[Decimal]:
    """
    采集人力资源模块指标

    Args:
        db: 数据库会话
        metric: 指标名称
        filters: 筛选条件
        aggregation: 聚合方式

    Returns:
        Optional[Decimal]: 采集到的值
    """
    from app.models.user import User

    filters = filters or {}

    query = db.query(User).filter(User.is_active == True)

    # 应用筛选条件
    if "department_id" in filters:
        query = query.filter(User.department_id == filters["department_id"])

    if metric == "EMPLOYEE_COUNT":
        # 员工数量
        return Decimal(query.count())

    elif metric == "EMPLOYEE_TURNOVER_RATE":
        # 离职率（需要离职记录表，暂时返回模拟数据）
        # TODO: 集成离职记录
        return None

    return None
