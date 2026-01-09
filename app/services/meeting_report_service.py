# -*- coding: utf-8 -*-
"""
会议报告生成服务
"""
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, List
from calendar import monthrange

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from app.models.management_rhythm import (
    StrategicMeeting, MeetingActionItem, MeetingReport, MeetingReportConfig, ReportMetricDefinition
)
from app.models.enums import ActionItemStatus, MeetingRhythmLevel
from app.models.user import User
from app.services.metric_calculation_service import MetricCalculationService
from app.services.comparison_calculation_service import ComparisonCalculationService


class MeetingReportService:
    """会议报告生成服务"""
    
    @staticmethod
    def generate_annual_report(
        db: Session,
        year: int,
        rhythm_level: Optional[str] = None,
        generated_by: int = None,
        config_id: Optional[int] = None
    ) -> MeetingReport:
        """
        生成年度会议报告
        
        Args:
            db: 数据库会话
            year: 报告年份
            rhythm_level: 节律层级筛选（可选）
            generated_by: 生成人ID
            
        Returns:
            MeetingReport对象
        """
        # 计算年度周期
        period_start = date(year, 1, 1)
        period_end = date(year, 12, 31)
        
        # 生成报告编号
        report_no = f"MR-{year}-ANNUAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 查询会议
        query = db.query(StrategicMeeting).filter(
            and_(
                StrategicMeeting.meeting_date >= period_start,
                StrategicMeeting.meeting_date <= period_end
            )
        )
        
        if rhythm_level:
            query = query.filter(StrategicMeeting.rhythm_level == rhythm_level)
        
        meetings = query.order_by(StrategicMeeting.meeting_date).all()
        
        # 统计会议
        total_meetings = len(meetings)
        completed_meetings = len([m for m in meetings if m.status == "COMPLETED"])
        
        # 查询行动项
        meeting_ids = [m.id for m in meetings]
        total_action_items = 0
        completed_action_items = 0
        overdue_action_items = 0
        
        if meeting_ids:
            total_action_items = db.query(MeetingActionItem).filter(
                MeetingActionItem.meeting_id.in_(meeting_ids)
            ).count()
            
            completed_action_items = db.query(MeetingActionItem).filter(
                and_(
                    MeetingActionItem.meeting_id.in_(meeting_ids),
                    MeetingActionItem.status == ActionItemStatus.COMPLETED.value
                )
            ).count()
            
            overdue_action_items = db.query(MeetingActionItem).filter(
                and_(
                    MeetingActionItem.meeting_id.in_(meeting_ids),
                    MeetingActionItem.status == ActionItemStatus.OVERDUE.value
                )
            ).count()
        
        completion_rate = f"{(completed_action_items / total_action_items * 100):.1f}%" if total_action_items > 0 else "0%"
        
        # 收集关键决策
        key_decisions = []
        for meeting in meetings:
            if meeting.key_decisions:
                key_decisions.extend(meeting.key_decisions)
        
        # 收集战略结构
        strategic_structures = []
        for meeting in meetings:
            if meeting.strategic_structure:
                strategic_structures.append({
                    "meeting_id": meeting.id,
                    "meeting_name": meeting.meeting_name,
                    "meeting_date": meeting.meeting_date.isoformat(),
                    "structure": meeting.strategic_structure
                })
        
        # 构建报告数据
        report_data = {
            "summary": {
                "total_meetings": total_meetings,
                "completed_meetings": completed_meetings,
                "completion_rate": f"{(completed_meetings / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%",
                "total_action_items": total_action_items,
                "completed_action_items": completed_action_items,
                "overdue_action_items": overdue_action_items,
                "action_completion_rate": completion_rate
            },
            "meetings": [
                {
                    "id": m.id,
                    "meeting_name": m.meeting_name,
                    "meeting_date": m.meeting_date.isoformat(),
                    "rhythm_level": m.rhythm_level,
                    "cycle_type": m.cycle_type,
                    "status": m.status,
                    "organizer_name": m.organizer_name,
                    "action_items_count": db.query(MeetingActionItem).filter(
                        MeetingActionItem.meeting_id == m.id
                    ).count()
                }
                for m in meetings
            ],
            "action_items_summary": {
                "total": total_action_items,
                "completed": completed_action_items,
                "overdue": overdue_action_items,
                "in_progress": total_action_items - completed_action_items - overdue_action_items
            },
            "key_decisions": key_decisions,
            "strategic_structures": strategic_structures
        }
        
        # 按层级统计
        by_level = {}
        for meeting in meetings:
            level = meeting.rhythm_level
            if level not in by_level:
                by_level[level] = {"total": 0, "completed": 0}
            by_level[level]["total"] += 1
            if meeting.status == "COMPLETED":
                by_level[level]["completed"] += 1
        
        report_data["by_level"] = by_level
        
        # 如果提供了配置ID，根据配置计算业务指标
        comparison_data = None
        if config_id:
            config = db.query(MeetingReportConfig).filter(MeetingReportConfig.id == config_id).first()
            if config and config.enabled_metrics:
                metric_service = MetricCalculationService(db)
                comparison_service = ComparisonCalculationService(db)
                
                # 计算启用的指标
                business_metrics = {}
                metric_codes = [m.get('metric_code') for m in config.enabled_metrics if m.get('enabled', True)]
                
                for metric_code in metric_codes:
                    try:
                        result = metric_service.calculate_metric(metric_code, period_start, period_end)
                        business_metrics[metric_code] = result
                    except Exception as e:
                        business_metrics[metric_code] = {
                            "metric_code": metric_code,
                            "error": str(e),
                            "value": None
                        }
                
                report_data["business_metrics"] = business_metrics
                
                # 计算同比对比（如果配置启用）
                if config.comparison_config and config.comparison_config.get('enable_yoy', False):
                    yoy_comparisons = comparison_service.calculate_comparisons_batch(
                        metric_codes,
                        year,
                        month=None,
                        enable_mom=False,
                        enable_yoy=True
                    )
                    comparison_data = {"yoy_comparisons": yoy_comparisons}
        
        # 创建报告记录
        report = MeetingReport(
            report_no=report_no,
            report_type="ANNUAL",
            report_title=f"{year}年度会议报告" + (f"（{rhythm_level}）" if rhythm_level else ""),
            period_year=year,
            period_month=None,
            period_start=period_start,
            period_end=period_end,
            rhythm_level=rhythm_level or "ALL",
            report_data=report_data,
            comparison_data=comparison_data,
            status="GENERATED",
            generated_by=generated_by,
            generated_at=datetime.now()
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return report
    
    @staticmethod
    def generate_monthly_report(
        db: Session,
        year: int,
        month: int,
        rhythm_level: Optional[str] = None,
        generated_by: int = None,
        config_id: Optional[int] = None
    ) -> MeetingReport:
        """
        生成月度会议报告（包含与上月对比）
        
        Args:
            db: 数据库会话
            year: 报告年份
            month: 报告月份
            rhythm_level: 节律层级筛选（可选）
            generated_by: 生成人ID
            
        Returns:
            MeetingReport对象
        """
        # 计算月度周期
        period_start = date(year, month, 1)
        _, last_day = monthrange(year, month)
        period_end = date(year, month, last_day)
        
        # 计算上月周期（用于对比）
        if month == 1:
            prev_year = year - 1
            prev_month = 12
        else:
            prev_year = year
            prev_month = month - 1
        
        prev_period_start = date(prev_year, prev_month, 1)
        _, prev_last_day = monthrange(prev_year, prev_month)
        prev_period_end = date(prev_year, prev_month, prev_last_day)
        
        # 生成报告编号
        report_no = f"MR-{year}{month:02d}-MONTHLY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 查询本月会议
        current_query = db.query(StrategicMeeting).filter(
            and_(
                StrategicMeeting.meeting_date >= period_start,
                StrategicMeeting.meeting_date <= period_end
            )
        )
        
        if rhythm_level:
            current_query = current_query.filter(StrategicMeeting.rhythm_level == rhythm_level)
        
        current_meetings = current_query.order_by(StrategicMeeting.meeting_date).all()
        
        # 查询上月会议（用于对比）
        prev_query = db.query(StrategicMeeting).filter(
            and_(
                StrategicMeeting.meeting_date >= prev_period_start,
                StrategicMeeting.meeting_date <= prev_period_end
            )
        )
        
        if rhythm_level:
            prev_query = prev_query.filter(StrategicMeeting.rhythm_level == rhythm_level)
        
        prev_meetings = prev_query.all()
        
        # 统计本月数据
        current_total_meetings = len(current_meetings)
        current_completed_meetings = len([m for m in current_meetings if m.status == "COMPLETED"])
        
        current_meeting_ids = [m.id for m in current_meetings]
        current_total_action_items = 0
        current_completed_action_items = 0
        current_overdue_action_items = 0
        
        if current_meeting_ids:
            current_total_action_items = db.query(MeetingActionItem).filter(
                MeetingActionItem.meeting_id.in_(current_meeting_ids)
            ).count()
            
            current_completed_action_items = db.query(MeetingActionItem).filter(
                and_(
                    MeetingActionItem.meeting_id.in_(current_meeting_ids),
                    MeetingActionItem.status == ActionItemStatus.COMPLETED.value
                )
            ).count()
            
            current_overdue_action_items = db.query(MeetingActionItem).filter(
                and_(
                    MeetingActionItem.meeting_id.in_(current_meeting_ids),
                    MeetingActionItem.status == ActionItemStatus.OVERDUE.value
                )
            ).count()
        
        current_completion_rate = (
            (current_completed_action_items / current_total_action_items * 100)
            if current_total_action_items > 0 else 0.0
        )
        
        # 统计上月数据（用于对比）
        prev_total_meetings = len(prev_meetings)
        prev_completed_meetings = len([m for m in prev_meetings if m.status == "COMPLETED"])
        
        prev_meeting_ids = [m.id for m in prev_meetings]
        prev_total_action_items = 0
        prev_completed_action_items = 0
        
        if prev_meeting_ids:
            prev_total_action_items = db.query(MeetingActionItem).filter(
                MeetingActionItem.meeting_id.in_(prev_meeting_ids)
            ).count()
            
            prev_completed_action_items = db.query(MeetingActionItem).filter(
                and_(
                    MeetingActionItem.meeting_id.in_(prev_meeting_ids),
                    MeetingActionItem.status == ActionItemStatus.COMPLETED.value
                )
            ).count()
        
        prev_completion_rate = (
            (prev_completed_action_items / prev_total_action_items * 100)
            if prev_total_action_items > 0 else 0.0
        )
        
        # 构建对比数据
        def calculate_change(current, previous):
            """计算变化"""
            change = current - previous
            change_rate = (change / previous * 100) if previous > 0 else (100 if current > 0 else 0)
            return {
                "current": current,
                "previous": previous,
                "change": change,
                "change_rate": f"{change_rate:+.1f}%",
                "change_abs": abs(change)
            }
        
        comparison_data = {
            "previous_period": f"{prev_year}-{prev_month:02d}",
            "current_period": f"{year}-{month:02d}",
            "meetings_comparison": calculate_change(current_total_meetings, prev_total_meetings),
            "completed_meetings_comparison": calculate_change(current_completed_meetings, prev_completed_meetings),
            "action_items_comparison": calculate_change(current_total_action_items, prev_total_action_items),
            "completed_action_items_comparison": calculate_change(current_completed_action_items, prev_completed_action_items),
            "completion_rate_comparison": {
                "current": f"{current_completion_rate:.1f}%",
                "previous": f"{prev_completion_rate:.1f}%",
                "change": f"{current_completion_rate - prev_completion_rate:+.1f}%",
                "change_value": current_completion_rate - prev_completion_rate
            }
        }
        
        # 收集关键决策
        key_decisions = []
        for meeting in current_meetings:
            if meeting.key_decisions:
                key_decisions.extend(meeting.key_decisions)
        
        # 构建报告数据
        report_data = {
            "summary": {
                "total_meetings": current_total_meetings,
                "completed_meetings": current_completed_meetings,
                "completion_rate": f"{(current_completed_meetings / current_total_meetings * 100):.1f}%" if current_total_meetings > 0 else "0%",
                "total_action_items": current_total_action_items,
                "completed_action_items": current_completed_action_items,
                "overdue_action_items": current_overdue_action_items,
                "action_completion_rate": f"{current_completion_rate:.1f}%"
            },
            "meetings": [
                {
                    "id": m.id,
                    "meeting_name": m.meeting_name,
                    "meeting_date": m.meeting_date.isoformat(),
                    "rhythm_level": m.rhythm_level,
                    "cycle_type": m.cycle_type,
                    "status": m.status,
                    "organizer_name": m.organizer_name,
                    "action_items_count": db.query(MeetingActionItem).filter(
                        MeetingActionItem.meeting_id == m.id
                    ).count()
                }
                for m in current_meetings
            ],
            "action_items_summary": {
                "total": current_total_action_items,
                "completed": current_completed_action_items,
                "overdue": current_overdue_action_items,
                "in_progress": current_total_action_items - current_completed_action_items - current_overdue_action_items
            },
            "key_decisions": key_decisions
        }
        
        # 按层级统计
        by_level = {}
        for meeting in current_meetings:
            level = meeting.rhythm_level
            if level not in by_level:
                by_level[level] = {"total": 0, "completed": 0}
            by_level[level]["total"] += 1
            if meeting.status == "COMPLETED":
                by_level[level]["completed"] += 1
        
        report_data["by_level"] = by_level
        
        # 如果提供了配置ID，根据配置计算业务指标
        if config_id:
            config = db.query(MeetingReportConfig).filter(MeetingReportConfig.id == config_id).first()
            if config and config.enabled_metrics:
                metric_service = MetricCalculationService(db)
                comparison_service = ComparisonCalculationService(db)
                
                period_start = date(year, month, 1)
                _, last_day = monthrange(year, month)
                period_end = date(year, month, last_day)
                
                # 计算启用的指标
                business_metrics = {}
                metric_codes = [m.get('metric_code') for m in config.enabled_metrics if m.get('enabled', True)]
                
                for metric_code in metric_codes:
                    try:
                        result = metric_service.calculate_metric(metric_code, period_start, period_end)
                        business_metrics[metric_code] = result
                    except Exception as e:
                        business_metrics[metric_code] = {
                            "metric_code": metric_code,
                            "error": str(e),
                            "value": None
                        }
                
                report_data["business_metrics"] = business_metrics
                
                # 计算对比数据（如果配置启用）
                if config.comparison_config:
                    enable_mom = config.comparison_config.get('enable_mom', False)
                    enable_yoy = config.comparison_config.get('enable_yoy', False)
                    
                    if enable_mom or enable_yoy:
                        comparisons = comparison_service.calculate_comparisons_batch(
                            metric_codes,
                            year,
                            month=month,
                            enable_mom=enable_mom,
                            enable_yoy=enable_yoy
                        )
                        
                        # 合并到comparison_data中
                        if not comparison_data:
                            comparison_data = {}
                        comparison_data["business_metrics_comparison"] = comparisons
        
        # 创建报告记录
        report = MeetingReport(
            report_no=report_no,
            report_type="MONTHLY",
            report_title=f"{year}年{month}月会议报告" + (f"（{rhythm_level}）" if rhythm_level else ""),
            period_year=year,
            period_month=month,
            period_start=period_start,
            period_end=period_end,
            rhythm_level=rhythm_level or "ALL",
            report_data=report_data,
            comparison_data=comparison_data,
            status="GENERATED",
            generated_by=generated_by,
            generated_at=datetime.now()
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return report
