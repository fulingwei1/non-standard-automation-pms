# -*- coding: utf-8 -*-
"""
缺料告警管理服务
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.common.pagination import get_pagination_params
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.core.config import settings
from app.models.material import BomItem, Material, MaterialShortage
from app.models.production import WorkOrder
from app.models.project import Machine, Project
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.shortage import (
    ArrivalFollowUp,
    MaterialArrival,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageReport,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.shortage import (
    ArrivalFollowUpCreate,
    MaterialArrivalListResponse,
    MaterialArrivalResponse,
    MaterialSubstitutionCreate,
    MaterialSubstitutionListResponse,
    MaterialSubstitutionResponse,
    MaterialTransferCreate,
    MaterialTransferListResponse,
    MaterialTransferResponse,
    ShortageReportCreate,
    ShortageReportListResponse,
    ShortageReportResponse,
)


class ShortageAlertsService:
    """缺料告警管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_shortage_alerts(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        material_id: Optional[int] = None,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> PaginatedResponse:
        """获取缺料告警列表"""
        query = self.db.query(MaterialShortage).options(
            joinedload(MaterialShortage.material),
            joinedload(MaterialShortage.project),
            joinedload(MaterialShortage.machine),
            joinedload(MaterialShortage.assigned_user)
        )

        # 搜索条件
        query = apply_keyword_filter(
            query,
            MaterialShortage,
            keyword,
            ["material_code", "material_name", "shortage_reason"],
        )

        # 筛选条件
        if severity:
            query = query.filter(MaterialShortage.severity == severity)

        if status:
            query = query.filter(MaterialShortage.status == status)

        if material_id:
            query = query.filter(MaterialShortage.material_id == material_id)

        if project_id:
            query = query.filter(MaterialShortage.project_id == project_id)

        if start_date:
            query = query.filter(MaterialShortage.created_at >= start_date)

        if end_date:
            query = query.filter(MaterialShortage.created_at <= end_date)

        # 按创建时间倒序
        query = query.order_by(MaterialShortage.created_at.desc())

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
            items=[self._format_shortage_alert(item) for item in items]
        )

    def get_shortage_alert(self, alert_id: int) -> Optional[dict]:
        """获取单个缺料告警"""
        shortage = self.db.query(MaterialShortage).options(
            joinedload(MaterialShortage.material),
            joinedload(MaterialShortage.project),
            joinedload(MaterialShortage.machine),
            joinedload(MaterialShortage.assigned_user),
            joinedload(MaterialShortage.acknowledged_by_user),
            joinedload(MaterialShortage.resolved_by_user)
        ).filter(MaterialShortage.id == alert_id).first()

        if not shortage:
            return None

        return self._format_shortage_alert(shortage)

    def acknowledge_shortage_alert(
        self,
        alert_id: int,
        current_user: User,
        note: Optional[str] = None
    ) -> Optional[dict]:
        """确认缺料告警"""
        shortage = self.db.query(MaterialShortage).filter(
            MaterialShortage.id == alert_id
        ).first()

        if not shortage:
            return None

        if shortage.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="只能确认待处理状态的告警"
            )

        shortage.status = "acknowledged"
        shortage.acknowledged_by = current_user.id
        shortage.acknowledged_at = datetime.now(timezone.utc)
        shortage.acknowledgment_note = note
        shortage.updated_by = current_user.id
        shortage.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(shortage)

        # 发送通知
        self._send_notification(shortage, "acknowledged")

        return self._format_shortage_alert(shortage)

    def update_shortage_alert(
        self,
        alert_id: int,
        update_data: dict,
        current_user: User
    ) -> Optional[dict]:
        """更新缺料告警"""
        shortage = self.db.query(MaterialShortage).filter(
            MaterialShortage.id == alert_id
        ).first()

        if not shortage:
            return None

        # 更新字段
        for field, value in update_data.items():
            if hasattr(shortage, field) and field not in ['id', 'created_at', 'created_by']:
                setattr(shortage, field, value)

        shortage.updated_by = current_user.id
        shortage.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(shortage)

        return self._format_shortage_alert(shortage)

    def add_follow_up(
        self,
        alert_id: int,
        follow_up_data: dict,
        current_user: User
    ) -> dict:
        """添加跟进行动"""
        shortage = self.db.query(MaterialShortage).filter(
            MaterialShortage.id == alert_id
        ).first()

        if not shortage:
            raise HTTPException(
                status_code=404,
                detail="缺料告警不存在"
            )

        follow_up = ArrivalFollowUp(
            shortage_id=alert_id,
            follow_up_type=follow_up_data["follow_up_type"],
            description=follow_up_data["description"],
            contact_person=follow_up_data.get("contact_person"),
            contact_method=follow_up_data.get("contact_method"),
            scheduled_time=follow_up_data.get("scheduled_time"),
            created_by=current_user.id,
            status="pending"
        )

        self.db.add(follow_up)
        self.db.commit()
        self.db.refresh(follow_up)

        return {
            "follow_up_id": follow_up.id,
            "message": "跟进行动添加成功"
        }

    def get_follow_ups(self, alert_id: int) -> List[dict]:
        """获取跟进行动列表"""
        follow_ups = self.db.query(ArrivalFollowUp).options(
            joinedload(ArrivalFollowUp.created_by_user)
        ).filter(
            ArrivalFollowUp.shortage_id == alert_id
        ).order_by(ArrivalFollowUp.created_at.desc()).all()

        return [
            {
                "id": fu.id,
                "follow_up_type": fu.follow_up_type,
                "description": fu.description,
                "contact_person": fu.contact_person,
                "contact_method": fu.contact_method,
                "scheduled_time": fu.scheduled_time.isoformat() if fu.scheduled_time else None,
                "status": fu.status,
                "created_by": fu.created_by_user.name if fu.created_by_user else None,
                "created_at": fu.created_at.isoformat(),
                "completed_at": fu.completed_at.isoformat() if fu.completed_at else None
            }
            for fu in follow_ups
        ]

    def resolve_shortage_alert(
        self,
        alert_id: int,
        resolve_data: dict,
        current_user: User
    ) -> Optional[dict]:
        """解决缺料告警"""
        shortage = self.db.query(MaterialShortage).filter(
            MaterialShortage.id == alert_id
        ).first()

        if not shortage:
            return None

        shortage.status = "resolved"
        shortage.resolved_by = current_user.id
        shortage.resolved_at = datetime.now(timezone.utc)
        shortage.resolution_method = resolve_data.get("resolution_method")
        shortage.resolution_note = resolve_data.get("resolution_note")
        shortage.actual_arrival_date = resolve_data.get("actual_arrival_date")
        shortage.updated_by = current_user.id
        shortage.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(shortage)

        # 发送通知
        self._send_notification(shortage, "resolved")

        return self._format_shortage_alert(shortage)

    def get_statistics_overview(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """获取统计概览"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        # 基础查询
        base_query = self.db.query(MaterialShortage).filter(
            MaterialShortage.created_at >= start_date,
            MaterialShortage.created_at <= end_date
        )

        # 总告警数
        total_alerts = base_query.count()

        # 按状态统计
        status_stats = base_query.with_entities(
            MaterialShortage.status,
            func.count(MaterialShortage.id).label('count')
        ).group_by(MaterialShortage.status).all()

        status_distribution = {stat.status: stat.count for stat in status_stats}

        # 按严重程度统计
        severity_stats = base_query.with_entities(
            MaterialShortage.severity,
            func.count(MaterialShortage.id).label('count')
        ).group_by(MaterialShortage.severity).all()

        severity_distribution = {stat.severity: stat.count for stat in severity_stats}

        # 按物料类型统计
        material_type_stats = base_query.join(Material).with_entities(
            Material.material_type,
            func.count(MaterialShortage.id).label('count')
        ).group_by(Material.material_type).all()

        material_type_distribution = {stat.material_type: stat.count for stat in material_type_stats}

        # 平均解决时间
        avg_resolution_time = base_query.filter(
            MaterialShortage.resolved_at.isnot(None)
        ).with_entities(
            func.avg(func.extract('epoch', MaterialShortage.resolved_at - MaterialShortage.created_at))
        ).scalar()

        # 今日新增
        today_alerts = base_query.filter(
            func.date(MaterialShortage.created_at) == date.today()
        ).count()

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_alerts": total_alerts,
            "today_new_alerts": today_alerts,
            "status_distribution": status_distribution,
            "severity_distribution": severity_distribution,
            "material_type_distribution": material_type_distribution,
            "average_resolution_hours": round(avg_resolution_time / 3600, 2) if avg_resolution_time else None
        }

    def get_dashboard_data(self) -> dict:
        """获取仪表板数据"""
        today = date.today()

        # 今日统计
        today_alerts = self.db.query(MaterialShortage).filter(
            func.date(MaterialShortage.created_at) == today
        ).count()

        # 待处理告警
        pending_alerts = self.db.query(MaterialShortage).filter(
            MaterialShortage.status == "pending"
        ).count()

        # 已确认告警
        acknowledged_alerts = self.db.query(MaterialShortage).filter(
            MaterialShortage.status == "acknowledged"
        ).count()

        # 今日解决
        today_resolved = self.db.query(MaterialShortage).filter(
            MaterialShortage.status == "resolved",
            func.date(MaterialShortage.resolved_at) == today
        ).count()

        # 最近7天趋势
        week_trend = []
        for i in range(7):
            date_i = today - timedelta(days=i)
            day_alerts = self.db.query(MaterialShortage).filter(
                func.date(MaterialShortage.created_at) == date_i
            ).count()
            week_trend.append({
                "date": date_i.isoformat(),
                "count": day_alerts
            })

        week_trend.reverse()

        # 紧急告警
        critical_alerts = self.db.query(MaterialShortage).options(
            joinedload(MaterialShortage.material),
            joinedload(MaterialShortage.project),
            joinedload(MaterialShortage.assigned_user)
        ).filter(
            MaterialShortage.severity.in_(["critical", "high"]),
            MaterialShortage.status.in_(["pending", "acknowledged"])
        ).order_by(MaterialShortage.created_at.desc()).limit(10).all()

        return {
            "today_summary": {
                "new_alerts": today_alerts,
                "pending_alerts": pending_alerts,
                "acknowledged_alerts": acknowledged_alerts,
                "resolved_alerts": today_resolved
            },
            "week_trend": week_trend,
            "critical_alerts": [
                {
                    "id": alert.id,
                    "material_name": alert.material_name,
                    "shortage_quantity": alert.shortage_quantity,
                    "severity": alert.severity,
                    "status": alert.status,
                    "project_name": alert.project.name if alert.project else None,
                    "assigned_to": alert.assigned_user.name if alert.assigned_user else None,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in critical_alerts
            ]
        }

    def _format_shortage_alert(self, shortage: MaterialShortage) -> dict:
        """格式化缺料告警数据"""
        return {
            "id": shortage.id,
            "material_id": shortage.material_id,
            "material_code": shortage.material_code,
            "material_name": shortage.material_name,
            "shortage_quantity": shortage.shortage_quantity,
            "required_date": shortage.required_date.isoformat() if shortage.required_date else None,
            "severity": shortage.severity,
            "status": shortage.status,
            "shortage_reason": shortage.shortage_reason,
            "project_id": shortage.project_id,
            "project_name": shortage.project.name if shortage.project else None,
            "machine_id": shortage.machine_id,
            "machine_name": shortage.machine.name if shortage.machine else None,
            "assigned_to": shortage.assigned_user.name if shortage.assigned_user else None,
            "acknowledged_by": shortage.acknowledged_by_user.name if shortage.acknowledged_by_user else None,
            "acknowledged_at": shortage.acknowledged_at.isoformat() if shortage.acknowledged_at else None,
            "acknowledgment_note": shortage.acknowledgment_note,
            "resolved_by": shortage.resolved_by_user.name if shortage.resolved_by_user else None,
            "resolved_at": shortage.resolved_at.isoformat() if shortage.resolved_at else None,
            "resolution_method": shortage.resolution_method,
            "resolution_note": shortage.resolution_note,
            "actual_arrival_date": shortage.actual_arrival_date.isoformat() if shortage.actual_arrival_date else None,
            "created_at": shortage.created_at.isoformat(),
            "updated_at": shortage.updated_at.isoformat() if shortage.updated_at else None
        }

    def _send_notification(self, shortage: MaterialShortage, action: str):
        """发送通知（使用统一通知服务）"""
        try:
            from app.services.notification_dispatcher import NotificationDispatcher
            from app.services.channel_handlers.base import NotificationRequest, NotificationPriority

            dispatcher = NotificationDispatcher(self.db)

            # 确定接收人（负责人或创建人）
            recipient_id = getattr(shortage, 'handler_id', None) or getattr(shortage, 'created_by', None)
            if not recipient_id:
                return

            action_titles = {
                "acknowledged": "物料短缺已确认",
                "resolved": "物料短缺已解决",
            }
            title = action_titles.get(action, f"物料短缺状态更新: {action}")
            material_name = getattr(shortage, 'material_name', '') or getattr(shortage, 'material_code', '')
            content = f"物料: {material_name}\n状态: {action}"

            request = NotificationRequest(
                recipient_id=recipient_id,
                notification_type="SHORTAGE_UPDATE",
                category="alert",
                title=title,
                content=content,
                priority=NotificationPriority.HIGH,
                source_type="shortage",
                source_id=shortage.id,
                link_url=f"/shortage/{shortage.id}",
            )
            dispatcher.send_notification_request(request)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"物料短缺通知发送失败: {e}")
