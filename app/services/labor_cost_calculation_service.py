# -*- coding: utf-8 -*-
"""
人工成本计算辅助服务
"""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.project import Project, ProjectCost
from app.models.timesheet import Timesheet

# LaborCostService 延迟导入，避免循环依赖


def query_approved_timesheets(
    db: Session,
    project_id: int,
    start_date: Optional[date],
    end_date: Optional[date]
) -> List[Timesheet]:
    """
    查询已审批的工时记录

    Returns:
        List[Timesheet]: 工时记录列表
    """
    query = db.query(Timesheet).filter(
        Timesheet.project_id == project_id,
        Timesheet.status == "APPROVED"
    )

    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)

    return query.all()


def delete_existing_costs(
    db: Session,
    project: Project,
    project_id: int
) -> None:
    """
    删除现有的工时成本记录
    """
    existing_costs = db.query(ProjectCost).filter(
        ProjectCost.project_id == project_id,
        ProjectCost.source_module == "TIMESHEET",
        ProjectCost.source_type == "LABOR_COST"
    ).all()

    for cost in existing_costs:
        # 更新项目实际成本
        project.actual_cost = max(0, (project.actual_cost or 0) - float(cost.amount))
        db.delete(cost)


def group_timesheets_by_user(timesheets: List[Timesheet]) -> Dict[int, Dict]:
    """
    按用户分组工时记录

    Returns:
        Dict[int, Dict]: 用户ID到用户数据的映射
    """
    user_costs: Dict[int, Dict] = {}

    for ts in timesheets:
        user_id = ts.user_id
        if user_id not in user_costs:
            user_costs[user_id] = {
                "user_id": user_id,
                "user_name": ts.user_name,
                "total_hours": Decimal("0"),
                "timesheet_ids": [],
                "cost_amount": Decimal("0"),
                "work_date": ts.work_date
            }

        hours = Decimal(str(ts.hours or 0))
        user_costs[user_id]["total_hours"] += hours
        user_costs[user_id]["timesheet_ids"].append(ts.id)

        # 更新工作日期（使用最新的日期）
        if ts.work_date:
            user_costs[user_id]["work_date"] = ts.work_date

    return user_costs


def find_existing_cost(
    db: Session,
    project_id: int,
    user_id: int
) -> Optional[ProjectCost]:
    """
    查找现有的成本记录

    Returns:
        Optional[ProjectCost]: 现有成本记录
    """
    return db.query(ProjectCost).filter(
        ProjectCost.project_id == project_id,
        ProjectCost.source_module == "TIMESHEET",
        ProjectCost.source_type == "LABOR_COST",
        ProjectCost.source_id == user_id
    ).first()


def update_existing_cost(
    db: Session,
    project: Project,
    existing_cost: ProjectCost,
    cost_amount: Decimal,
    user_data: Dict,
    end_date: Optional[date]
) -> None:
    """
    更新现有成本记录
    """
    old_amount = existing_cost.amount
    existing_cost.amount = cost_amount
    existing_cost.cost_date = end_date or date.today()
    existing_cost.description = f"人工成本：{user_data['user_name']}，工时：{user_data['total_hours']}小时"

    # 更新项目实际成本
    project.actual_cost = (project.actual_cost or 0) - float(old_amount) + float(cost_amount)

    db.add(existing_cost)


def create_new_cost(
    db: Session,
    project: Project,
    project_id: int,
    user_id: int,
    cost_amount: Decimal,
    user_data: Dict,
    end_date: Optional[date]
) -> ProjectCost:
    """
    创建新的成本记录

    Returns:
        ProjectCost: 新创建的成本记录
    """
    cost = ProjectCost(
        project_id=project_id,
        cost_type="LABOR",
        cost_category="LABOR",
        source_module="TIMESHEET",
        source_type="LABOR_COST",
        source_id=user_id,
        source_no=f"LABOR-{user_id}-{date.today().strftime('%Y%m%d')}",
        amount=cost_amount,
        tax_amount=Decimal("0"),
        cost_date=end_date or date.today(),
        description=f"人工成本：{user_data['user_name']}，工时：{user_data['total_hours']}小时",
        created_by=None
    )
    db.add(cost)

    # 更新项目实际成本
    project.actual_cost = (project.actual_cost or 0) + float(cost_amount)

    return cost


def check_budget_alert(
    db: Session,
    project_id: int,
    user_id: int
) -> None:
    """
    检查预算执行情况并生成预警
    """
    try:
        from app.services.cost_alert_service import CostAlertService
        CostAlertService.check_budget_execution(
            db, project_id, trigger_source="TIMESHEET", source_id=user_id
        )
    except Exception as e:
        import logging
        logging.warning(f"成本预警检查失败：{str(e)}")


def process_user_costs(
    db: Session,
    project: Project,
    project_id: int,
    user_costs: Dict[int, Dict],
    end_date: Optional[date],
    recalculate: bool
) -> tuple[List[ProjectCost], Decimal]:
    """
    处理用户成本

    Returns:
        Tuple[List[ProjectCost], Decimal]: (创建的成本记录列表, 总成本)
    """
    # 延迟导入，避免循环依赖
    from app.services.labor_cost_service import LaborCostService

    created_costs = []
    total_cost = Decimal("0")

    for user_id, user_data in user_costs.items():
        # 获取用户时���
        work_date = user_data.get("work_date") or end_date or date.today()
        hourly_rate = LaborCostService.get_user_hourly_rate(db, user_id, work_date)

        # 计算成本金额
        cost_amount = user_data["total_hours"] * hourly_rate

        # 检查是否已存在该用户的成本记录
        existing_cost = None
        if not recalculate:
            existing_cost = find_existing_cost(db, project_id, user_id)

        if existing_cost:
            # 更新现有成本记录
            update_existing_cost(db, project, existing_cost, cost_amount, user_data, end_date)
            created_costs.append(existing_cost)

            # 检查预算预警
            check_budget_alert(db, project_id, user_id)
        else:
            # 创建新的成本记录
            cost = create_new_cost(db, project, project_id, user_id, cost_amount, user_data, end_date)
            created_costs.append(cost)

            # 检查预算预警
            check_budget_alert(db, project_id, user_id)

        total_cost += cost_amount

    return created_costs, total_cost
