# -*- coding: utf-8 -*-
"""
服务工单管理服务
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Customer, Project
from app.models.service import (
    CustomerCommunication,
    CustomerSatisfaction,
    KnowledgeBase,
    SatisfactionSurveyTemplate,
    ServiceRecord,
    ServiceTicket,
)
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.service import (
    CustomerCommunicationCreate,
    CustomerCommunicationResponse,
    CustomerCommunicationUpdate,
    CustomerSatisfactionCreate,
    CustomerSatisfactionResponse,
    CustomerSatisfactionUpdate,
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
    PaginatedResponse,
    SatisfactionSurveyTemplateCreate,
    SatisfactionSurveyTemplateUpdate,
    ServiceDashboardStatistics,
    ServiceRecordCreate,
    ServiceRecordResponse,
    ServiceRecordUpdate,
    ServiceTicketAssign,
    ServiceTicketClose,
    ServiceTicketCreate,
    ServiceTicketResponse,
    ServiceTicketUpdate,
)


class ServiceTicketsService:
    """服务工单管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_statistics(self) -> ServiceDashboardStatistics:
        """获取服务工单仪表板统计"""
        today = date.today()

        # 今日新增工单
        today_tickets = self.db.query(ServiceTicket).filter(
            func.date(ServiceTicket.created_at) == today
        ).count()

        # 待处理工单
        pending_tickets = self.db.query(ServiceTicket).filter(
            ServiceTicket.status == "pending"
        ).count()

        # 进行中工单
        in_progress_tickets = self.db.query(ServiceTicket).filter(
            ServiceTicket.status == "in_progress"
        ).count()

        # 今日完成工单
        today_completed = self.db.query(ServiceTicket).filter(
            ServiceTicket.status == "completed",
            func.date(ServiceTicket.updated_at) == today
        ).count()

        # 平均响应时间
        avg_response_time = self._calculate_avg_response_time()

        # 客户满意度
        satisfaction_rate = self._calculate_satisfaction_rate()

        return ServiceDashboardStatistics(
            today_new_tickets=today_tickets,
            pending_tickets=pending_tickets,
            in_progress_tickets=in_progress_tickets,
            today_completed_tickets=today_completed,
            average_response_time_minutes=avg_response_time,
            customer_satisfaction_rate=satisfaction_rate
        )

    def get_project_members(self) -> dict:
        """获取项目成员列表"""
        users = self.db.query(User).filter(
            User.is_active == True,
            User.department_id.in_([3, 4])  # 服务部和技术部
        ).all()

        return {
            "members": [
                {
                    "id": user.id,
                    "name": user.name,
                    "department": user.department.name if user.department else None,
                    "position": user.position,
                    "contact": user.phone
                }
                for user in users
            ]
        }

    def get_ticket_projects(self, ticket_id: int) -> dict:
        """获取工单关联的项目"""
        ticket = self.db.query(ServiceTicket).filter(
            ServiceTicket.id == ticket_id
        ).first()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工单不存在"
            )

        return {
            "projects": [
                {
                    "id": project.id,
                    "name": project.name,
                    "status": project.status
                }
                for project in ticket.projects
            ]
        }

    def get_ticket_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[int] = None
    ) -> dict:
        """获取工单统计信息"""
        query = self.db.query(ServiceTicket)

        if start_date:
            query = query.filter(ServiceTicket.created_at >= start_date)

        if end_date:
            query = query.filter(ServiceTicket.created_at <= end_date)

        if status:
            query = query.filter(ServiceTicket.status == status)

        if priority:
            query = query.filter(ServiceTicket.priority == priority)

        if assigned_to:
            query = query.filter(ServiceTicket.assigned_to == assigned_to)

        # 基础统计
        total_tickets = query.count()

        # 状态分布
        status_stats = query.with_entities(
            ServiceTicket.status,
            func.count(ServiceTicket.id).label('count')
        ).group_by(ServiceTicket.status).all()

        status_distribution = {stat.status: stat.count for stat in status_stats}

        # 优先级分布
        priority_stats = query.with_entities(
            ServiceTicket.priority,
            func.count(ServiceTicket.id).label('count')
        ).group_by(ServiceTicket.priority).all()

        priority_distribution = {stat.priority: stat.count for stat in priority_stats}

        # 处理时长统计
        processing_times = []
        for ticket in query.filter(ServiceTicket.status == "completed").all():
            if ticket.resolved_at:
                duration = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600  # 小时
                processing_times.append(duration)

        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

        return {
            "total_tickets": total_tickets,
            "status_distribution": status_distribution,
            "priority_distribution": priority_distribution,
            "average_processing_time_hours": round(avg_processing_time, 2),
            "completed_tickets": status_distribution.get("completed", 0),
            "completion_rate": (status_distribution.get("completed", 0) / total_tickets * 100) if total_tickets > 0 else 0
        }

    def get_service_tickets(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        ticket_type: Optional[str] = None,
        assigned_to: Optional[int] = None,
        customer_id: Optional[int] = None,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> PaginatedResponse[ServiceTicketResponse]:
        """获取服务工单列表"""
        query = self.db.query(ServiceTicket).options(
            joinedload(ServiceTicket.customer),
            joinedload(ServiceTicket.assigned_user),
            joinedload(ServiceTicket.created_by_user)
        )

        # 搜索条件
        if keyword:
            query = query.filter(
                or_(
                    ServiceTicket.ticket_number.ilike(f"%{keyword}%"),
                    ServiceTicket.title.ilike(f"%{keyword}%"),
                    ServiceTicket.description.ilike(f"%{keyword}%")
                )
            )

        # 筛选条件
        if status:
            query = query.filter(ServiceTicket.status == status)

        if priority:
            query = query.filter(ServiceTicket.priority == priority)

        if ticket_type:
            query = query.filter(ServiceTicket.ticket_type == ticket_type)

        if assigned_to:
            query = query.filter(ServiceTicket.assigned_to == assigned_to)

        if customer_id:
            query = query.filter(ServiceTicket.customer_id == customer_id)

        if project_id:
            query = query.filter(ServiceTicket.project_id == project_id)

        if start_date:
            query = query.filter(ServiceTicket.created_at >= start_date)

        if end_date:
            query = query.filter(ServiceTicket.created_at <= end_date)

        # 按创建时间倒序
        query = query.order_by(ServiceTicket.created_at.desc())

        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[ServiceTicketResponse.model_validate(item) for item in items]
        )

    def get_service_ticket(self, ticket_id: int) -> Optional[ServiceTicket]:
        """获取单个服务工单"""
        return self.db.query(ServiceTicket).options(
            joinedload(ServiceTicket.customer),
            joinedload(ServiceTicket.assigned_user),
            joinedload(ServiceTicket.created_by_user),
            joinedload(ServiceTicket.updated_by_user),
            joinedload(ServiceTicket.resolved_by_user),
            joinedload(ServiceTicket.service_records),
            joinedload(ServiceTicket.communications)
        ).filter(ServiceTicket.id == ticket_id).first()

    def create_service_ticket(
        self,
        ticket_data: ServiceTicketCreate,
        current_user: User
    ) -> ServiceTicket:
        """创建服务工单"""
        # 生成工单编号
        ticket_number = self._generate_ticket_number(ticket_data.ticket_type)

        service_ticket = ServiceTicket(
            ticket_number=ticket_number,
            title=ticket_data.title,
            description=ticket_data.description,
            ticket_type=ticket_data.ticket_type,
            priority=ticket_data.priority,
            customer_id=ticket_data.customer_id,
            project_id=ticket_data.project_id,
            contact_person=ticket_data.contact_person,
            contact_phone=ticket_data.contact_phone,
            contact_email=ticket_data.contact_email,
            service_location=ticket_data.service_location,
            expected_resolution_time=ticket_data.expected_resolution_time,
            created_by=current_user.id,
            status="pending"
        )

        self.db.add(service_ticket)
        self.db.commit()
        self.db.refresh(service_ticket)

        # 自动分配处理人
        self._auto_assign_ticket(service_ticket)

        # 发送通知
        self._send_ticket_notification(service_ticket, "created")

        return service_ticket

    def assign_ticket(
        self,
        ticket_id: int,
        assign_data: ServiceTicketAssign,
        current_user: User
    ) -> Optional[ServiceTicket]:
        """分配服务工单"""
        service_ticket = self.get_service_ticket(ticket_id)
        if not service_ticket:
            return None

        service_ticket.assigned_to = assign_data.assigned_to
        service_ticket.status = "assigned"
        service_ticket.assigned_at = datetime.now(timezone.utc)
        service_ticket.assigned_note = assign_data.note
        service_ticket.updated_by = current_user.id
        service_ticket.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(service_ticket)

        # 发送通知
        self._send_ticket_notification(service_ticket, "assigned")

        return service_ticket

    def update_ticket_status(
        self,
        ticket_id: int,
        status: str,
        note: Optional[str] = None,
        current_user: User = None
    ) -> Optional[ServiceTicket]:
        """更新工单状态"""
        service_ticket = self.get_service_ticket(ticket_id)
        if not service_ticket:
            return None

        old_status = service_ticket.status
        service_ticket.status = status
        service_ticket.updated_by = current_user.id if current_user else service_ticket.updated_by
        service_ticket.updated_at = datetime.now(timezone.utc)

        if note:
            service_ticket.status_note = note

        # 设置解决时间
        if status == "completed" and old_status != "completed":
            service_ticket.resolved_at = datetime.now(timezone.utc)
            service_ticket.resolved_by = current_user.id if current_user else None

        # 设置开始时间
        if status == "in_progress" and old_status in ["pending", "assigned"]:
            service_ticket.started_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(service_ticket)

        # 发送通知
        self._send_ticket_notification(service_ticket, f"status_changed_to_{status}")

        return service_ticket

    def close_ticket(
        self,
        ticket_id: int,
        close_data: ServiceTicketClose,
        current_user: User
    ) -> Optional[ServiceTicket]:
        """关闭服务工单"""
        service_ticket = self.get_service_ticket(ticket_id)
        if not service_ticket:
            return None

        service_ticket.status = "completed"
        service_ticket.resolution_summary = close_data.resolution_summary
        service_ticket.customer_feedback = close_data.customer_feedback
        service_ticket.customer_satisfaction = close_data.customer_satisfaction
        service_ticket.resolved_at = datetime.now(timezone.utc)
        service_ticket.resolved_by = current_user.id
        service_ticket.updated_by = current_user.id
        service_ticket.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(service_ticket)

        # 发送通知
        self._send_ticket_notification(service_ticket, "closed")

        # 创建满意度调查
        self._create_satisfaction_survey(service_ticket)

        return service_ticket

    def _generate_ticket_number(self, ticket_type: str) -> str:
        """生成工单编号"""
        # 工单类型编码映射
        type_codes = {
            "installation": "INST",
            "maintenance": "MAINT",
            "repair": "REPAIR",
            "consultation": "CONS",
            "complaint": "COMP",
            "other": "OTHER"
        }

        type_code = type_codes.get(ticket_type, "SRV")

        # 获取当天该类型的工单数量
        today = date.today()
        count = self.db.query(ServiceTicket).filter(
            ServiceTicket.ticket_type == ticket_type,
            func.date(ServiceTicket.created_at) == today
        ).count()

        return f"{type_code}{today.strftime('%Y%m%d')}{count+1:04d}"

    def _auto_assign_ticket(self, service_ticket: ServiceTicket):
        """自动分配工单"""
        # 根据工单类型和优先级自动分配
        assignment_rules = {
            "installation": [1, 2],  # 安装工程师ID
            "maintenance": [3, 4],   # 维护工程师ID
            "repair": [5, 6],        # 维修工程师ID
            "consultation": [7, 8],   # 咨询顾问ID
        }

        # 高优先级工单分配给高级工程师
        if service_ticket.priority in ["high", "critical"]:
            # 可以有更复杂的分配逻辑
            pass

    def _send_ticket_notification(self, service_ticket: ServiceTicket, action: str):
        """发送工单通知"""
        # 集成通知系统（邮件、短信等）
        pass

    def _create_satisfaction_survey(self, service_ticket: ServiceTicket):
        """创建满意度调查"""
        # 自动生成满意度调查
        pass

    def _calculate_avg_response_time(self) -> float:
        """计算平均响应时间"""
        # 计算最近30天的平均响应时间
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        response_times = self.db.query(ServiceTicket).filter(
            ServiceTicket.created_at >= thirty_days_ago,
            ServiceTicket.assigned_at.isnot(None)
        ).with_entities(
            func.extract('epoch', ServiceTicket.assigned_at - ServiceTicket.created_at)
        ).all()

        if not response_times:
            return 0

        avg_seconds = sum(rt[0] for rt in response_times) / len(response_times)
        return round(avg_seconds / 60, 2)  # 转换为分钟

    def _calculate_satisfaction_rate(self) -> float:
        """计算客户满意度率"""
        # 计算最近30天的客户满意度
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        satisfactions = self.db.query(CustomerSatisfaction).filter(
            CustomerSatisfaction.created_at >= thirty_days_ago,
            CustomerSatisfaction.overall_rating.isnot(None)
        ).with_entities(CustomerSatisfaction.overall_rating).all()

        if not satisfactions:
            return 0

        avg_rating = sum(s[0] for s in satisfactions) / len(satisfactions)
        return round(avg_rating, 2)
