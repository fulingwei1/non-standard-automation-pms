# -*- coding: utf-8 -*-
"""
缺料报告管理服务
"""

from typing import Any, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.shortage import ShortageReport
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.shortage import (
    ShortageReportCreate, ShortageReportResponse, ShortageReportListResponse
)


class ShortageReportsService:
    """缺料报告管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_shortage_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        reporter_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> PaginatedResponse:
        """获取缺料报告列表"""
        query = self.db.query(ShortageReport).options(
            joinedload(ShortageReport.reporter),
            joinedload(ShortageReport.confirmer),
            joinedload(ShortageReport.handler),
            joinedload(ShortageReport.resolver)
        )
        
        # 搜索条件
        if keyword:
            query = query.filter(
                or_(
                    ShortageReport.title.ilike(f"%{keyword}%"),
                    ShortageReport.description.ilike(f"%{keyword}%")
                )
            )
        
        # 筛选条件
        if status:
            query = query.filter(ShortageReport.status == status)
        
        if reporter_id:
            query = query.filter(ShortageReport.reporter_id == reporter_id)
        
        if start_date:
            query = query.filter(ShortageReport.created_at >= start_date)
        
        if end_date:
            query = query.filter(ShortageReport.created_at <= end_date)
        
        # 按创建时间倒序
        query = query.order_by(ShortageReport.created_at.desc())
        
        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[ShortageReportResponse.from_orm(item) for item in items]
        )
    
    def create_shortage_report(
        self,
        report_data: ShortageReportCreate,
        current_user: User
    ) -> ShortageReport:
        """创建缺料报告"""
        shortage_report = ShortageReport(
            title=report_data.title,
            description=report_data.description,
            material_id=report_data.material_id,
            shortage_quantity=report_data.shortage_quantity,
            shortage_reason=report_data.shortage_reason,
            impact_assessment=report_data.impact_assessment,
            expected_arrival_date=report_data.expected_arrival_date,
            reporter_id=current_user.id,
            status="pending"
        )
        
        self.db.add(shortage_report)
        self.db.commit()
        self.db.refresh(shortage_report)
        
        return shortage_report
    
    def get_shortage_report(self, report_id: int) -> Optional[ShortageReport]:
        """获取单个缺料报告"""
        return self.db.query(ShortageReport).options(
            joinedload(ShortageReport.reporter),
            joinedload(ShortageReport.confirmer),
            joinedload(ShortageReport.handler),
            joinedload(ShortageReport.resolver)
        ).filter(ShortageReport.id == report_id).first()
    
    def confirm_shortage_report(
        self,
        report_id: int,
        current_user: User
    ) -> Optional[ShortageReport]:
        """确认缺料报告"""
        shortage_report = self.get_shortage_report(report_id)
        if not shortage_report:
            return None
        
        shortage_report.status = "confirmed"
        shortage_report.confirmer_id = current_user.id
        shortage_report.confirmed_at = datetime.utcnow()
        shortage_report.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(shortage_report)
        
        return shortage_report
    
    def handle_shortage_report(
        self,
        report_id: int,
        handle_data: dict,
        current_user: User
    ) -> Optional[ShortageReport]:
        """处理缺料报告"""
        shortage_report = self.get_shortage_report(report_id)
        if not shortage_report:
            return None
        
        shortage_report.status = "handling"
        shortage_report.handler_id = current_user.id
        shortage_report.handling_method = handle_data.get("handling_method")
        shortage_report.handling_note = handle_data.get("handling_note")
        shortage_report.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(shortage_report)
        
        return shortage_report
    
    def resolve_shortage_report(
        self,
        report_id: int,
        resolve_data: dict,
        current_user: User
    ) -> Optional[ShortageReport]:
        """解决缺料报告"""
        shortage_report = self.get_shortage_report(report_id)
        if not shortage_report:
            return None
        
        shortage_report.status = "resolved"
        shortage_report.resolver_id = current_user.id
        shortage_report.resolved_at = datetime.utcnow()
        shortage_report.resolution_method = resolve_data.get("resolution_method")
        shortage_report.resolution_note = resolve_data.get("resolution_note")
        shortage_report.actual_arrival_date = resolve_data.get("actual_arrival_date")
        shortage_report.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(shortage_report)
        
        return shortage_report