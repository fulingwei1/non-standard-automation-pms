# -*- coding: utf-8 -*-
"""
BI 报表 - 自动生成
从 report_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
报表中心 API endpoints
核心功能：多角色视角报表、智能生成、导出分享
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.outsourcing import OutsourcingOrder
from app.models.vendor import Vendor
from app.models.project import Project, ProjectPaymentPlan
from app.models.sales import Contract
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/bi",
    tags=["bi"]
)

# 共 5 个路由

# ==================== BI 报表 ====================

@router.get("/delivery-rate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_delivery_rate(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    交付准时率
    统计项目按计划交付的准时率
    """
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()

    # 获取在时间范围内的项目
    projects = db.query(Project).filter(
        Project.planned_end_date >= start_date,
        Project.planned_end_date <= end_date,
        Project.status.in_(["COMPLETED", "EXECUTING"])
    ).all()

    total_projects = len(projects)
    on_time_projects = 0
    delayed_projects = 0

    for project in projects:
        if project.actual_end_date and project.planned_end_date:
            if project.actual_end_date <= project.planned_end_date:
                on_time_projects += 1
            else:
                delayed_projects += 1

    on_time_rate = (on_time_projects / total_projects * 100) if total_projects > 0 else 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "total_projects": total_projects,
            "on_time_projects": on_time_projects,
            "delayed_projects": delayed_projects,
            "on_time_rate": round(on_time_rate, 2)
        }
    )


@router.get("/health-distribution", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_health_distribution(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    项目健康度分布
    统计各健康度等级的项目数量
    """
    health_stats = db.query(
        Project.health,
        func.count(Project.id).label('count')
    ).filter(
        Project.status != "CANCELLED"
    ).group_by(Project.health).all()

    distribution = {}
    total = 0
    for stat in health_stats:
        health = stat.health or "H4"
        count = stat.count or 0
        distribution[health] = count
        total += count

    # 计算百分比
    distribution_pct = {}
    for health, count in distribution.items():
        distribution_pct[health] = round(count / total * 100, 2) if total > 0 else 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_projects": total,
            "distribution": distribution,
            "distribution_percentage": distribution_pct
        }
    )


@router.get("/utilization", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_utilization(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    人员利用率
    统计人员的工时利用情况
    """
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    # 查询工时记录
    query = db.query(Timesheet).filter(
        Timesheet.work_date >= start_date,
        Timesheet.work_date <= end_date,
        Timesheet.status == "APPROVED"
    )

    if department_id:
        # 通过用户关联部门
        query = query.join(User).filter(User.department_id == department_id)

    timesheets = query.all()

    # 按用户统计
    user_hours = {}
    for ts in timesheets:
        user_id = ts.user_id
        if user_id not in user_hours:
            user_hours[user_id] = 0
        user_hours[user_id] += float(ts.hours or 0)

    # 计算标准工时（假设每天8小时，工作日）
    work_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # 周一到周五
            work_days += 1
        current += timedelta(days=1)

    standard_hours = work_days * 8

    utilization_data = []
    for user_id, hours in user_hours.items():
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            utilization_rate = (hours / standard_hours * 100) if standard_hours > 0 else 0
            utilization_data.append({
                "user_id": user_id,
                "user_name": user.real_name or user.username,
                "department": user.department,
                "total_hours": round(hours, 2),
                "standard_hours": standard_hours,
                "utilization_rate": round(utilization_rate, 2)
            })

    # 按利用率排序
    utilization_data.sort(key=lambda x: x["utilization_rate"], reverse=True)

    avg_utilization = sum([u["utilization_rate"] for u in utilization_data]) / len(utilization_data) if utilization_data else 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "total_users": len(utilization_data),
            "avg_utilization_rate": round(avg_utilization, 2),
            "utilization_list": utilization_data
        }
    )


