# -*- coding: utf-8 -*-
"""
Dashboard基类使用示例

展示如何使用BaseDashboardService创建Dashboard服务
"""

from typing import Dict, Any, Optional, List
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.common.dashboard import BaseDashboardService
from app.models.project import Project, ProjectCost


class ProjectDashboardService(BaseDashboardService):
    """
    项目Dashboard服务示例
    
    展示如何继承BaseDashboardService并实现Dashboard功能
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def get_overview(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        获取项目概览数据（必须实现）
        
        Returns:
            概览数据字典
        """
        # 使用基类提供的工具方法
        total = self.count_total(Project, filters)
        
        # 按状态统计
        by_status = self.count_by_status(Project, "status", filters)
        
        return {
            "total": total,
            "active": by_status.get("ACTIVE", 0),
            "pending": by_status.get("PENDING", 0),
            "completed": by_status.get("COMPLETED", 0),
            "by_status": by_status,
        }
    
    def get_stats(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        获取统计数据（可选重写）
        
        Returns:
            统计数据字典
        """
        # 按阶段统计
        by_stage = self.count_by_field(Project, "stage", filters)
        
        # 计算总成本和平均成本
        total_cost = self.calculate_sum(ProjectCost, "amount", filters)
        avg_cost = self.calculate_avg(ProjectCost, "amount", filters)
        
        return {
            "by_stage": by_stage,
            "total_cost": total_cost,
            "avg_cost": avg_cost,
        }
    
    def get_trends(
        self,
        date_field: str = "created_at",
        days: int = 30,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取项目创建趋势（可选重写）
        
        Returns:
            趋势数据列表
        """
        return self.get_trend_by_date(Project, date_field, days=days, filters=filters)
    
    def get_recent_items(
        self,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取最近项目列表（可选重写）
        
        Returns:
            最近项目列表
        """
        query = self.db.query(Project)
        
        # 应用筛选条件
        if filters:
            query = self._apply_filters(query, Project, filters)
        
        # 按创建时间倒序排列
        projects = query.order_by(desc(Project.created_at)).limit(limit).all()
        
        return [
            {
                "id": p.id,
                "code": p.project_code,
                "name": p.project_name,
                "status": p.status,
                "stage": p.stage,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ]
    
    def get_dashboard_data(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        获取完整Dashboard数据（可选重写以自定义结构）
        
        Returns:
            完整的Dashboard数据字典
        """
        return {
            "overview": self.get_overview(filters),
            "stats": self.get_stats(filters),
            "trends": self.get_trends(filters=filters),
            "recent_projects": self.get_recent_items(filters=filters),
            "timestamp": datetime.now().isoformat()
        }


# ========== 在API端点中使用 ==========

# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# 
# from app.api import deps
# from app.core import security
# from app.models.user import User
# from app.schemas.common import ResponseModel
# 
# router = APIRouter()
# 
# @router.get("/dashboard", response_model=ResponseModel[Dict])
# def get_project_dashboard(
#     db: Session = Depends(deps.get_db),
#     current_user: User = Depends(security.get_current_active_user),
# ):
#     """获取项目Dashboard数据"""
#     service = ProjectDashboardService(db)
#     dashboard_data = service.get_dashboard_data()
#     
#     return ResponseModel(
#         code=200,
#         message="获取Dashboard数据成功",
#         data=dashboard_data
#     )
