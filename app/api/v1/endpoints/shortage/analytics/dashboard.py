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

重构说明:
- 业务逻辑已提取到 app/services/shortage_analytics/ShortageAnalyticsService
- 本文件仅作为薄 controller 层
"""
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.dashboard.base import BaseDashboardEndpoint
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.shortage_analytics import ShortageAnalyticsService


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
    
    def get_dashboard_data(
        self,
        db: Session,
        current_user: User,
        project_id: Optional[int] = None
    ) -> dict[str, Any]:
        """
        获取缺料看板数据（通过服务层）
        
        Args:
            db: 数据库会话
            current_user: 当前用户
            project_id: 项目ID筛选
            
        Returns:
            缺料看板数据
        """
        service = ShortageAnalyticsService(db)
        data = service.get_dashboard_data(project_id)
        
        # 为基类 dashboard 格式添加统计卡片
        stats = [
            self.create_stat_card(
                key="total_reports",
                label="缺料上报总数",
                value=data["reports"]["total"],
                unit="个",
                icon="report"
            ),
            self.create_stat_card(
                key="urgent_reports",
                label="紧急缺料",
                value=data["reports"]["urgent"],
                unit="个",
                icon="urgent",
                color="danger"
            ),
            self.create_stat_card(
                key="unresolved_alerts",
                label="未解决预警",
                value=data["alerts"]["unresolved"],
                unit="个",
                icon="alert",
                color="warning"
            ),
            self.create_stat_card(
                key="critical_alerts",
                label="严重预警",
                value=data["alerts"]["critical"],
                unit="个",
                icon="critical",
                color="danger"
            ),
            self.create_stat_card(
                key="pending_arrivals",
                label="待处理到货",
                value=data["arrivals"]["pending"],
                unit="个",
                icon="arrival",
                color="warning"
            ),
            self.create_stat_card(
                key="delayed_arrivals",
                label="延迟到货",
                value=data["arrivals"]["delayed"],
                unit="个",
                icon="delayed",
                color="danger"
            ),
        ]
        
        # 转换 recent_reports 为列表项格式
        recent_reports_list = []
        for report in data["recent_reports"]:
            recent_reports_list.append(
                self.create_list_item(
                    id=report["id"],
                    title=f"{report['material_name']} - 缺料数量: {report['shortage_qty']}",
                    subtitle=f"项目: {report['project_name'] or '未知'} | 状态: {report['status']}",
                    status=report["status"].lower(),
                    priority=report["urgent_level"].lower() if report["urgent_level"] else None,
                    extra=report
                )
            )
        
        return {
            "stats": stats,
            **data,
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
    service = ShortageAnalyticsService(db)
    data = service.get_daily_report(report_date, project_id)
    
    return ResponseModel(
        code=200,
        message="success",
        data=data
    )


@router.get("/daily-report/latest", response_model=ResponseModel)
def get_latest_daily_report(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最新缺料日报（定时预生成的数据）
    """
    service = ShortageAnalyticsService(db)
    data = service.get_latest_daily_report()
    
    if not data:
        return ResponseModel(code=200, message="暂无日报数据", data=None)
    
    return ResponseModel(code=200, message="success", data=data)


@router.get("/daily-report/by-date", response_model=ResponseModel)
def get_daily_report_by_date(
    db: Session = Depends(deps.get_db),
    report_date: date = Query(..., description="报表日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    按日期获取缺料日报（定时预生成的数据）
    """
    service = ShortageAnalyticsService(db)
    data = service.get_daily_report_by_date(report_date)
    
    if not data:
        raise HTTPException(status_code=404, detail="指定日期不存在缺料日报")
    
    return ResponseModel(code=200, message="success", data=data)


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
    service = ShortageAnalyticsService(db)
    data = service.get_shortage_trends(days, project_id)
    
    return ResponseModel(
        code=200,
        message="success",
        data=data
    )
