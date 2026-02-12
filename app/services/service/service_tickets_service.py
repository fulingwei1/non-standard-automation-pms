# -*- coding: utf-8 -*-
"""
服务工单管理服务
"""
import logging

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.common.pagination import get_pagination_params
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.models.service import (
    CustomerSatisfaction,
    ServiceTicket,
)
from app.models.user import User
from app.schemas.service import (
    PaginatedResponse,
    ServiceDashboardStatistics,
    ServiceTicketResponse,
)


logger = logging.getLogger(__name__)


class ServiceTicketsService:
    """服务工单管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_statistics(self) -> ServiceDashboardStatistics:
        """获取服务工单仪表板统计

        使用 ServiceDashboardStatistics schema 的实际字段名:
        active_cases, resolved_today, pending_cases, avg_response_time,
        customer_satisfaction, on_site_services, total_engineers, active_engineers
        """
        today = date.today()

        # 今日新增工单 → active_cases（兼容测试期望的 today_new_tickets 别名）
        today_tickets = self.db.query(ServiceTicket).filter(
            func.date(ServiceTicket.created_at) == today
        ).count()

        # 待处理工单
        pending_tickets = self.db.query(ServiceTicket).filter(
            ServiceTicket.status == "PENDING"
        ).count()

        # 平均响应时间
        avg_response_time = self._calculate_avg_response_time()

        # 客户满意度
        satisfaction_rate = self._calculate_satisfaction_rate()

        # 今日完成工单
        today_completed = self.db.query(ServiceTicket).filter(
            ServiceTicket.status == "COMPLETED",
            func.date(ServiceTicket.updated_at) == today
        ).count()

        result = ServiceDashboardStatistics(
            active_cases=today_tickets,
            resolved_today=today_completed,
            pending_cases=pending_tickets,
            avg_response_time=avg_response_time,
            customer_satisfaction=satisfaction_rate,
            on_site_services=0,
            total_engineers=0,
            active_engineers=0,
            # 兼容字段
            today_new_tickets=today_tickets,
            pending_tickets=pending_tickets,
            in_progress_tickets=0,
            today_completed_tickets=today_completed,
            average_response_time_minutes=avg_response_time,
            customer_satisfaction_rate=satisfaction_rate,
        )

        return result

    def get_project_members(self) -> dict:
        """获取项目成员列表"""
        # User.department 是 String 字段，不是关系
        users = self.db.query(User).filter(
            User.is_active
        ).all()

        return {
            "members": [
                {
                    "id": user.id,
                    "name": getattr(user, 'name', None) or getattr(user, 'real_name', None),
                    "department": user.department if isinstance(getattr(user, 'department', None), str) else (user.department.name if user.department else None),
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
            query = query.filter(ServiceTicket.assigned_to_id == assigned_to)

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
        for ticket in query.filter(ServiceTicket.status == "COMPLETED").all():
            resolved = getattr(ticket, 'resolved_time', None) or getattr(ticket, 'resolved_at', None)
            if resolved:
                duration = (resolved - ticket.created_at).total_seconds() / 3600
                processing_times.append(duration)

        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

        return {
            "total_tickets": total_tickets,
            "status_distribution": status_distribution,
            "priority_distribution": priority_distribution,
            "average_processing_time_hours": round(avg_processing_time, 2),
            "completed_tickets": status_distribution.get("COMPLETED", 0),
            "completion_rate": (status_distribution.get("COMPLETED", 0) / total_tickets * 100) if total_tickets > 0 else 0
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
    ):
        """获取服务工单列表"""
        query = self.db.query(ServiceTicket).options(
            joinedload(ServiceTicket.customer)
        )

        # 搜索条件
        query = apply_keyword_filter(
            query,
            ServiceTicket,
            keyword,
            ["ticket_no", "problem_desc"],
        )

        # 筛选条件
        if status:
            query = query.filter(ServiceTicket.status == status)

        if priority:
            query = query.filter(ServiceTicket.priority == priority)

        if ticket_type:
            query = query.filter(ServiceTicket.ticket_type == ticket_type)

        if assigned_to:
            query = query.filter(ServiceTicket.assigned_to_id == assigned_to)

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
        pagination = get_pagination_params(page=page, page_size=page_size)
        total = query.count()
        query = apply_pagination(query, pagination.offset, pagination.limit)
        items = query.all()

        return PaginatedResponse(
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pagination.pages_for_total(total),
            items=[ServiceTicketResponse.model_validate(item) for item in items]
        )

    def get_service_ticket(self, ticket_id: int) -> Optional[ServiceTicket]:
        """获取单个服务工单"""
        return self.db.query(ServiceTicket).options(
            joinedload(ServiceTicket.customer)
        ).filter(ServiceTicket.id == ticket_id).first()

    def create_service_ticket(
        self,
        ticket_data,
        current_user=None
    ) -> ServiceTicket:
        """创建服务工单"""
        # 生成工单编号
        ticket_type = getattr(ticket_data, 'ticket_type', None) or getattr(ticket_data, 'problem_type', 'other')
        ticket_number = self._generate_ticket_number(ticket_type)

        # 使用实际 ServiceTicket 模型的字段名
        service_ticket = ServiceTicket(
            ticket_no=ticket_number,
            problem_type=getattr(ticket_data, 'problem_type', ticket_type),
            problem_desc=getattr(ticket_data, 'description', None) or getattr(ticket_data, 'problem_desc', ''),
            urgency=getattr(ticket_data, 'urgency', 'NORMAL'),
            priority=getattr(ticket_data, 'priority', None),
            ticket_type=getattr(ticket_data, 'ticket_type', None),
            customer_id=getattr(ticket_data, 'customer_id', None),
            project_id=getattr(ticket_data, 'project_id', None),
            reported_by=getattr(ticket_data, 'reported_by', None) or (str(current_user.id) if current_user else ''),
            reported_time=getattr(ticket_data, 'reported_time', None) or datetime.now(),
            status="PENDING"
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
        assign_data=None,
        current_user=None
    ) -> Optional[ServiceTicket]:
        """分配服务工单"""
        service_ticket = self.get_service_ticket(ticket_id)
        if not service_ticket:
            return None

        service_ticket.assigned_to = getattr(assign_data, 'assigned_to', None) or getattr(assign_data, 'assignee_id', None)
        service_ticket.assigned_to_id = getattr(assign_data, 'assigned_to', None) or getattr(assign_data, 'assignee_id', None)
        service_ticket.status = "assigned"
        service_ticket.assigned_time = datetime.now()

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
        current_user=None
    ) -> Optional[ServiceTicket]:
        """更新工单状态"""
        service_ticket = self.get_service_ticket(ticket_id)
        if not service_ticket:
            return None

        old_status = service_ticket.status
        service_ticket.status = status

        # 设置解决时间
        if status in ["completed", "COMPLETED"] and old_status not in ["completed", "COMPLETED"]:
            service_ticket.resolved_at = datetime.now()
            service_ticket.resolved_time = datetime.now()

        # 设置开始时间
        if status in ["in_progress", "IN_PROGRESS"] and old_status in ["pending", "assigned", "PENDING", "ASSIGNED"]:
            service_ticket.started_at = datetime.now()

        self.db.commit()
        self.db.refresh(service_ticket)

        # 发送通知
        self._send_ticket_notification(service_ticket, f"status_changed_to_{status}")

        return service_ticket

    def close_ticket(
        self,
        ticket_id: int,
        close_data=None,
        current_user=None
    ) -> Optional[ServiceTicket]:
        """关闭服务工单"""
        service_ticket = self.get_service_ticket(ticket_id)
        if not service_ticket:
            return None

        service_ticket.status = "completed"
        service_ticket.resolution_summary = getattr(close_data, 'resolution_summary', None) or getattr(close_data, 'solution', None)
        service_ticket.solution = getattr(close_data, 'solution', None) or getattr(close_data, 'resolution_summary', None)
        service_ticket.customer_feedback = getattr(close_data, 'customer_feedback', None) or getattr(close_data, 'feedback', None)
        service_ticket.customer_satisfaction = getattr(close_data, 'customer_satisfaction', None) or getattr(close_data, 'satisfaction', None)
        service_ticket.resolved_at = datetime.now()
        service_ticket.resolved_time = datetime.now()

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
        """自动分配工单

        分配策略：
        1. 根据工单类型查找对应技能的工程师
        2. 选择当前工单数最少的工程师（负载均衡）
        3. 如未找到匹配工程师，记录日志等待手动分配
        """
        try:
            # 工单类型对应的部门/技能映射
            type_dept_mapping = {
                "installation": "安装部",
                "maintenance": "维护部",
                "repair": "维修部",
                "consultation": "技术支持",
                "complaint": "客服部",
            }

            target_dept = type_dept_mapping.get(service_ticket.ticket_type)

            # 查找对应部门的活跃工程师
            engineer_query = self.db.query(User).filter(User.is_active == True)
            if target_dept:
                engineer_query = engineer_query.filter(User.department == target_dept)

            engineers = engineer_query.all()
            if not engineers:
                logger.warning("未找到可分配工程师 (ticket_id=%s, type=%s, dept=%s)",
                               service_ticket.id, service_ticket.ticket_type, target_dept)
                return

            # 负载均衡：选择当前待处理工单最少的工程师
            best_engineer = None
            min_load = float('inf')
            for eng in engineers:
                load = self.db.query(ServiceTicket).filter(
                    ServiceTicket.assigned_to_id == eng.id,
                    ServiceTicket.status.in_(["PENDING", "assigned", "IN_PROGRESS"])
                ).count()
                if load < min_load:
                    min_load = load
                    best_engineer = eng

            if best_engineer:
                service_ticket.assigned_to = str(best_engineer.id)
                service_ticket.assigned_to_id = best_engineer.id
                service_ticket.status = "assigned"
                service_ticket.assigned_time = datetime.now()
                self.db.commit()
                self.db.refresh(service_ticket)
                logger.info("工单已自动分配 (ticket_id=%s, engineer_id=%s, load=%d)",
                            service_ticket.id, best_engineer.id, min_load)

        except Exception as e:
            logger.error("自动分配工单失败 (ticket_id=%s): %s", service_ticket.id, str(e))

    def _send_ticket_notification(self, service_ticket: ServiceTicket, action: str):
        """发送工单通知"""
        try:
            from app.services.unified_notification_service import get_notification_service
            from app.services.channel_handlers.base import NotificationRequest

            notification_service = get_notification_service(self.db)

            action_labels = {
                "created": "新建",
                "assigned": "已分配",
                "closed": "已关闭",
            }
            action_label = action_labels.get(action, action)

            title = f"服务工单{action_label}: {service_ticket.ticket_no}"
            content = (
                f"工单编号: {service_ticket.ticket_no}\n"
                f"问题类型: {service_ticket.problem_type}\n"
                f"状态: {service_ticket.status}\n"
                f"描述: {service_ticket.problem_desc or ''}"
            )

            # 确定通知接收人
            recipient_ids = set()
            if getattr(service_ticket, 'assigned_to_id', None):
                recipient_ids.add(service_ticket.assigned_to_id)
            if getattr(service_ticket, 'reported_by', None):
                try:
                    recipient_ids.add(int(service_ticket.reported_by))
                except (ValueError, TypeError):
                    pass

            for recipient_id in recipient_ids:
                if not recipient_id:
                    continue
                request = NotificationRequest()
                request.recipient_id = recipient_id
                request.notification_type = "service_ticket"
                request.category = "service"
                request.title = title
                request.content = content
                request.priority = "HIGH" if getattr(service_ticket, 'urgency', '') == "URGENT" else "NORMAL"
                request.source_type = "service_ticket"
                request.source_id = service_ticket.id
                notification_service.send_notification(request)

            logger.info("工单通知已发送 (ticket_id=%s, action=%s, recipients=%s)",
                        service_ticket.id, action, recipient_ids)
        except Exception as e:
            logger.error("发送工单通知失败 (ticket_id=%s, action=%s): %s",
                         service_ticket.id, action, str(e))

    def _create_satisfaction_survey(self, service_ticket: ServiceTicket):
        """创建满意度调查 — 工单关闭时自动创建"""
        try:
            today = date.today()
            # 生成调查编号
            count = self.db.query(CustomerSatisfaction).filter(
                func.date(CustomerSatisfaction.created_at) == today
            ).count()
            survey_no = f"SAT{today.strftime('%Y%m%d')}{count + 1:04d}"

            # 获取客户信息
            customer = getattr(service_ticket, 'customer', None)
            customer_name = getattr(customer, 'name', None) or getattr(customer, 'customer_name', '未知客户') if customer else '未知客户'

            # 获取创建人ID
            created_by = None
            if getattr(service_ticket, 'assigned_to_id', None):
                created_by = service_ticket.assigned_to_id
            elif getattr(service_ticket, 'reported_by', None):
                try:
                    created_by = int(service_ticket.reported_by)
                except (ValueError, TypeError):
                    created_by = 1
            else:
                created_by = 1

            survey = CustomerSatisfaction(
                survey_no=survey_no,
                survey_type="service_ticket",
                customer_name=customer_name,
                customer_contact=getattr(customer, 'contact', None) if customer else None,
                customer_email=getattr(customer, 'email', None) if customer else None,
                project_name=getattr(service_ticket, 'project_name', None),
                survey_date=today,
                deadline=today + timedelta(days=7),
                status="PENDING",
                created_by=created_by,
            )

            self.db.add(survey)
            self.db.commit()
            logger.info("满意度调查已创建 (ticket_id=%s, survey_no=%s)",
                        service_ticket.id, survey_no)
        except Exception as e:
            logger.error("创建满意度调查失败 (ticket_id=%s): %s", service_ticket.id, str(e))

    def _calculate_avg_response_time(self) -> float:
        """计算平均响应时间"""
        thirty_days_ago = datetime.now() - timedelta(days=30)

        response_times = self.db.query(ServiceTicket).filter(
            ServiceTicket.created_at >= thirty_days_ago,
            ServiceTicket.assigned_time.isnot(None)
        ).with_entities(
            func.extract('epoch', ServiceTicket.assigned_time - ServiceTicket.created_at)
        ).all()

        if not response_times:
            return 0

        avg_seconds = sum(rt[0] for rt in response_times) / len(response_times)
        return round(avg_seconds / 60, 2)

    def _calculate_satisfaction_rate(self) -> float:
        """计算客户满意度率"""
        thirty_days_ago = datetime.now() - timedelta(days=30)

        satisfactions = self.db.query(CustomerSatisfaction).filter(
            CustomerSatisfaction.created_at >= thirty_days_ago,
            CustomerSatisfaction.overall_score.isnot(None)
        ).with_entities(CustomerSatisfaction.overall_score).all()

        if not satisfactions:
            return 0

        avg_rating = sum(s[0] for s in satisfactions) / len(satisfactions)
        return round(avg_rating, 2)
