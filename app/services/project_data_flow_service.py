# -*- coding: utf-8 -*-
"""
项目数据流通服务

提供项目→生产/采购/交付/售后的数据自动关联功能
实现项目全生命周期的数据流转
"""

import logging
from calendar import monthrange
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

        # 查询项目 WBS 中会进入生产执行的任务
        from app.models.progress import Task

        tasks = self.db.query(Task).filter(
            Task.project_id == project_id,
            Task.stage.in_(["S4", "S5"]),
        ).all()
        
        created_orders = []
        skipped = 0
        
        for task in tasks:
            task_code = task.task_code or str(task.id)
            wo_no = f"WO-{project.project_code}-{task_code}"

            # 检查是否已有工单
            existing = self.db.query(WorkOrder).filter(
                WorkOrder.project_id == project_id,
                WorkOrder.work_order_no == wo_no,
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            work_order = WorkOrder(
                work_order_no=wo_no,
                project_id=project_id,
                task_name=task.task_name or task_code,
                task_type=_work_order_type_for_stage(task.stage),
                plan_start_date=task.plan_start,
                plan_end_date=task.plan_end,
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

        bom_header_ids = [bom.id for bom in bom_headers]
        existing_request = self.db.query(PurchaseRequest).filter(
            PurchaseRequest.project_id == project_id,
            PurchaseRequest.source_type == "BOM",
            PurchaseRequest.source_id.in_(bom_header_ids),
        ).first()
        if existing_request:
            return {
                "project_id": project_id,
                "request_no": existing_request.request_no,
                "request_id": existing_request.id,
                "total_materials": 0,
                "items_with_net_demand": 0,
                "skipped_existing": True,
            }
        
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
                        "bom_item_id": item.id,
                        "material_code": item.material_code,
                        "material_name": item.material_name,
                        "specification": item.specification,
                        "unit": item.unit or "件",
                        "unit_price": Decimal(str(item.unit_price or 0)),
                        "required_date": item.required_date,
                        "total_qty": Decimal("0"),
                        "bom_items": [],
                    }
                material_needs[mid]["total_qty"] += Decimal(str(item.quantity or 0))
                material_needs[mid]["bom_items"].append(item.id)
                if item.required_date and (
                    material_needs[mid]["required_date"] is None
                    or item.required_date < material_needs[mid]["required_date"]
                ):
                    material_needs[mid]["required_date"] = item.required_date
        
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
            source_type="BOM",
            source_id=bom_headers[0].id,
            request_reason=f"项目 BOM 自动生成",
            status="DRAFT",
        )
        self.db.add(pr)
        self.db.flush()
        
        items_created = 0
        total_amount = Decimal("0")
        for mid, need in material_needs.items():
            if need["net_qty"] > 0:
                amount = need["net_qty"] * need["unit_price"]
                pri = PurchaseRequestItem(
                    request_id=pr.id,
                    bom_item_id=need["bom_item_id"],
                    material_id=mid,
                    material_code=need["material_code"],
                    material_name=need["material_name"],
                    specification=need["specification"],
                    unit=need["unit"],
                    quantity=need["net_qty"],
                    unit_price=need["unit_price"],
                    amount=amount,
                    required_date=need["required_date"],
                )
                self.db.add(pri)
                items_created += 1
                total_amount += amount
        pr.total_amount = total_amount
        
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

        existing_schedule = self.db.query(ProjectDeliverySchedule).filter(
            ProjectDeliverySchedule.project_id == project_id,
            ProjectDeliverySchedule.is_active.is_(True),
        ).first()
        if existing_schedule:
            return {
                "project_id": project_id,
                "schedule_id": existing_schedule.id,
                "schedule_no": existing_schedule.schedule_no,
                "tasks_created": 0,
                "skipped_existing": True,
            }
        
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
        from app.models.project import ProjectMilestone
        
        milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id
        ).order_by(ProjectMilestone.planned_date).all()
        
        tasks_created = 0
        for i, ms in enumerate(milestones):
            if not ms.planned_date:
                continue
            task = ProjectDeliveryTask(
                schedule_id=schedule.id,
                task_no=f"T{i+1:03d}",
                task_type="PRODUCTION",
                task_name=ms.milestone_name or ms.milestone_code or f"里程碑 {ms.id}",
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
        
        existing_regular = self.db.query(AfterSalesMaintenance).filter(
            AfterSalesMaintenance.project_id == project_id,
            AfterSalesMaintenance.maintenance_type == "REGULAR",
        ).all()
        existing_contents = {item.maintenance_content for item in existing_regular}

        maintenance_start = (
            project.warranty_start_date
            or project.actual_end_date
            or project.planned_end_date
            or date.today()
        )
        maintenance_plan = [
            (1, "1 个月保养", "交付后 1 个月定期保养"),
            (3, "3 个月保养", "交付后 3 个月定期保养"),
            (6, "6 个月保养", "交付后 6 个月定期保养"),
            (12, "12 个月保养", "交付后 12 个月定期保养（质保期内）"),
        ]

        maintenance_records = []
        skipped_existing = 0

        for months, label, content in maintenance_plan:
            if content in existing_contents:
                skipped_existing += 1
                continue

            maintenance = AfterSalesMaintenance(
                project_id=project_id,
                customer_id=project.customer_id,
                maintenance_type="REGULAR",
                maintenance_content=content,
                scheduled_date=_add_months(maintenance_start, months),
                status="SCHEDULED",
            )
            self.db.add(maintenance)
            maintenance_records.append(label)

        if maintenance_records:
            self.db.commit()
        
        logger.info(f"项目 {project_id}: 已转入售后，创建 {len(maintenance_records)} 个保养计划")
        
        return {
            "project_id": project_id,
            "maintenance_created": len(maintenance_records),
            "maintenance_records": maintenance_records,
            "skipped_existing": skipped_existing,
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


def _work_order_type_for_stage(stage: Optional[str]) -> str:
    """把项目 WBS 阶段映射为生产工单类型"""
    return {
        "S4": "PRODUCTION",
        "S5": "ASSEMBLY",
    }.get(stage or "", "OTHER")


def _add_months(value: date, months: int) -> date:
    """按自然月推算计划日期，自动处理月末天数"""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)
