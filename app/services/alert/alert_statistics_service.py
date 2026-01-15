# -*- coding: utf-8 -*-
"""
告警统计分析服务
"""

from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import or_, and_, func, case, extract

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


class AlertStatisticsService:
    """告警统计分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_alert_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[int] = None
    ) -> dict:
        """获取告警统计信息"""
        if not start_date:
            start_date = datetime.utcnow().date() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow().date()
        
        # 基础查询
        base_query = self.db.query(AlertRecord).filter(
            AlertRecord.created_at >= start_date,
            AlertRecord.created_at <= end_date
        )
        
        if project_id:
            base_query = base_query.filter(AlertRecord.project_id == project_id)
        
        # 总告警数
        total_alerts = base_query.count()
        
        # 按状态统计
        status_stats = base_query.with_entities(
            AlertRecord.status,
            func.count(AlertRecord.id).label('count')
        ).group_by(AlertRecord.status).all()
        
        status_counts = {stat.status: stat.count for stat in status_stats}
        
        # 按严重程度统计
        severity_stats = base_query.with_entities(
            AlertRecord.severity,
            func.count(AlertRecord.id).label('count')
        ).group_by(AlertRecord.severity).all()
        
        severity_counts = {stat.severity: stat.count for stat in severity_stats}
        
        # 按规则类型统计
        rule_type_stats = base_query.join(AlertRule).with_entities(
            AlertRule.rule_type,
            func.count(AlertRecord.id).label('count')
        ).group_by(AlertRule.rule_type).all()
        
        rule_type_counts = {stat.rule_type: stat.count for stat in rule_type_stats}
        
        # 响应时间统计
        response_time_stats = base_query.filter(
            AlertRecord.acknowledged_at.isnot(None)
        ).with_entities(
            func.avg(
                func.extract('epoch', AlertRecord.acknowledged_at - AlertRecord.created_at)
            ).label('avg_response_seconds'),
            func.min(
                func.extract('epoch', AlertRecord.acknowledged_at - AlertRecord.created_at)
            ).label('min_response_seconds'),
            func.max(
                func.extract('epoch', AlertRecord.acknowledged_at - AlertRecord.created_at)
            ).label('max_response_seconds')
        ).first()
        
        # 解决时间统计
        resolution_time_stats = base_query.filter(
            AlertRecord.resolved_at.isnot(None)
        ).with_entities(
            func.avg(
                func.extract('epoch', AlertRecord.resolved_at - AlertRecord.created_at)
            ).label('avg_resolution_seconds'),
            func.min(
                func.extract('epoch', AlertRecord.resolved_at - AlertRecord.created_at)
            ).label('min_resolution_seconds'),
            func.max(
                func.extract('epoch', AlertRecord.resolved_at - AlertRecord.created_at)
            ).label('max_resolution_seconds')
        ).first()
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_alerts": total_alerts,
            "status_distribution": status_counts,
            "severity_distribution": severity_counts,
            "rule_type_distribution": rule_type_counts,
            "response_metrics": {
                "average_response_time": self._format_seconds(response_time_stats.avg_response_seconds) if response_time_stats else None,
                "min_response_time": self._format_seconds(response_time_stats.min_response_seconds) if response_time_stats else None,
                "max_response_time": self._format_seconds(response_time_stats.max_response_seconds) if response_time_stats else None
            },
            "resolution_metrics": {
                "average_resolution_time": self._format_seconds(resolution_time_stats.avg_resolution_seconds) if resolution_time_stats else None,
                "min_resolution_time": self._format_seconds(resolution_time_stats.min_resolution_seconds) if resolution_time_stats else None,
                "max_resolution_time": self._format_seconds(resolution_time_stats.max_resolution_seconds) if resolution_time_stats else None
            }
        }
    
    def get_alert_trends(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "daily",
        project_id: Optional[int] = None
    ) -> dict:
        """获取告警趋势数据"""
        if not start_date:
            start_date = datetime.utcnow().date() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow().date()
        
        # 根据周期选择时间格式
        date_format = {
            "daily": func.date(AlertRecord.created_at),
            "weekly": func.date_trunc('week', AlertRecord.created_at),
            "monthly": func.date_trunc('month', AlertRecord.created_at)
        }.get(period, func.date(AlertRecord.created_at))
        
        # 趋势查询
        base_query = self.db.query(
            date_format.label('period'),
            AlertRecord.status,
            func.count(AlertRecord.id).label('count')
        ).filter(
            AlertRecord.created_at >= start_date,
            AlertRecord.created_at <= end_date
        )
        
        if project_id:
            base_query = base_query.filter(AlertRecord.project_id == project_id)
        
        trend_data = base_query.group_by(
            date_format, AlertRecord.status
        ).order_by(date_format).all()
        
        # 格式化数据
        periods = {}
        for item in trend_data:
            period_key = item.period.isoformat() if hasattr(item.period, 'isoformat') else str(item.period)
            if period_key not in periods:
                periods[period_key] = {}
            periods[period_key][item.status] = item.count
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "granularity": period
            },
            "trend_data": periods
        }
    
    def get_alert_dashboard_data(
        self,
        project_id: Optional[int] = None
    ) -> dict:
        """获取告警仪表板数据"""
        today = datetime.utcnow().date()
        
        # 今日告警统计
        today_alerts_query = self.db.query(AlertRecord).filter(
            func.date(AlertRecord.created_at) == today
        )
        
        if project_id:
            today_alerts_query = today_alerts_query.filter(AlertRecord.project_id == project_id)
        
        today_stats = today_alerts_query.with_entities(
            AlertRecord.status,
            func.count(AlertRecord.id).label('count')
        ).group_by(AlertRecord.status).all()
        
        today_counts = {stat.status: stat.count for stat in today_stats}
        
        # 本周告警趋势
        week_start = today - timedelta(days=today.weekday())
        week_trend = self._get_week_trend(week_start, project_id)
        
        # 严重告警列表
        critical_alerts = self.db.query(AlertRecord).options(
            joinedload(AlertRecord.project),
            joinedload(AlertRecord.assigned_user)
        ).filter(
            AlertRecord.severity.in_(["critical", "high"]),
            AlertRecord.status.in_(["pending", "acknowledged"])
        )
        
        if project_id:
            critical_alerts = critical_alerts.filter(AlertRecord.project_id == project_id)
        
        critical_alerts = critical_alerts.order_by(AlertRecord.created_at.desc()).limit(10).all()
        
        # 处理效率统计
        efficiency_metrics = self._calculate_efficiency_metrics(project_id)
        
        return {
            "today_summary": {
                "total": today_counts.get("pending", 0) + today_counts.get("acknowledged", 0),
                "pending": today_counts.get("pending", 0),
                "acknowledged": today_counts.get("acknowledged", 0),
                "resolved": today_counts.get("resolved", 0)
            },
            "week_trend": week_trend,
            "critical_alerts": [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "severity": alert.severity,
                    "status": alert.status,
                    "project": alert.project.name if alert.project else None,
                    "assigned_to": alert.assigned_user.name if alert.assigned_user else None,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in critical_alerts
            ],
            "efficiency_metrics": efficiency_metrics
        }
    
    def get_response_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[int] = None
    ) -> dict:
        """获取响应时间指标"""
        if not start_date:
            start_date = datetime.utcnow().date() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow().date()
        
        # 响应时间分布
        response_time_query = self.db.query(AlertRecord).filter(
            AlertRecord.acknowledged_at.isnot(None),
            AlertRecord.created_at >= start_date,
            AlertRecord.created_at <= end_date
        )
        
        if project_id:
            response_time_query = response_time_query.filter(AlertRecord.project_id == project_id)
        
        # 计算响应时间分布
        response_times = []
        for alert in response_time_query.all():
            response_time = (alert.acknowledged_at - alert.created_at).total_seconds()
            response_times.append(response_time)
        
        # 计算百分位数
        response_times.sort()
        total_count = len(response_times)
        
        if total_count == 0:
            return {
                "total_responded": 0,
                "response_time_distribution": {},
                "percentile_metrics": {}
            }
        
        # 计算时间分布
        time_ranges = {
            "within_5min": 0,
            "within_30min": 0,
            "within_1hour": 0,
            "within_4hours": 0,
            "within_24hours": 0,
            "over_24hours": 0
        }
        
        for time_seconds in response_times:
            if time_seconds <= 300:  # 5分钟
                time_ranges["within_5min"] += 1
            elif time_seconds <= 1800:  # 30分钟
                time_ranges["within_30min"] += 1
            elif time_seconds <= 3600:  # 1小时
                time_ranges["within_1hour"] += 1
            elif time_seconds <= 14400:  # 4小时
                time_ranges["within_4hours"] += 1
            elif time_seconds <= 86400:  # 24小时
                time_ranges["within_24hours"] += 1
            else:
                time_ranges["over_24hours"] += 1
        
        # 计算百分位数
        percentiles = {}
        if total_count > 0:
            percentiles["50th"] = self._get_percentile(response_times, 50)
            percentiles["90th"] = self._get_percentile(response_times, 90)
            percentiles["95th"] = self._get_percentile(response_times, 95)
            percentiles["99th"] = self._get_percentile(response_times, 99)
        
        return {
            "total_responded": total_count,
            "response_time_distribution": time_ranges,
            "percentile_metrics": percentiles
        }
    
    def get_efficiency_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[int] = None
    ) -> dict:
        """获取效率指标"""
        return self._calculate_efficiency_metrics(project_id, start_date, end_date)
    
    def _get_week_trend(self, week_start: date, project_id: Optional[int] = None) -> List[dict]:
        """获取周趋势数据"""
        week_data = []
        current_day = week_start
        
        for i in range(7):
            day_end = current_day + timedelta(days=1)
            
            query = self.db.query(AlertRecord).filter(
                AlertRecord.created_at >= current_day,
                AlertRecord.created_at < day_end
            )
            
            if project_id:
                query = query.filter(AlertRecord.project_id == project_id)
            
            day_stats = query.with_entities(
                AlertRecord.status,
                func.count(AlertRecord.id).label('count')
            ).group_by(AlertRecord.status).all()
            
            day_counts = {stat.status: stat.count for stat in day_stats}
            
            week_data.append({
                "date": current_day.isoformat(),
                "total": sum(day_counts.values()),
                "pending": day_counts.get("pending", 0),
                "resolved": day_counts.get("resolved", 0)
            })
            
            current_day = day_end
        
        return week_data
    
    def _calculate_efficiency_metrics(
        self, 
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """计算效率指标"""
        if not start_date:
            start_date = datetime.utcnow().date() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow().date()
        
        base_query = self.db.query(AlertRecord).filter(
            AlertRecord.created_at >= start_date,
            AlertRecord.created_at <= end_date
        )
        
        if project_id:
            base_query = base_query.filter(AlertRecord.project_id == project_id)
        
        total_alerts = base_query.count()
        
        # 解决率
        resolved_count = base_query.filter(AlertRecord.status == "resolved").count()
        resolution_rate = (resolved_count / total_alerts * 100) if total_alerts > 0 else 0
        
        # 平均响应时间和解决时间
        avg_response_time = base_query.filter(
            AlertRecord.acknowledged_at.isnot(None)
        ).with_entities(
            func.avg(func.extract('epoch', AlertRecord.acknowledged_at - AlertRecord.created_at))
        ).scalar()
        
        avg_resolution_time = base_query.filter(
            AlertRecord.resolved_at.isnot(None)
        ).with_entities(
            func.avg(func.extract('epoch', AlertRecord.resolved_at - AlertRecord.created_at))
        ).scalar()
        
        return {
            "resolution_rate": round(resolution_rate, 2),
            "average_response_time": self._format_seconds(avg_response_time),
            "average_resolution_time": self._format_seconds(avg_resolution_time),
            "total_processed": total_alerts
        }
    
    def _format_seconds(self, seconds: Optional[float]) -> Optional[str]:
        """格式化秒数为可读格式"""
        if not seconds:
            return None
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{minutes}分钟"
    
    def _get_percentile(self, sorted_list: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not sorted_list:
            return 0
        
        index = int(len(sorted_list) * percentile / 100)
        index = min(index, len(sorted_list) - 1)
        return sorted_list[index]