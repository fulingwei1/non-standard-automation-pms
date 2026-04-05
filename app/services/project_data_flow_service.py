# -*- coding: utf-8 -*-
"""
项目数据流通服务

提供项目→生产/采购/交付/售后的数据自动关联功能
实现项目全生命周期的数据流转
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ProjectDataFlowService:
    """项目数据流通服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 项目→生产 ====================
    
    def create_work_orders_from_wbs(self, project_id: int) -> Dict[str, Any]:
        """从项目 WBS 任务自动生成生产工单"""
        from app.models.project import Project
        from app.models.production import WorkOrder
        
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}
        
        # 查询项目的 WBS 任务（生产类型）
        from app.models.project.extensions import ProjectTask
        
        tasks = self.db.query(ProjectTask).filter(
            ProjectTask.project_id == project_id,
            ProjectTask.task_type.in_(["ASSEMBLY", "DEBUG", "PRODUCTION"]),
        ).all()
        
        created_orders = []
        skipped = 0
        
        for task in tasks:
            # 检查是否已有工单
            existing = self.db.query(WorkOrder).filter(
                WorkOrder.project_id == project_id,
                WorkOrder.source_task_id == task.id,
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # 创建生产工单
            wo_no = f"WO-{project.project_code}-{task.task_no}"
            
            work_order = WorkOrder(
                work_order_no=wo_no,
                project_id=project_id,
                source_task_id=task.id,
                task_name=task.task_name,
                planned_start=task.planned_start,
                planned_end=task.planned_end,
                status="PENDING",
            )
            
            self.db.add(work_order)
            created_orders.append(wo_no)
        
        self.db.commit()
        
        logger.info(f"项目 {project_id}: 从 WBS 生成 {len(created_orders)} 个工单，跳过 {skipped} 个已存在")
        
        return {
            "project_id": project_id,
            "created_count": len(created_orders),
            "skipped_count": skipped,
            "created_orders": created_orders,
        }
    
    # ==================== 项目→采购 ====================
    
    def create_purchase_requests_from_bom(self, project_id: int, group_by: str = "supplier") -> Dict[str, Any]:
        """从项目 BOM 自动生成采购申请"""
        from app.models.material import BomHeader, BomItem
        from app.models.purchase import PurchaseRequest, PurchaseRequestItem
        from app.models.inventory_tracking import MaterialStock
        
        # 查询项目 BOM
        bom_headers = self.db.query(BomHeader).filter(BomHeader.project_id == project_id).all()
        
        if not bom_headers:
            return {"error": "项目无 BOM 数据"}
        
        # 合并所有 BOM 的物料需求
        material_needs = {}
        
        for bom in bom_headers:
            items = self.db.query(BomItem).filter(
                BomItem.bom_id == bom.id,
                BomItem.source_type == "PURCHASE",
            ).all()
            
            for item in items:
                mid = item.material_id
                if mid not in material_needs:
                    material_needs[mid] = {
                        "material_id": mid,
                        "material_name": item.material_name,
                        "total_qty": Decimal("0"),
                        "bom_items": [],
                    }
                material_needs[mid]["total_qty"] += Decimal(str(item.quantity or 0))
                material_needs[mid]["bom_items"].append(item.id)
        
        # 扣减库存
        for mid, need in material_needs.items():
            stock = (
                self.db.query(func.coalesce(func.sum(MaterialStock.available_quantity), 0))
                .filter(MaterialStock.material_id == mid)
                .scalar()
            )
            need["stock_qty"] = Decimal(str(stock or 0))
            need["net_qty"] = max(Decimal("0"), need["total_qty"] - need["stock_qty"])
        
        # 生成采购申请
        request_no = f"PR-{datetime.now().strftime('%Y%m%d')}-{project_id}"
        
        pr = PurchaseRequest(
            request_no=request_no,
            project_id=project_id,
            request_reason=f"项目 BOM 自动生成",
            status="DRAFT",
        )
        self.db.add(pr)
        self.db.flush()
        
        items_created = 0
        for mid, need in material_needs.items():
            if need["net_qty"] > 0:
                pri = PurchaseRequestItem(
                    request_id=pr.id,
                    material_id=mid,
                    quantity=need["net_qty"],
                )
                self.db.add(pri)
                items_created += 1
        
        self.db.commit()
        
        logger.info(f"项目 {project_id}: 从 BOM 生成采购申请 {request_no}，{items_created} 项物料")
        
        return {
            "project_id": project_id,
            "request_no": request_no,
            "request_id": pr.id,
            "total_materials": len(material_needs),
            "items_with_net_demand": items_created,
        }
    
    # ==================== 项目→交付 ====================
    
    def create_delivery_schedule_from_project(self, project_id: int, initiator_id: int) -> Dict[str, Any]:
        """从项目里程碑自动生成交付排产计划"""
        from app.models.project import Project
        from app.models.project_delivery import ProjectDeliverySchedule, ProjectDeliveryTask
        
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}
        
        # 生成计划编号
        schedule_no = f"PDS-{datetime.now().strftime('%Y')}-{project_id:03d}"
        
        # 创建交付排产计划
        schedule = ProjectDeliverySchedule(
            schedule_no=schedule_no,
            schedule_name=f"{project.project_name} - 交付排产计划",
            project_id=project_id,
            usage_type="INTERNAL",
            initiator_id=initiator_id,
            status="DRAFT",
            is_active=True,
        )
        
        self.db.add(schedule)
        self.db.flush()
        
        # 从项目里程碑生成交付任务
        from app.models.project.lifecycle import ProjectMilestone
        
        milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id
        ).order_by(ProjectMilestone.planned_date).all()
        
        tasks_created = 0
        for i, ms in enumerate(milestones):
            task = ProjectDeliveryTask(
                schedule_id=schedule.id,
                task_no=f"T{i+1:03d}",
                task_type="PRODUCTION",
                task_name=ms.milestone_name,
                planned_start=ms.planned_date,
                planned_end=ms.planned_date,
                status="PENDING",
            )
            self.db.add(task)
            tasks_created += 1
        
        self.db.commit()
        
        logger.info(f"项目 {project_id}: 从里程碑生成交付计划 {schedule_no}，{tasks_created} 个任务")
        
        return {
            "project_id": project_id,
            "schedule_id": schedule.id,
            "schedule_no": schedule_no,
            "tasks_created": tasks_created,
        }
    
    # ==================== 交付→售后 ====================
    
    def transfer_to_after_sales(self, project_id: int) -> Dict[str, Any]:
        """项目验收后转入售后服务"""
        from app.models.project import Project
        from app.models.after_sales import AfterSalesMaintenance
        
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}
        
        # 创建定期保养计划
        maintenance_records = []
        
        # 1 个月保养
        m1 = AfterSalesMaintenance(
            project_id=project_id,
            customer_id=project.customer_id,
            maintenance_type="REGULAR",
            maintenance_content="交付后 1 个月定期保养",
            status="SCHEDULED",
        )
        self.db.add(m1)
        maintenance_records.append("1 个月保养")
        
        # 3 个月保养
        m3 = AfterSalesMaintenance(
            project_id=project_id,
            customer_id=project.customer_id,
            maintenance_type="REGULAR",
            maintenance_content="交付后 3 个月定期保养",
            status="SCHEDULED",
        )
        self.db.add(m3)
        maintenance_records.append("3 个月保养")
        
        # 6 个月保养
        m6 = AfterSalesMaintenance(
            project_id=project_id,
            customer_id=project.customer_id,
            maintenance_type="REGULAR",
            maintenance_content="交付后 6 个月定期保养",
            status="SCHEDULED",
        )
        self.db.add(m6)
        maintenance_records.append("6 个月保养")
        
        # 12 个月保养
        m12 = AfterSalesMaintenance(
            project_id=project_id,
            customer_id=project.customer_id,
            maintenance_type="REGULAR",
            maintenance_content="交付后 12 个月定期保养（质保期内）",
            status="SCHEDULED",
        )
        self.db.add(m12)
        maintenance_records.append("12 个月保养")
        
        self.db.commit()
        
        logger.info(f"项目 {project_id}: 已转入售后，创建 {len(maintenance_records)} 个保养计划")
        
        return {
            "project_id": project_id,
            "maintenance_created": len(maintenance_records),
            "maintenance_records": maintenance_records,
        }
    
    # ==================== 项目全链路状态 ====================
    
    def get_project_full_status(self, project_id: int) -> Dict[str, Any]:
        """获取项目全链路状态（生产+采购+交付+售后）"""
        from app.services.views.project_production_view import get_project_production_overview
        from app.services.views.project_procurement_view import get_project_procurement_overview
        from app.services.views.project_delivery_view import get_project_delivery_overview
        from app.services.views.project_after_sales_view import get_project_after_sales_overview
        
        return {
            "project_id": project_id,
            "production": get_project_production_overview(self.db, project_id),
            "procurement": get_project_procurement_overview(self.db, project_id),
            "delivery": get_project_delivery_overview(self.db, project_id),
            "after_sales": get_project_after_sales_overview(self.db, project_id),
        }


def get_project_data_flow_service(db: Session) -> ProjectDataFlowService:
    """获取项目数据流通服务"""
    return ProjectDataFlowService(db)
