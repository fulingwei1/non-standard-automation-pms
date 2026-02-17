# -*- coding: utf-8 -*-
"""
Dashboard API 端点基类

提供统一的Dashboard实现模式，减少代码重复。
所有模块的dashboard端点应该继承此基类。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel


class BaseDashboardService(ABC):
    """兼容占位：历史代码引用的Dashboard服务基类"""

    module_name: str = ""
    permission_required: Optional[str] = None

    @abstractmethod
    def get_dashboard_data(
        self, db: Session, current_user: User
    ) -> Dict[str, Any]:
        """子类需要实现获取dashboard数据的逻辑"""
        raise NotImplementedError


class BaseDashboardEndpoint(BaseDashboardService):
    """Dashboard端点基类
    
    所有模块的dashboard端点应该继承此类，实现必要的方法。
    
    使用示例:
        class ProductionDashboardEndpoint(BaseDashboardEndpoint):
            module_name = "production"
            permission_required = "production:read"
            
            def get_stats(self, db: Session, current_user: User) -> Dict[str, Any]:
                # 实现统计逻辑
                return {...}
    """
    
    # 子类必须定义的属性
    module_name: str = ""  # 模块名称，用于路由前缀
    permission_required: Optional[str] = None  # 需要的权限，None表示不需要特殊权限
    
    def __init__(self):
        """初始化路由"""
        self.router = APIRouter()
        self._register_routes()
    
    def _register_routes(self):
        """注册路由"""
        user_dependency = self._get_user_dependency()

        async def dashboard_endpoint(
            db: Session = Depends(deps.get_db),
            current_user: User = Depends(user_dependency),
        ):
            return self._get_dashboard_handler(db, current_user)

        # 主dashboard端点
        self.router.add_api_route(
            f"/{self.module_name}/dashboard",
            dashboard_endpoint,
            methods=["GET"],
            summary=f"获取{self.module_name}模块仪表板数据",
            response_model=ResponseModel[Dict[str, Any]],
        )

        # 可选：统计端点
        if hasattr(self, "get_stats_only"):

            async def stats_endpoint(
                db: Session = Depends(deps.get_db),
                current_user: User = Depends(user_dependency),
            ):
                return self._get_stats_handler(db, current_user)

            self.router.add_api_route(
                f"/{self.module_name}/dashboard/stats",
                stats_endpoint,
                methods=["GET"],
                summary=f"获取{self.module_name}模块统计数据",
                response_model=ResponseModel[Dict[str, Any]],
            )
    
    def _get_dashboard_handler(
        self,
        db: Session,
        current_user: User,
    ) -> ResponseModel[Dict[str, Any]]:
        """Dashboard端点处理器（统一入口）"""
        try:
            data = self.get_dashboard_data(db, current_user)
            return ResponseModel(
                code=200,
                message="获取仪表板数据成功",
                data=data
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取仪表板数据失败: {str(e)}"
            )
    
    def _get_stats_handler(
        self,
        db: Session,
        current_user: User,
    ) -> ResponseModel[Dict[str, Any]]:
        """统计端点处理器"""
        try:
            stats = self.get_stats(db, current_user)
            return ResponseModel(
                code=200,
                message="获取统计数据成功",
                data=stats
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取统计数据失败: {str(e)}"
            )
    
    def _get_user_dependency(self):
        """获取用户依赖（根据权限要求）"""
        if self.permission_required:
            return security.require_permission(self.permission_required)
        return security.get_current_active_user
    
    @abstractmethod
    def get_dashboard_data(
        self,
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """获取完整的dashboard数据
        
        Args:
            db: 数据库会话
            current_user: 当前用户
            
        Returns:
            dashboard数据字典，包含所有统计和展示数据
        """
        pass
    
    def get_stats(
        self,
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """获取统计数据（可选实现）
        
        如果只需要统计卡片数据，可以实现此方法。
        默认实现调用get_dashboard_data并提取stats字段。
        
        Args:
            db: 数据库会话
            current_user: 当前用户
            
        Returns:
            统计数据字典
        """
        dashboard_data = self.get_dashboard_data(db, current_user)
        # 尝试提取stats字段，如果没有则返回整个数据
        return dashboard_data.get("stats", dashboard_data)
    
    def create_stat_card(
        self,
        key: str,
        label: str,
        value: Any,
        trend: Optional[float] = None,
        unit: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建统计卡片数据
        
        Args:
            key: 统计项标识
            label: 统计项名称
            value: 统计值
            trend: 趋势（百分比）
            unit: 单位
            icon: 图标名称
            color: 颜色
            
        Returns:
            统计卡片字典
        """
        return {
            "key": key,
            "label": label,
            "value": value,
            "trend": trend,
            "unit": unit,
            "icon": icon,
            "color": color
        }
    
    def create_list_item(
        self,
        id: Any,
        title: str,
        subtitle: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        event_date: Optional[date] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建列表项数据
        
        Args:
            id: 项目ID
            title: 标题
            subtitle: 副标题
            status: 状态
            priority: 优先级
            event_date: 日期
            extra: 额外信息
            
        Returns:
            列表项字典
        """
        item = {
            "id": id,
            "title": title,
            "subtitle": subtitle,
            "status": status,
            "priority": priority,
            "event_date": str(event_date) if event_date else None,
            "extra": extra or {}
        }
        return item
    
    def create_chart_data(
        self,
        chart_type: str,
        data_points: List[Dict[str, Any]],
        title: Optional[str] = None,
        series: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """创建图表数据
        
        Args:
            chart_type: 图表类型（line/bar/pie/area/scatter）
            data_points: 数据点列表
            title: 图表标题
            series: 多系列数据
            
        Returns:
            图表数据字典
        """
        return {
            "type": chart_type,
            "title": title,
            "data": data_points,
            "series": series
        }


def create_dashboard_router(
    module_name: str,
    get_dashboard_data_func,
    permission_required: Optional[str] = None,
    additional_routes: Optional[List[Dict[str, Any]]] = None
) -> APIRouter:
    """快速创建dashboard路由的工厂函数
    
    Args:
        module_name: 模块名称
        get_dashboard_data_func: 获取dashboard数据的函数
        permission_required: 需要的权限
        additional_routes: 额外的路由配置
        
    Returns:
        APIRouter实例
        
    使用示例:
        router = create_dashboard_router(
            module_name="production",
            get_dashboard_data_func=get_production_dashboard_data,
            permission_required="production:read"
        )
    """
    router = APIRouter()
    
    # 用户依赖
    if permission_required:
        user_dep = security.require_permission(permission_required)
    else:
        user_dep = security.get_current_active_user
    
    # 主dashboard端点
    @router.get("/dashboard", response_model=ResponseModel[Dict[str, Any]])
    def get_dashboard(
        db: Session = Depends(deps.get_db),
        current_user: User = Depends(user_dep),
    ) -> ResponseModel[Dict[str, Any]]:
        """获取仪表板数据"""
        try:
            data = get_dashboard_data_func(db, current_user)
            return ResponseModel(
                code=200,
                message="获取仪表板数据成功",
                data=data
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取仪表板数据失败: {str(e)}"
            )
    
    # 添加额外路由
    if additional_routes:
        for route_config in additional_routes:
            router.add_api_route(**route_config)
    
    return router
