# -*- coding: utf-8 -*-
"""
看板报表 - dashboard.py

合并来源:
- app/api/v1/endpoints/shortage/statistics_dashboard.py
- app/api/v1/endpoints/shortage/statistics_daily_report.py
- app/api/v1/endpoints/shortage_alerts/statistics.py (dashboard, daily-report)

路由:
- GET    /dashboard                 缺料看板
- GET    /daily-report              日报（实时计算）
- GET    /daily-report/latest       最新日报（预生成）
- GET    /daily-report/by-date      按日期获取日报
- GET    /trends                    趋势分析
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.dashboard.base import BaseDashboardEndpoint
from app.core import security
from app.models.material import MaterialShortage
from app.models.project import Project
from app.models.shortage import (
    MaterialArrival,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageDailyReport,
    ShortageReport,
)
from app.models.user import User
from app.schemas.common import ResponseModel


# ============================================================
# 辅助函数
# ============================================================

def _build_shortage_daily_report(report: ShortageDailyReport) -> Dict[str, Any]:
    """序列化缺料日报（预生成的数据）"""
    return {
        "date": report.report_date.isoformat(),
        "alerts": {
            "new": report.new_alerts,
            "resolved": report.resolved_alerts,
            "pending": report.pending_alerts,
            "overdue": report.overdue_alerts,
            "levels": {
                "level1": report.level1_count,
                "level2": report.level2_count,
                "level3": report.level3_count,
                "level4": report.level4_count,
            }
        },
        "reports": {
            "new": report.new_reports,
            "resolved": report.resolved_reports,
        },
        "kit": {
            "total_work_orders": report.total_work_orders,
            "complete_count": report.kit_complete_count,
            "kit_rate": float(report.kit_rate) if report.kit_rate else 0.0,
        },
        "arrivals": {
            "expected": report.expected_arrivals,
            "actual": report.actual_arrivals,
            "delayed": report.delayed_arrivals,
            "on_time_rate": float(report.on_time_rate) if report.on_time_rate else 0.0,
        },
        "response": {
            "avg_response_minutes": report.avg_response_minutes,
            "avg_resolve_hours": float(report.avg_resolve_hours) if report.avg_resolve_hours else 0.0,
        },
        "stoppage": {
            "count": report.stoppage_count,
            "hours": float(report.stoppage_hours) if report.stoppage_hours else 0.0,
        },
    }


# ============================================================
# 缺料看板
# ============================================================

class ShortageAnalyticsDashboardEndpoint(BaseDashboardEndpoint):
    """缺料分析Dashboard端点"""
    
    module_name = "shortage_analytics"
    permission_required = None  # 使用默认权限
    
    def __init__(self):
        """初始化路由，添加额外端点"""
        # 先创建router，不调用super().__init__()
        self.router = APIRouter()
        self._register_custom_routes()
    
    def _register_custom_routes(self):
        """注册自定义路由"""
        user_dependency = self._get_user_dependency()
        
        # 主dashboard端点
        async def dashboard_endpoint(
            db: Session = Depends(deps.get_db),
            project_id: Optional[int] = Query(None, description="项目ID筛选"),
            current_user: User = Depends(user_dependency),
        ):
            return self._get_dashboard_handler(db, current_user, project_id)
        
        self.router.add_api_route(
            "/dashboard",
            dashboard_endpoint,
            methods=["GET"],
            summary="缺料看板",
            response_model=ResponseModel
        )
        
        # 保留其他端点（daily-report, trends等）
        # 这些端点将在文件末尾注册
    
    def get_dashboard_data(
        self,
        db: Session,
        current_user: User,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        缺料看板
        综合展示缺料上报、到货跟踪、物料替代、物料调拨的状态
        """
        # === 缺料上报统计 (ShortageReport) ===
        report_query = db.query(ShortageReport)
        if project_id:
            report_query = report_query.filter(ShortageReport.project_id == project_id)

        total_reports = report_query.count()
        reported = report_query.filter(ShortageReport.status == 'REPORTED').count()
        confirmed = report_query.filter(ShortageReport.status == 'CONFIRMED').count()
        handling = report_query.filter(ShortageReport.status == 'HANDLING').count()
        resolved = report_query.filter(ShortageReport.status == 'RESOLVED').count()

        # 紧急缺料
        urgent_reports = report_query.filter(
            ShortageReport.urgent_level.in_(['URGENT', 'CRITICAL']),
            ShortageReport.status != 'RESOLVED'
        ).count()

        # === 系统检测的缺料预警 (MaterialShortage) ===
        alert_query = db.query(MaterialShortage)
        if project_id:
            alert_query = alert_query.filter(MaterialShortage.project_id == project_id)

        total_alerts = alert_query.count()
        unresolved_alerts = alert_query.filter(MaterialShortage.status != "RESOLVED").count()
        critical_alerts = alert_query.filter(
            MaterialShortage.alert_level == "CRITICAL",
            MaterialShortage.status != "RESOLVED"
        ).count()

        # === 到货跟踪统计 ===
        arrival_query = db.query(MaterialArrival)
        total_arrivals = arrival_query.count()
        pending_arrivals = arrival_query.filter(MaterialArrival.status == 'PENDING').count()
        delayed_arrivals = arrival_query.filter(MaterialArrival.is_delayed == True).count()

        # === 物料替代统计 ===
        sub_query = db.query(MaterialSubstitution)
        if project_id:
            sub_query = sub_query.filter(MaterialSubstitution.project_id == project_id)
        total_substitutions = sub_query.count()
        pending_substitutions = sub_query.filter(
            MaterialSubstitution.status.in_(['DRAFT', 'TECH_PENDING', 'PROD_PENDING'])
        ).count()

        # === 物料调拨统计 ===
        transfer_query = db.query(MaterialTransfer)
        if project_id:
            transfer_query = transfer_query.filter(
                (MaterialTransfer.from_project_id == project_id) |
                (MaterialTransfer.to_project_id == project_id)
            )
        total_transfers = transfer_query.count()
        pending_transfers = transfer_query.filter(
            MaterialTransfer.status.in_(['DRAFT', 'PENDING'])
        ).count()

        # === 最近缺料上报 ===
        recent_query = db.query(ShortageReport)
        if project_id:
            recent_query = recent_query.filter(ShortageReport.project_id == project_id)
        recent_reports = recent_query.order_by(desc(ShortageReport.created_at)).limit(10).all()

        recent_reports_list = []
        for report in recent_reports:
            project = db.query(Project).filter(Project.id == report.project_id).first()
            recent_reports_list.append(
                self.create_list_item(
                    id=report.id,
                    title=f"{report.material_name} - 缺料数量: {report.shortage_qty}",
                    subtitle=f"项目: {project.project_name if project else '未知'} | 状态: {report.status}",
                    status=report.status.lower(),
                    priority=report.urgent_level.lower() if report.urgent_level else None,
                    extra={
                        'report_no': report.report_no,
                        'project_id': report.project_id,
                        'project_name': project.project_name if project else None,
                        'material_name': report.material_name,
                        'shortage_qty': float(report.shortage_qty),
                        'urgent_level': report.urgent_level,
                        'report_time': str(report.report_time) if report.report_time else None,
                    }
                )
            )

        # 使用基类方法创建统计卡片
        stats = [
            self.create_stat_card(
                key="total_reports",
                label="缺料上报总数",
                value=total_reports,
                unit="个",
                icon="report"
            ),
            self.create_stat_card(
                key="urgent_reports",
                label="紧急缺料",
                value=urgent_reports,
                unit="个",
                icon="urgent",
                color="danger"
            ),
            self.create_stat_card(
                key="unresolved_alerts",
                label="未解决预警",
                value=unresolved_alerts,
                unit="个",
                icon="alert",
                color="warning"
            ),
            self.create_stat_card(
                key="critical_alerts",
                label="严重预警",
                value=critical_alerts,
                unit="个",
                icon="critical",
                color="danger"
            ),
            self.create_stat_card(
                key="pending_arrivals",
                label="待处理到货",
                value=pending_arrivals,
                unit="个",
                icon="arrival",
                color="warning"
            ),
            self.create_stat_card(
                key="delayed_arrivals",
                label="延迟到货",
                value=delayed_arrivals,
                unit="个",
                icon="delayed",
                color="danger"
            ),
        ]

        return {
            "stats": stats,
            "reports": {
                "total": total_reports,
                "reported": reported,
                "confirmed": confirmed,
                "handling": handling,
                "resolved": resolved,
                "urgent": urgent_reports
            },
            "alerts": {
                "total": total_alerts,
                "unresolved": unresolved_alerts,
                "critical": critical_alerts
            },
            "arrivals": {
                "total": total_arrivals,
                "pending": pending_arrivals,
                "delayed": delayed_arrivals
            },
            "substitutions": {
                "total": total_substitutions,
                "pending": pending_substitutions
            },
            "transfers": {
                "total": total_transfers,
                "pending": pending_transfers
            },
            "recent_reports": recent_reports_list
        }
    
    def _get_dashboard_handler(
        self,
        db: Session,
        current_user: User,
        project_id: Optional[int] = None
    ) -> ResponseModel:
        """Dashboard处理器，支持project_id参数"""
        try:
            data = self.get_dashboard_data(db, current_user, project_id)
            return ResponseModel(
                code=200,
                message="success",
                data=data
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取仪表板数据失败: {str(e)}"
            )


