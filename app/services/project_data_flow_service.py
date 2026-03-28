# -*- coding: utf-8 -*-
"""
项目数据流通服务

提供项目→生产/采购/交付/售后的数据自动关联功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.production import WorkOrder
from app.models.purchase import PurchaseRequest
from app.models.project_delivery import ProjectDeliverySchedule, ProjectDeliveryTask
from app.models.after_sales import AfterSalesSupportTicket


class ProjectDataFlowService:
    """项目数据流通服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_work_order_from_wbs(self, project_id: int, wbs_task_id: int) -> Optional[WorkOrder]:
        """从 WBS 任务创建生产工单"""
        # TODO: 实现 WBS 任务→生产工单的转换
        pass
    
    def create_purchase_request_from_bom(self, project_id: int, bom_id: int) -> Optional[PurchaseRequest]:
        """从 BOM 创建采购申请"""
        # TODO: 实现 BOM→采购申请的转换
        pass
    
    def create_delivery_schedule_from_milestones(self, project_id: int) -> Optional[ProjectDeliverySchedule]:
        """从项目里程碑生成交付排产计划"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        
        # 创建交付排产计划
        schedule = ProjectDeliverySchedule(
            project_id=project_id,
            schedule_name=f"{project.project_name} - 交付排产计划",
            usage_type="INTERNAL",
            initiator_id=project.pm_id,
            initiator_name=project.pm_name if hasattr(project, 'pm_name') else "",
        )
        
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        
        return schedule
    
    def create_support_ticket_from_feedback(self, project_id: int, feedback_content: str) -> Optional[AfterSalesSupportTicket]:
        """从客户反馈创建技术支持工单"""
        # 生成工单编号
        ticket_no = f"SUP-{datetime.now().strftime('%Y%m%d')}-{project_id}"
        
        ticket = AfterSalesSupportTicket(
            project_id=project_id,
            ticket_no=ticket_no,
            subject=f"项目 {project_id} 客户反馈",
            description=feedback_content,
            category="TECHNICAL",
            status="OPEN",
        )
        
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        
        return ticket
    
    def transfer_project_to_after_sales(self, project_id: int) -> bool:
        """项目验收后转入售后服务"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        # 更新项目状态为"已验收"
        project.status = "ACCEPTED"
        
        # TODO: 自动创建售后档案
        # TODO: 发送通知给售后团队
        
        self.db.commit()
        
        return True


def get_project_data_flow_service(db: Session) -> ProjectDataFlowService:
    """获取项目数据流通服务"""
    return ProjectDataFlowService(db)
