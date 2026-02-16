# -*- coding: utf-8 -*-
"""
KPI数据采集器 - 模块采集器
"""
from decimal import Decimal
from typing import Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from .registry import register_collector


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

    query = db.query(Project).filter(Project.is_active)

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

    支持的指标：
    - CONTRACT_TOTAL_AMOUNT: 合同总金额
    - CONTRACT_RECEIVED_AMOUNT: 已收款金额
    - PROJECT_COST_TOTAL: 项目成本总计
    - PROJECT_PROFIT_MARGIN: 项目利润率
    - RECEIVABLE_OVERDUE_AMOUNT: 逾期应收款金额
    - RECEIVABLE_OVERDUE_COUNT: 逾期应收款笔数

    Args:
        db: 数据库会话
        metric: 指标名称
        filters: 筛选条件 (year, project_id, customer_id)
        aggregation: 聚合方式

    Returns:
        Optional[Decimal]: 采集到的值
    """
    from datetime import date
    from app.models.sales.contracts import Contract
    from app.models.project.financial import ProjectCost, ProjectPaymentPlan

    filters = filters or {}

    if metric == "CONTRACT_TOTAL_AMOUNT":
        # 合同总金额
        query = db.query(func.sum(Contract.contract_amount))
        if "year" in filters:
            query = query.filter(func.year(Contract.signed_date) == filters["year"])
        if "customer_id" in filters:
            query = query.filter(Contract.customer_id == filters["customer_id"])
        result = query.scalar()
        return Decimal(str(result or 0))

    elif metric == "CONTRACT_RECEIVED_AMOUNT":
        # 已收款金额（从收款计划中统计）
        query = db.query(func.sum(ProjectPaymentPlan.actual_amount))
        if "year" in filters:
            query = query.filter(func.year(ProjectPaymentPlan.actual_date) == filters["year"])
        if "project_id" in filters:
            query = query.filter(ProjectPaymentPlan.project_id == filters["project_id"])
        result = query.scalar()
        return Decimal(str(result or 0))

    elif metric == "PROJECT_COST_TOTAL":
        # 项目成本总计
        query = db.query(func.sum(ProjectCost.amount))
        if "year" in filters:
            query = query.filter(func.year(ProjectCost.cost_date) == filters["year"])
        if "project_id" in filters:
            query = query.filter(ProjectCost.project_id == filters["project_id"])
        result = query.scalar()
        return Decimal(str(result or 0))

    elif metric == "PROJECT_PROFIT_MARGIN":
        # 项目利润率 = (合同金额 - 成本) / 合同金额 * 100
        from app.models.project import Project
        project_id = filters.get("project_id")
        if not project_id:
            return None
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.contract_amount:
            return None
        total_cost = db.query(func.sum(ProjectCost.amount)).filter(
            ProjectCost.project_id == project_id
        ).scalar() or 0
        contract_amount = float(project.contract_amount)
        if contract_amount == 0:
            return Decimal(0)
        profit_margin = (contract_amount - float(total_cost)) / contract_amount * 100
        return Decimal(str(round(profit_margin, 2)))

    elif metric == "RECEIVABLE_OVERDUE_AMOUNT":
        # 逾期应收款金额
        today = date.today()
        query = db.query(
            func.sum(ProjectPaymentPlan.planned_amount - ProjectPaymentPlan.actual_amount)
        ).filter(
            ProjectPaymentPlan.planned_date < today,
            ProjectPaymentPlan.status.in_(["PENDING", "PARTIAL"])
        )
        if "project_id" in filters:
            query = query.filter(ProjectPaymentPlan.project_id == filters["project_id"])
        result = query.scalar()
        return Decimal(str(result or 0))

    elif metric == "RECEIVABLE_OVERDUE_COUNT":
        # 逾期应收款笔数
        today = date.today()
        query = db.query(func.count(ProjectPaymentPlan.id)).filter(
            ProjectPaymentPlan.planned_date < today,
            ProjectPaymentPlan.status.in_(["PENDING", "PARTIAL"])
        )
        if "project_id" in filters:
            query = query.filter(ProjectPaymentPlan.project_id == filters["project_id"])
        result = query.scalar()
        return Decimal(result or 0)

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

    query = db.query(PurchaseOrder).filter(PurchaseOrder.is_active)

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

    支持的指标：
    - EMPLOYEE_COUNT: 员工总数
    - EMPLOYEE_ACTIVE_COUNT: 在职员工数
    - EMPLOYEE_RESIGNED_COUNT: 离职员工数
    - EMPLOYEE_TURNOVER_RATE: 离职率
    - EMPLOYEE_PROBATION_COUNT: 试用期员工数
    - EMPLOYEE_CONFIRMATION_RATE: 转正率

    Args:
        db: 数据库会话
        metric: 指标名称
        filters: 筛选条件 (department_id, year)
        aggregation: 聚合方式

    Returns:
        Optional[Decimal]: 采集到的值
    """
    from app.models.user import User
    from app.models.organization import Employee, EmployeeHrProfile

    filters = filters or {}

    if metric == "EMPLOYEE_COUNT":
        # 员工总数
        query = db.query(func.count(Employee.id))
        if "department_id" in filters:
            query = query.join(User, User.employee_id == Employee.id).filter(
                User.department_id == filters["department_id"]
            )
        result = query.scalar()
        return Decimal(result or 0)

    elif metric == "EMPLOYEE_ACTIVE_COUNT":
        # 在职员工数
        query = db.query(func.count(Employee.id)).filter(
            Employee.employment_status == "active"
        )
        if "department_id" in filters:
            query = query.join(User, User.employee_id == Employee.id).filter(
                User.department_id == filters["department_id"]
            )
        result = query.scalar()
        return Decimal(result or 0)

    elif metric == "EMPLOYEE_RESIGNED_COUNT":
        # 离职员工数
        query = db.query(func.count(Employee.id)).filter(
            Employee.employment_status == "resigned"
        )
        if "year" in filters:
            query = query.join(
                EmployeeHrProfile, EmployeeHrProfile.employee_id == Employee.id
            ).filter(func.year(EmployeeHrProfile.resignation_date) == filters["year"])
        result = query.scalar()
        return Decimal(result or 0)

    elif metric == "EMPLOYEE_TURNOVER_RATE":
        # 离职率 = 离职人数 / 总员工数 * 100
        total_query = db.query(func.count(Employee.id))
        if "department_id" in filters:
            total_query = total_query.join(User, User.employee_id == Employee.id).filter(
                User.department_id == filters["department_id"]
            )
        total = total_query.scalar() or 0
        if total == 0:
            return Decimal(0)

        resigned_query = db.query(func.count(Employee.id)).filter(
            Employee.employment_status == "resigned"
        )
        if "year" in filters:
            resigned_query = resigned_query.join(
                EmployeeHrProfile, EmployeeHrProfile.employee_id == Employee.id
            ).filter(func.year(EmployeeHrProfile.resignation_date) == filters["year"])
        resigned = resigned_query.scalar() or 0

        turnover_rate = resigned / total * 100
        return Decimal(str(round(turnover_rate, 2)))

    elif metric == "EMPLOYEE_PROBATION_COUNT":
        # 试用期员工数
        query = db.query(func.count(Employee.id)).filter(
            Employee.employment_type == "probation",
            Employee.employment_status == "active"
        )
        result = query.scalar()
        return Decimal(result or 0)

    elif metric == "EMPLOYEE_CONFIRMATION_RATE":
        # 转正率 = 已转正人数 / (已转正 + 试用期离职) * 100
        confirmed = db.query(func.count(EmployeeHrProfile.id)).filter(
            EmployeeHrProfile.is_confirmed
        ).scalar() or 0

        # 试用期离职（简化：employment_type仍为probation且状态为resigned）
        probation_resigned = db.query(func.count(Employee.id)).filter(
            Employee.employment_type == "probation",
            Employee.employment_status == "resigned"
        ).scalar() or 0

        total = confirmed + probation_resigned
        if total == 0:
            return Decimal(100)  # 没有试用期数据，默认100%

        confirmation_rate = confirmed / total * 100
        return Decimal(str(round(confirmation_rate, 2)))

    return None
