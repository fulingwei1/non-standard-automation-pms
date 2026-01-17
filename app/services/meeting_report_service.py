# -*- coding: utf-8 -*-
"""
会议报告生成服务
"""
from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.enums import ActionItemStatus, MeetingRhythmLevel
from app.models.management_rhythm import (
    MeetingActionItem,
    MeetingReport,
    MeetingReportConfig,
    ReportMetricDefinition,
    StrategicMeeting,
)
from app.models.user import User
from app.services.comparison_calculation_service import ComparisonCalculationService
from app.services.metric_calculation_service import MetricCalculationService


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
        from app.services.meeting_report_helpers import (
            build_meetings_data,
            calculate_action_item_statistics,
            calculate_business_metrics,
            calculate_by_level_statistics,
            calculate_completion_rate,
            calculate_meeting_statistics,
            calculate_yoy_comparisons,
            collect_key_decisions,
            collect_strategic_structures,
            create_report_record,
            query_meetings,
        )

        # 计算年度周期
        period_start = date(year, 1, 1)
        period_end = date(year, 12, 31)

        # 生成报告编号
        report_no = f"MR-{year}-ANNUAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 查询会议
        meetings = query_meetings(db, period_start, period_end, rhythm_level)

        # 统计会议
        total_meetings, completed_meetings = calculate_meeting_statistics(meetings)

        # 查询行动项
        meeting_ids = [m.id for m in meetings]
        total_action_items, completed_action_items, overdue_action_items = calculate_action_item_statistics(
            db, meeting_ids
        )

        completion_rate = calculate_completion_rate(completed_action_items, total_action_items)

        # 收集关键决策和战略结构
        key_decisions = collect_key_decisions(meetings)
        strategic_structures = collect_strategic_structures(meetings)

        # 构建报告数据
        report_data = {
            "summary": {
                "total_meetings": total_meetings,
                "completed_meetings": completed_meetings,
                "completion_rate": calculate_completion_rate(completed_meetings, total_meetings),
                "total_action_items": total_action_items,
                "completed_action_items": completed_action_items,
                "overdue_action_items": overdue_action_items,
                "action_completion_rate": completion_rate
            },
            "meetings": build_meetings_data(db, meetings),
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
        report_data["by_level"] = calculate_by_level_statistics(meetings)

        # 如果提供了配置ID，根据配置计算业务指标
        comparison_data = None
        if config_id:
            config = db.query(MeetingReportConfig).filter(MeetingReportConfig.id == config_id).first()
            if config and config.enabled_metrics:
                business_metrics = calculate_business_metrics(
                    db, config, period_start, period_end
                )
                report_data["business_metrics"] = business_metrics

                # 计算同比对比（如果配置启用）
                if config.comparison_config and config.comparison_config.get('enable_yoy', False):
                    metric_codes = [m.get('metric_code') for m in config.enabled_metrics if m.get('enabled', True)]
                    comparison_data = calculate_yoy_comparisons(
                        db, metric_codes, year, month=None
                    )

        # 创建报告记录
        report = create_report_record(
            db,
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
            generated_by=generated_by
        )

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
        from app.services.meeting_report_helpers import (
            build_comparison_data,
            build_meetings_data,
            build_report_summary,
            calculate_action_item_statistics,
            calculate_by_level_statistics,
            calculate_completion_rate,
            calculate_meeting_statistics,
            calculate_periods,
            collect_key_decisions,
            query_meetings,
        )

        # 计算月度周期
        period_start, period_end, prev_period_start, prev_period_end = calculate_periods(year, month)

        # 计算上月年份和月份（用于对比数据）
        if month == 1:
            prev_year = year - 1
            prev_month = 12
        else:
            prev_year = year
            prev_month = month - 1

        # 生成报告编号
        report_no = f"MR-{year}{month:02d}-MONTHLY-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 查询本月和上月会议
        current_meetings = query_meetings(db, period_start, period_end, rhythm_level)
        prev_meetings = query_meetings(db, prev_period_start, prev_period_end, rhythm_level)

        # 统计本月数据
        current_meeting_stats = calculate_meeting_statistics(current_meetings)
        current_meeting_ids = [m.id for m in current_meetings]
        current_action_item_stats = calculate_action_item_statistics(db, current_meeting_ids)
        current_completion_rate = calculate_completion_rate(
            current_action_item_stats['completed'],
            current_action_item_stats['total']
        )

        # 统计上月数据（用于对比）
        prev_meeting_stats = calculate_meeting_statistics(prev_meetings)
        prev_meeting_ids = [m.id for m in prev_meetings]
        prev_action_item_stats = calculate_action_item_statistics(db, prev_meeting_ids)
        prev_completion_rate = calculate_completion_rate(
            prev_action_item_stats['completed'],
            prev_action_item_stats['total']
        )

        # 构建对比数据
        comparison_data = build_comparison_data(
            year, month, prev_year, prev_month,
            {
                **current_meeting_stats,
                'action_items_total': current_action_item_stats['total'],
                'action_items_completed': current_action_item_stats['completed']
            },
            {
                **prev_meeting_stats,
                'action_items_total': prev_action_item_stats['total'],
                'action_items_completed': prev_action_item_stats['completed']
            },
            current_completion_rate,
            prev_completion_rate
        )

        # 收集关键决策
        key_decisions = collect_key_decisions(current_meetings)

        # 构建报告数据
        report_data = {
            "summary": build_report_summary(
                current_meeting_stats,
                current_action_item_stats,
                current_completion_rate
            ),
            "meetings": build_meetings_data(db, current_meetings),
            "action_items_summary": {
                "total": current_action_item_stats['total'],
                "completed": current_action_item_stats['completed'],
                "overdue": current_action_item_stats['overdue'],
                "in_progress": current_action_item_stats['total'] - current_action_item_stats['completed'] - current_action_item_stats['overdue']
            },
            "key_decisions": key_decisions,
            "by_level": calculate_by_level_statistics(current_meetings)
        }

        # 如果提供了配置ID，根据配置计算业务指标
        if config_id:
            from app.services.meeting_report_helpers import (
                calculate_business_metrics,
                calculate_metric_comparisons,
            )

            business_metrics = calculate_business_metrics(db, config_id, period_start, period_end)
            if business_metrics:
                report_data["business_metrics"] = business_metrics

                # 计算对比数据（如果配置启用）
                config = db.query(MeetingReportConfig).filter(MeetingReportConfig.id == config_id).first()
                if config and config.enabled_metrics:
                    metric_codes = [m.get('metric_code') for m in config.enabled_metrics if m.get('enabled', True)]
                    comparisons = calculate_metric_comparisons(db, config_id, year, month, metric_codes)
                    if comparisons:
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
