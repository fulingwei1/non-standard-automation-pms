# -*- coding: utf-8 -*-
"""
生产管理模块 - 仪表板端点

提供生产统计数据概览
"""
from datetime import date, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.dashboard.base import BaseDashboardEndpoint
from app.common.date_range import get_month_range
from app.core import security
from app.models.production import ProductionDailyReport, WorkOrder, Workshop
from app.models.user import User
from app.schemas.common import ResponseModel


class ProductionDashboardEndpoint(BaseDashboardEndpoint):
    """生产管理Dashboard端点"""
    
    module_name = "production"
    permission_required = None  # 使用默认权限检查
    
    def get_dashboard_data(
        self,
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """
        获取生产仪表板数据
        返回产能利用率、质量合格率等关键指标
        """
        today = date.today()
        month_start, _ = get_month_range(today)

        # 统计车间数量
        workshop_count = db.query(func.count(Workshop.id)).filter(
            Workshop.is_active == True
        ).scalar() or 0

        # 统计本月工单
        work_order_stats = db.query(
            func.count(WorkOrder.id).label('total'),
            func.sum(case((WorkOrder.status == 'COMPLETED', 1), else_=0)).label('completed'),
            func.sum(case((WorkOrder.status == 'IN_PROGRESS', 1), else_=0)).label('in_progress'),
        ).filter(
            WorkOrder.created_at >= month_start
        ).first()

        total_orders = work_order_stats.total or 0
        completed_orders = work_order_stats.completed or 0
        in_progress_orders = work_order_stats.in_progress or 0

        # 计算产能利用率（简化计算：进行中+完成 / 总数）
        capacity_utilization = 0
        if total_orders > 0:
            capacity_utilization = round((completed_orders + in_progress_orders) / total_orders * 100, 1)

        # 获取最近的日报数据计算质量合格率
        recent_reports = db.query(ProductionDailyReport).filter(
            ProductionDailyReport.report_date >= today - timedelta(days=30)
        ).all()

        pass_rate = 95.0  # 默认值
        if recent_reports:
            total_produced = sum(r.produced_quantity or 0 for r in recent_reports)
            total_defects = sum(r.defect_quantity or 0 for r in recent_reports)
            if total_produced > 0:
                pass_rate = round((total_produced - total_defects) / total_produced * 100, 1)

        # 使用基类方法创建统计卡片
        stats = [
            self.create_stat_card(
                key="workshop_count",
                label="车间数量",
                value=workshop_count,
                unit="个",
                icon="workshop"
            ),
            self.create_stat_card(
                key="total_orders",
                label="本月工单",
                value=total_orders,
                unit="单",
                icon="order"
            ),
            self.create_stat_card(
                key="capacity_utilization",
                label="产能利用率",
                value=capacity_utilization,
                unit="%",
                icon="capacity"
            ),
            self.create_stat_card(
                key="pass_rate",
                label="质量合格率",
                value=pass_rate,
                unit="%",
                icon="quality"
            ),
        ]

        return {
            "stats": stats,
            "workshop_count": workshop_count,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "in_progress_orders": in_progress_orders,
            "capacity_utilization": capacity_utilization,
            "pass_rate": pass_rate,
            "on_time_delivery_rate": 90.0,  # 默认值，可从项目数据计算
        }


# 创建端点实例并获取路由
dashboard_endpoint = ProductionDashboardEndpoint()
router = dashboard_endpoint.router
