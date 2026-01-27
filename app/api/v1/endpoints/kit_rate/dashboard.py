# -*- coding: utf-8 -*-
"""
齐套率看板和趋势分析端点
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.dashboard.base import BaseDashboardEndpoint
from app.core import security
from app.schemas.common import ResponseModel
from app.services.kit_rate import KitRateService
from app.models.user import User


class KitRateDashboardEndpoint(BaseDashboardEndpoint):
    """齐套率Dashboard端点"""
    
    module_name = "kit-rate"
    permission_required = None  # 使用自定义权限检查
    
    def __init__(self):
        """初始化路由，添加额外端点"""
        # 先创建router，但不调用super().__init__()，因为需要覆盖主dashboard路由
        self.router = APIRouter()
        user_dependency = security.require_procurement_access()
        
        # 覆盖主dashboard路由，支持project_ids参数
        async def dashboard_endpoint(
            db: Session = Depends(deps.get_db),
            project_ids: Optional[str] = Query(None, description="项目ID列表，逗号分隔"),
            current_user: User = Depends(user_dependency),
        ):
            project_id_list = None
            if project_ids:
                project_id_list = [int(id.strip()) for id in project_ids.split(",") if id.strip()]
            
            service = KitRateService(db)
            return service.get_dashboard(project_id_list)
        
        self.router.add_api_route(
            "/kit-rate/dashboard",
            dashboard_endpoint,
            methods=["GET"],
            summary="获取齐套看板数据"
        )
        
        # 添加趋势分析端点
        async def trend_endpoint(
            db: Session = Depends(deps.get_db),
            project_id: Optional[int] = Query(
                None, description="项目ID（可选，不提供则查询所有项目）"
            ),
            start_date: Optional[date] = Query(
                None, description="开始日期（可选，默认30天前）"
            ),
            end_date: Optional[date] = Query(None, description="结束日期（可选，默认今天）"),
            group_by: str = Query("day", description="分组方式：day（每日）或 month（每月）"),
            current_user: User = Depends(user_dependency),
        ):
            return self._get_trend_handler(
                db, current_user, project_id, start_date, end_date, group_by
            )
        
        self.router.add_api_route(
            "/kit-rate/trend",
            trend_endpoint,
            methods=["GET"],
            summary="获取齐套率趋势分析"
        )
        
        # 添加快照端点
        async def snapshots_endpoint(
            db: Session = Depends(deps.get_db),
            project_id: int = Query(..., description="项目ID"),
            start_date: Optional[date] = Query(None, description="开始日期"),
            end_date: Optional[date] = Query(None, description="结束日期"),
            snapshot_type: Optional[str] = Query(None, description="快照类型: DAILY/STAGE_CHANGE/MANUAL"),
            current_user: User = Depends(user_dependency),
        ):
            return self._get_snapshots_handler(
                db, current_user, project_id, start_date, end_date, snapshot_type
            )
        
        self.router.add_api_route(
            "/kit-rate/snapshots",
            snapshots_endpoint,
            methods=["GET"],
            summary="获取项目的齐套率快照历史"
        )
    
    def _get_user_dependency(self):
        """重写用户依赖，使用采购权限"""
        return security.require_procurement_access()
    
    def get_dashboard_data(
        self,
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """
        获取齐套看板数据（全局看板）
        注意：此方法不会被直接调用，因为路由已被覆盖
        """
        service = KitRateService(db)
        dashboard_data = service.get_dashboard(None)
        
        # 如果返回的是字典，直接返回；如果是ResponseModel，提取data
        if isinstance(dashboard_data, ResponseModel):
            result = dashboard_data.data
        else:
            result = dashboard_data
        
        # 确保是字典类型
        if not isinstance(result, dict):
            result = {"data": result}
        
        return result
    
    def _get_trend_handler(
        self,
        db: Session,
        current_user: User,
        project_id: Optional[int],
        start_date: Optional[date],
        end_date: Optional[date],
        group_by: str
    ) -> ResponseModel:
        """获取齐套率趋势分析"""
        # 设置默认日期范围
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=90)  # 默认90天

        if group_by not in ["day", "month"]:
            raise HTTPException(
                status_code=400, detail="group_by 必须是 day 或 month"
            )

        service = KitRateService(db)
        trend = service.get_trend(
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
            project_id=project_id,
        )
        return ResponseModel(code=200, message="success", data=trend)
    
    def _get_snapshots_handler(
        self,
        db: Session,
        current_user: User,
        project_id: int,
        start_date: Optional[date],
        end_date: Optional[date],
        snapshot_type: Optional[str]
    ) -> ResponseModel:
        """获取项目的齐套率快照历史"""
        # 设置默认日期范围
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        service = KitRateService(db)
        snapshot_data = service.get_snapshots(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            snapshot_type=snapshot_type,
        )
        return ResponseModel(code=200, message="success", data=snapshot_data)


# 创建端点实例并获取路由
dashboard_endpoint = KitRateDashboardEndpoint()
router = dashboard_endpoint.router