# 创建端点实例并获取路由
dashboard_endpoint = ShortageAnalyticsDashboardEndpoint()
router = dashboard_endpoint.router

# 注意：其他端点（daily-report, trends等）已经在文件末尾定义
# 它们使用 @router.get 装饰器，会自动注册到同一个router上


# ============================================================
# 缺料日报
# ============================================================

@router.get("/daily-report", response_model=ResponseModel)
def get_daily_report(
    db: Session = Depends(deps.get_db),
    report_date: Optional[date] = Query(None, description="报表日期（默认：今天）"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料日报（实时计算）
    按日期统计缺料上报情况
    """
    if not report_date:
        report_date = date.today()

    # 查询当日缺料上报
    query = db.query(ShortageReport).filter(
        func.date(ShortageReport.report_time) == report_date
    )
    if project_id:
        query = query.filter(ShortageReport.project_id == project_id)

    daily_reports = query.all()

    # 按紧急程度统计
    by_urgent: Dict[str, int] = {}
    for report in daily_reports:
        level = report.urgent_level
        by_urgent[level] = by_urgent.get(level, 0) + 1

    # 按状态统计
    by_status: Dict[str, int] = {}
    for report in daily_reports:
        status = report.status
        by_status[status] = by_status.get(status, 0) + 1

    # 按物料统计
    by_material: Dict[str, Dict[str, Any]] = {}
    for report in daily_reports:
        material_key = f"{report.material_id}_{report.material_name}"
        if material_key not in by_material:
            by_material[material_key] = {
                "material_id": report.material_id,
                "material_name": report.material_name,
                "count": 0,
                "total_shortage_qty": 0.0
            }
        by_material[material_key]["count"] += 1
        by_material[material_key]["total_shortage_qty"] += float(report.shortage_qty)

    # 按项目统计
    by_project: Dict[int, Dict[str, Any]] = {}
    for report in daily_reports:
        if report.project_id not in by_project:
            project = db.query(Project).filter(Project.id == report.project_id).first()
            by_project[report.project_id] = {
                "project_id": report.project_id,
                "project_name": project.project_name if project else None,
                "shortage_count": 0,
                "total_shortage_qty": Decimal("0"),
                "critical_count": 0
            }
        stats = by_project[report.project_id]
        stats["shortage_count"] += 1
        stats["total_shortage_qty"] += report.shortage_qty
        if report.urgent_level in ['URGENT', 'CRITICAL']:
            stats["critical_count"] += 1

    # 转换 Decimal 为 float
    project_list = []
    for stats in by_project.values():
        project_list.append({
            **stats,
            "total_shortage_qty": float(stats["total_shortage_qty"])
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "report_date": str(report_date),
            "total_reports": len(daily_reports),
            "by_urgent": by_urgent,
            "by_status": by_status,
            "by_material": list(by_material.values()),
            "by_project": project_list
        }
    )


@router.get("/daily-report/latest", response_model=ResponseModel)
def get_latest_daily_report(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最新缺料日报（定时预生成的数据）
    """
    latest_date = db.query(func.max(ShortageDailyReport.report_date)).scalar()
    if not latest_date:
        return ResponseModel(code=200, message="暂无日报数据", data=None)

    report = db.query(ShortageDailyReport).filter(
        ShortageDailyReport.report_date == latest_date
    ).first()

    if not report:
        return ResponseModel(code=200, message="暂无日报数据", data=None)

    return ResponseModel(code=200, message="success", data=_build_shortage_daily_report(report))


@router.get("/daily-report/by-date", response_model=ResponseModel)
def get_daily_report_by_date(
    db: Session = Depends(deps.get_db),
    report_date: date = Query(..., description="报表日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    按日期获取缺料日报（定时预生成的数据）
    """
    report = db.query(ShortageDailyReport).filter(
        ShortageDailyReport.report_date == report_date
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="指定日期不存在缺料日报")

    return ResponseModel(code=200, message="success", data=_build_shortage_daily_report(report))


# ============================================================
# 趋势分析
# ============================================================

@router.get("/trends", response_model=ResponseModel)
def get_shortage_trends(
    db: Session = Depends(deps.get_db),
    days: int = Query(30, ge=7, le=90, description="统计天数"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料趋势分析
    按天统计缺料数量的变化趋势
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # 按天统计缺料上报
    daily_stats = []
    current_date = start_date

    while current_date <= end_date:
        query = db.query(ShortageReport).filter(
            func.date(ShortageReport.report_time) == current_date
        )
        if project_id:
            query = query.filter(ShortageReport.project_id == project_id)

        new_count = query.count()
        resolved_count = db.query(ShortageReport).filter(
            func.date(ShortageReport.resolved_at) == current_date
        )
        if project_id:
            resolved_count = resolved_count.filter(ShortageReport.project_id == project_id)
        resolved_count = resolved_count.count()

        daily_stats.append({
            "date": str(current_date),
            "new": new_count,
            "resolved": resolved_count,
            "net": new_count - resolved_count
        })

        current_date += timedelta(days=1)

    # 计算汇总
    total_new = sum(d["new"] for d in daily_stats)
    total_resolved = sum(d["resolved"] for d in daily_stats)
    avg_daily_new = round(total_new / days, 2) if days > 0 else 0
    avg_daily_resolved = round(total_resolved / days, 2) if days > 0 else 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date), "days": days},
            "summary": {
                "total_new": total_new,
                "total_resolved": total_resolved,
                "avg_daily_new": avg_daily_new,
                "avg_daily_resolved": avg_daily_resolved
            },
            "daily": daily_stats
        }
    )
