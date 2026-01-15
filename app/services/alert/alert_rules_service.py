# -*- coding: utf-8 -*-
"""
预警规则管理服务
"""

from typing import Any, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import or_, and_, func, case

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.project import Project, Machine
from app.models.issue import Issue
from app.models.alert import (
    AlertRule, AlertRuleTemplate, AlertRecord, AlertNotification,
    ExceptionEvent, ExceptionAction, ExceptionEscalation,
    AlertStatistics, ProjectHealthSnapshot, AlertSubscription
)
from app.schemas.alert import (
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse,
    AlertRecordHandle, AlertRecordResponse, AlertRecordListResponse,
    ExceptionEventCreate, ExceptionEventUpdate, ExceptionEventResolve,
    ExceptionEventVerify, ExceptionEventResponse, ExceptionEventListResponse,
    ProjectHealthResponse, AlertStatisticsResponse,
    AlertSubscriptionCreate, AlertSubscriptionUpdate, AlertSubscriptionResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse


class AlertRulesService:
    """预警规则管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_alert_rules(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        rule_type: Optional[str] = None,
        target_type: Optional[str] = None,
        is_enabled: Optional[bool] = None
    ) -> PaginatedResponse:
        """获取预警规则列表"""
        query = self.db.query(AlertRule)
        
        # 搜索条件
        if keyword:
            query = query.filter(
                or_(
                    AlertRule.rule_code.ilike(f"%{keyword}%"),
                    AlertRule.rule_name.ilike(f"%{keyword}%")
                )
            )
        
        # 筛选条件
        if rule_type:
            query = query.filter(AlertRule.rule_type == rule_type)
        
        if target_type:
            query = query.filter(AlertRule.target_type == target_type)
        
        if is_enabled is not None:
            query = query.filter(AlertRule.is_enabled == is_enabled)
        
        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AlertRuleResponse.from_orm(item) for item in items]
        )
    
    def get_alert_rule(self, rule_id: int) -> Optional[AlertRule]:
        """获取单个预警规则"""
        return self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    
    def create_alert_rule(
        self, 
        rule_data: AlertRuleCreate,
        current_user: User
    ) -> AlertRule:
        """创建预警规则"""
        # 生成规则编码
        rule_code = self._generate_rule_code(rule_data.rule_type)
        
        alert_rule = AlertRule(
            rule_code=rule_code,
            rule_name=rule_data.rule_name,
            rule_type=rule_data.rule_type,
            target_type=rule_data.target_type,
            condition_config=rule_data.condition_config,
            notification_config=rule_data.notification_config,
            severity=rule_data.severity,
            is_enabled=rule_data.is_enabled,
            description=rule_data.description,
            created_by=current_user.id
        )
        
        self.db.add(alert_rule)
        self.db.commit()
        self.db.refresh(alert_rule)
        
        return alert_rule
    
    def update_alert_rule(
        self,
        rule_id: int,
        rule_data: AlertRuleUpdate,
        current_user: User
    ) -> Optional[AlertRule]:
        """更新预警规则"""
        alert_rule = self.get_alert_rule(rule_id)
        if not alert_rule:
            return None
        
        # 更新字段
        update_data = rule_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field != 'id':
                setattr(alert_rule, field, value)
        
        alert_rule.updated_by = current_user.id
        alert_rule.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(alert_rule)
        
        return alert_rule
    
    def toggle_alert_rule(self, rule_id: int, current_user: User) -> Optional[AlertRule]:
        """切换预警规则状态"""
        alert_rule = self.get_alert_rule(rule_id)
        if not alert_rule:
            return None
        
        alert_rule.is_enabled = not alert_rule.is_enabled
        alert_rule.updated_by = current_user.id
        alert_rule.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(alert_rule)
        
        return alert_rule
    
    def delete_alert_rule(self, rule_id: int) -> bool:
        """删除预警规则"""
        alert_rule = self.get_alert_rule(rule_id)
        if not alert_rule:
            return False
        
        self.db.delete(alert_rule)
        self.db.commit()
        
        return True
    
    def get_alert_rule_templates(self) -> List[dict]:
        """获取预警规则模板"""
        templates = self.db.query(AlertRuleTemplate).all()
        return [
            {
                "id": template.id,
                "template_name": template.template_name,
                "template_type": template.template_type,
                "target_type": template.target_type,
                "condition_config": template.condition_config,
                "notification_config": template.notification_config,
                "default_severity": template.default_severity
            }
            for template in templates
        ]
    
    def _generate_rule_code(self, rule_type: str) -> str:
        """生成规则编码"""
        # 规则类型编码映射
        type_codes = {
            "project_delay": "PD",
            "cost_overrun": "CO", 
            "quality_issue": "QI",
            "resource_shortage": "RS",
            "safety_incident": "SI",
            "delivery_delay": "DD"
        }
        
        type_code = type_codes.get(rule_type, "AL")
        
        # 获取当天该类型的规则数量
        today = datetime.utcnow().date()
        count = self.db.query(AlertRule).filter(
            AlertRule.rule_type == rule_type,
            func.date(AlertRule.created_at) == today
        ).count()
        
        return f"{type_code}{datetime.utcnow().strftime('%Y%m%d')}{count+1:03d}"