@router.get("/supplier-performance", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_supplier_performance(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    供应商绩效
    统计供应商的交期、质量、价格等绩效指标
    """
    if not start_date:
        start_date = date.today() - timedelta(days=180)
    if not end_date:
        end_date = date.today()

    # 查询外协订单
    orders = db.query(OutsourcingOrder).filter(
        OutsourcingOrder.created_at >= start_date,
        OutsourcingOrder.created_at <= end_date
    ).all()

    # 按供应商统计
    vendor_stats = {}
    for order in orders:
        vendor_id = order.vendor_id
        if vendor_id not in vendor_stats:
            vendor = db.query(Vendor).filter(
                Vendor.id == vendor_id,
                Vendor.vendor_type == 'OUTSOURCING'
            ).first()
            vendor_stats[vendor_id] = {
                "vendor_id": vendor_id,
                "vendor_name": vendor.supplier_name if vendor else None,
                "vendor_code": vendor.supplier_code if vendor else None,
                "total_orders": 0,
                "total_amount": Decimal("0"),
                "on_time_deliveries": 0,
                "delayed_deliveries": 0,
                "quality_pass_rate": 0.0
            }

        stats = vendor_stats[vendor_id]
        stats["total_orders"] += 1
        stats["total_amount"] += order.total_amount or Decimal("0")

        # 检查交付情况
        from app.models.outsourcing import OutsourcingDelivery
        deliveries = db.query(OutsourcingDelivery).filter(
            OutsourcingDelivery.order_id == order.id
        ).all()

        for delivery in deliveries:
            if delivery.delivery_date and order.expected_delivery_date:
                if delivery.delivery_date <= order.expected_delivery_date:
                    stats["on_time_deliveries"] += 1
                else:
                    stats["delayed_deliveries"] += 1

        # 检查质检情况
        from app.models.outsourcing import OutsourcingInspection
        inspections = db.query(OutsourcingInspection).filter(
            OutsourcingInspection.order_id == order.id
        ).all()

        if inspections:
            pass_count = sum([1 for ins in inspections if ins.inspection_result == "PASS"])
            stats["quality_pass_rate"] = (pass_count / len(inspections) * 100) if inspections else 0

    # 计算准时率
    performance_list = []
    for vendor_id, stats in vendor_stats.items():
        total_deliveries = stats["on_time_deliveries"] + stats["delayed_deliveries"]
        on_time_rate = (stats["on_time_deliveries"] / total_deliveries * 100) if total_deliveries > 0 else 0

        performance_list.append({
            "vendor_id": stats["vendor_id"],
            "vendor_name": stats["vendor_name"],
            "vendor_code": stats["vendor_code"],
            "total_orders": stats["total_orders"],
            "total_amount": float(stats["total_amount"]),
            "on_time_rate": round(on_time_rate, 2),
            "quality_pass_rate": round(stats["quality_pass_rate"], 2),
            "performance_score": round((on_time_rate + stats["quality_pass_rate"]) / 2, 2)
        })

    # 按绩效得分排序
    performance_list.sort(key=lambda x: x["performance_score"], reverse=True)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "total_vendors": len(performance_list),
            "performance_list": performance_list
        }
    )


@router.get("/dashboard/executive", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_executive_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    决策驾驶舱数据
    综合看板数据，包括项目、销售、成本、进度等关键指标
    """
    today = date.today()
    month_start = date(today.year, today.month, 1)

    # 项目统计
    total_projects = db.query(Project).filter(Project.status != "CANCELLED").count()
    active_projects = db.query(Project).filter(Project.status == "EXECUTING").count()
    completed_projects = db.query(Project).filter(Project.status == "COMPLETED").count()

    # 健康度分布
    health_dist = db.query(
        Project.health,
        func.count(Project.id).label('count')
    ).filter(Project.status != "CANCELLED").group_by(Project.health).all()
    health_distribution = {stat.health or "H4": stat.count for stat in health_dist}

    # 销售统计（本月）- Contract.status 使用小写与模型一致
    month_contracts = db.query(Contract).filter(
        func.date(Contract.signing_date) >= month_start,
        Contract.status.in_(["signed", "executing"])
    ).all()
    month_contract_amount = sum([float(c.total_amount or 0) for c in month_contracts])

    # 成本统计
    total_budget = db.query(func.sum(Project.budget_amount)).scalar() or 0
    total_actual = db.query(func.sum(Project.actual_cost)).scalar() or 0

    # 合同统计 - 状态与模型一致（小写）
    total_contracts = db.query(Contract).filter(
        Contract.status.in_(["signed", "executing"])
    ).count()
    total_contract_amount = db.query(func.sum(Contract.total_amount)).filter(
        Contract.status.in_(["signed", "executing"])
    ).scalar() or 0

    # 回款统计：按实际收款金额汇总（ProjectPaymentPlan 状态为 COMPLETED/PARTIAL，无 PAID）
    total_received = db.query(func.sum(ProjectPaymentPlan.actual_amount)).filter(
        ProjectPaymentPlan.status.in_(["COMPLETED", "PARTIAL"])
    ).scalar() or 0

    # 人员统计
    total_users = db.query(User).filter(User.is_active).count()

    # 工时统计（本月）
    try:
        month_timesheets = db.query(Timesheet).filter(
            Timesheet.work_date >= month_start,
            Timesheet.status == "APPROVED"
        ).all()
        month_total_hours = sum([float(ts.hours or 0) for ts in month_timesheets])
    except Exception:
        month_total_hours = 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "summary": {
                "total_projects": total_projects,
                "active_projects": active_projects,
                "completed_projects": completed_projects,
                "total_contracts": total_contracts,
                "total_contract_amount": round(float(total_contract_amount), 2),
                "total_received": round(float(total_received), 2),
                "total_budget": round(float(total_budget), 2),
                "total_actual_cost": round(float(total_actual), 2),
                "total_users": total_users
            },
            "monthly": {
                "month": today.strftime("%Y-%m"),
                "new_contracts": len(month_contracts),
                "contract_amount": round(month_contract_amount, 2),
                "total_hours": round(month_total_hours, 2)
            },
            "health_distribution": health_distribution,
            "updated_at": datetime.now().isoformat()
        }
    )

