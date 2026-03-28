# -*- coding: utf-8 -*-
"""
项目关联服务

提供项目与生产/采购/交付/售后模块的关联功能
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.production import ProductionPlan, WorkOrder
from app.models.purchase import PurchaseRequest, PurchaseOrder
from app.models.project_delivery import ProjectDeliverySchedule


class ProjectRelationService:
    """项目关联服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_project_overview(self, project_id: int) -> Dict[str, Any]:
        """获取项目总览（包含各模块数据）"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {}
        
        return {
            "project": project,
            "production": self.get_production_status(project_id),
            "procurement": self.get_procurement_status(project_id),
            "delivery": self.get_delivery_status(project_id),
            "after_sales": self.get_after_sales_status(project_id),
        }
    
    def get_production_status(self, project_id: int) -> Dict[str, Any]:
        """获取生产状态"""
        # 查询项目的生产工单
        work_orders = self.db.query(WorkOrder).filter(
            WorkOrder.project_id == project_id
        ).all()
        
        return {
            "work_orders_count": len(work_orders),
            "completed_count": sum(1 for wo in work_orders if wo.status == "COMPLETED"),
            "in_progress_count": sum(1 for wo in work_orders if wo.status == "IN_PROGRESS"),
            "pending_count": sum(1 for wo in work_orders if wo.status == "PENDING"),
        }
    
    def get_procurement_status(self, project_id: int) -> Dict[str, Any]:
        """获取采购状态"""
        # 查询项目的采购申请和订单
        purchase_requests = self.db.query(PurchaseRequest).filter(
            PurchaseRequest.project_id == project_id
        ).all()
        
        purchase_orders = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.project_id == project_id
        ).all()
        
        return {
            "purchase_requests_count": len(purchase_requests),
            "purchase_orders_count": len(purchase_orders),
            "approved_count": sum(1 for po in purchase_orders if po.status == "APPROVED"),
            "received_count": sum(1 for po in purchase_orders if po.status == "RECEIVED"),
        }
    
    def get_delivery_status(self, project_id: int) -> Dict[str, Any]:
        """获取交付状态"""
        # 查询项目的交付排产计划
        schedules = self.db.query(ProjectDeliverySchedule).filter(
            ProjectDeliverySchedule.project_id == project_id
        ).all()
        
        return {
            "schedules_count": len(schedules),
            "confirmed_count": sum(1 for s in schedules if s.status == "CONFIRMED"),
            "in_filling_count": sum(1 for s in schedules if s.status == "FILLING"),
        }
    
    def get_after_sales_status(self, project_id: int) -> Dict[str, Any]:
        """获取售后状态"""
        from app.services.views.project_after_sales_view import get_project_after_sales_overview
        return get_project_after_sales_overview(self.db, project_id)


def get_project_relation_service(db: Session) -> ProjectRelationService:
    """获取项目关联服务"""
    return ProjectRelationService(db)
