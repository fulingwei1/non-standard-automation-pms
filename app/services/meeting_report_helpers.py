# -*- coding: utf-8 -*-
"""
会议报告生成辅助函数
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import date, datetime
from calendar import monthrange
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.management_rhythm import StrategicMeeting, MeetingActionItem, MeetingReportConfig
from app.models.enums import ActionItemStatus
from app.services.metric_calculation_service import MetricCalculationService
from app.services.comparison_calculation_service import ComparisonCalculationService


def calculate_periods(year: int, month: int) -> Tuple[date, date, date, date]:
    """
    计算本月和上月的周期
    
    Returns:
        Tuple: (period_start, period_end, prev_period_start, prev_period_end)
    """
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
    
    return period_start, period_end, prev_period_start, prev_period_end


def query_meetings(
    db: Session,
    period_start: date,
    period_end: date,
    rhythm_level: Optional[str] = None
) -> List[StrategicMeeting]:
    """
    查询指定周期内的会议
    
    Returns:
        List[StrategicMeeting]: 会议列表
    """
    query = db.query(StrategicMeeting).filter(
        and_(
            StrategicMeeting.meeting_date >= period_start,
            StrategicMeeting.meeting_date <= period_end
        )
    )
    
    if rhythm_level:
        query = query.filter(StrategicMeeting.rhythm_level == rhythm_level)
    
    return query.order_by(StrategicMeeting.meeting_date).all()


def calculate_meeting_statistics(
    meetings: List[StrategicMeeting]
) -> Tuple[int, int]:
    """
    计算会议统计信息
    
    Returns:
        Tuple[int, int]: (总会议数, 已完成会议数)
    """
    total = len(meetings)
    completed = len([m for m in meetings if m.status == "COMPLETED"])
    return total, completed


def calculate_action_item_statistics(
    db: Session,
    meeting_ids: List[int]
) -> Tuple[int, int, int]:
    """
    计算行动项统计信息
    
    Returns:
        Tuple[int, int, int]: (总行动项数, 已完成数, 逾期数)
    """
    if not meeting_ids:
        return 0, 0, 0
    
    total = db.query(MeetingActionItem).filter(
        MeetingActionItem.meeting_id.in_(meeting_ids)
    ).count()
    
    completed = db.query(MeetingActionItem).filter(
        and_(
            MeetingActionItem.meeting_id.in_(meeting_ids),
            MeetingActionItem.status == ActionItemStatus.COMPLETED.value
        )
    ).count()
    
    overdue = db.query(MeetingActionItem).filter(
        and_(
            MeetingActionItem.meeting_id.in_(meeting_ids),
            MeetingActionItem.status == ActionItemStatus.OVERDUE.value
        )
    ).count()
    
    return total, completed, overdue


def calculate_completion_rate(completed: int, total: int) -> str:
    """
    计算完成率（字符串格式）
    
    Returns:
        str: 完成率（百分比字符串）
    """
    rate = (completed / total * 100) if total > 0 else 0.0
    return f"{rate:.1f}%"


def calculate_change(current: int, previous: int) -> Dict[str, Any]:
    """
    计算变化（用于对比）
    
    Returns:
        dict: 包含当前值、上期值、变化量、变化率的字典
    """
    change = current - previous
    change_rate = (change / previous * 100) if previous > 0 else (100 if current > 0 else 0)
    return {
        "current": current,
        "previous": previous,
        "change": change,
        "change_rate": f"{change_rate:+.1f}%",
        "change_abs": abs(change)
    }


def build_comparison_data(
    year: int,
    month: int,
    prev_year: int,
    prev_month: int,
    current_stats: Dict[str, int],
    prev_stats: Dict[str, int],
    current_completion_rate: float,
    prev_completion_rate: float
) -> Dict[str, Any]:
    """
    构建对比数据
    
    Returns:
        dict: 包含各项对比数据的字典
    """
    return {
        "previous_period": f"{prev_year}-{prev_month:02d}",
        "current_period": f"{year}-{month:02d}",
        "meetings_comparison": calculate_change(
            current_stats['total'], prev_stats['total']
        ),
        "completed_meetings_comparison": calculate_change(
            current_stats['completed'], prev_stats['completed']
        ),
        "action_items_comparison": calculate_change(
            current_stats.get('action_items_total', 0),
            prev_stats.get('action_items_total', 0)
        ),
        "completed_action_items_comparison": calculate_change(
            current_stats.get('action_items_completed', 0),
            prev_stats.get('action_items_completed', 0)
        ),
        "completion_rate_comparison": {
            "current": f"{current_completion_rate:.1f}%",
            "previous": f"{prev_completion_rate:.1f}%",
            "change": f"{current_completion_rate - prev_completion_rate:+.1f}%",
            "change_value": current_completion_rate - prev_completion_rate
        }
    }


def collect_key_decisions(meetings: List[StrategicMeeting]) -> List[str]:
    """
    收集关键决策
    
    Returns:
        List[str]: 关键决策列表
    """
    key_decisions = []
    for meeting in meetings:
        if meeting.key_decisions:
            key_decisions.extend(meeting.key_decisions)
    return key_decisions


def build_meetings_data(
    db: Session,
    meetings: List[StrategicMeeting]
) -> List[Dict[str, Any]]:
    """
    构建会议数据列表
    
    Returns:
        List[Dict]: 会议数据列表
    """
    return [
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
    ]


def calculate_by_level_statistics(
    meetings: List[StrategicMeeting]
) -> Dict[str, Dict[str, int]]:
    """
    按层级统计会议
    
    Returns:
        dict: 层级代码到统计数据的映射
    """
    by_level = {}
    for meeting in meetings:
        level = meeting.rhythm_level
        if level not in by_level:
            by_level[level] = {"total": 0, "completed": 0}
        by_level[level]["total"] += 1
        if meeting.status == "COMPLETED":
            by_level[level]["completed"] += 1
    return by_level


def build_report_summary(
    meeting_stats: Dict[str, int],
    action_item_stats: Dict[str, int],
    completion_rate: float
) -> Dict[str, Any]:
    """
    构建报告摘要
    
    Returns:
        dict: 报告摘要数据
    """
    return {
        "total_meetings": meeting_stats['total'],
        "completed_meetings": meeting_stats['completed'],
        "completion_rate": f"{(meeting_stats['completed'] / meeting_stats['total'] * 100):.1f}%" if meeting_stats['total'] > 0 else "0%",
        "total_action_items": action_item_stats['total'],
        "completed_action_items": action_item_stats['completed'],
        "overdue_action_items": action_item_stats['overdue'],
        "action_completion_rate": f"{completion_rate:.1f}%"
    }


def calculate_business_metrics(
    db: Session,
    config: MeetingReportConfig,
    period_start: date,
    period_end: date
) -> Dict[str, Any]:
    """
    计算业务指标
    
    Returns:
        dict: 业务指标数据
    """
    if not config or not config.enabled_metrics:
        return {}
    
    metric_service = MetricCalculationService(db)
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
    
    return business_metrics


def calculate_metric_comparisons(
    db: Session,
    config_id: int,
    year: int,
    month: int,
    metric_codes: List[str]
) -> Optional[Dict[str, Any]]:
    """
    计算指标对比数据
    
    Returns:
        Optional[Dict]: 对比数据，如果未启用则返回None
    """
    config = db.query(MeetingReportConfig).filter(MeetingReportConfig.id == config_id).first()
    if not config or not config.comparison_config:
        return None
    
    enable_mom = config.comparison_config.get('enable_mom', False)
    enable_yoy = config.comparison_config.get('enable_yoy', False)
    
    if not (enable_mom or enable_yoy):
        return None
    
    comparison_service = ComparisonCalculationService(db)
    comparisons = comparison_service.calculate_comparisons_batch(
        metric_codes,
        year,
        month=month,
        enable_mom=enable_mom,
        enable_yoy=enable_yoy
    )
    
    return comparisons


def collect_strategic_structures(meetings: List[StrategicMeeting]) -> List[Dict[str, Any]]:
    """
    收集战略结构
    
    Returns:
        List[Dict]: 战略结构列表
    """
    strategic_structures = []
    for meeting in meetings:
        if meeting.strategic_structure:
            strategic_structures.append({
                "meeting_id": meeting.id,
                "meeting_name": meeting.meeting_name,
                "meeting_date": meeting.meeting_date.isoformat(),
                "structure": meeting.strategic_structure
            })
    return strategic_structures


def calculate_yoy_comparisons(
    db: Session,
    metric_codes: List[str],
    year: int,
    month: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    计算同比对比数据
    
    Returns:
        Optional[Dict]: 同比对比数据
    """
    comparison_service = ComparisonCalculationService(db)
    yoy_comparisons = comparison_service.calculate_comparisons_batch(
        metric_codes,
        year,
        month=month,
        enable_mom=False,
        enable_yoy=True
    )
    return {"yoy_comparisons": yoy_comparisons}


def create_report_record(
    db: Session,
    report_no: str,
    report_type: str,
    report_title: str,
    period_year: int,
    period_month: Optional[int],
    period_start: date,
    period_end: date,
    rhythm_level: str,
    report_data: Dict[str, Any],
    comparison_data: Optional[Dict[str, Any]],
    generated_by: Optional[int]
) -> 'MeetingReport':
    """
    创建报告记录
    
    Returns:
        MeetingReport: 报告对象
    """
    from app.models.management_rhythm import MeetingReport
    
    report = MeetingReport(
        report_no=report_no,
        report_type=report_type,
        report_title=report_title,
        period_year=period_year,
        period_month=period_month,
        period_start=period_start,
        period_end=period_end,
        rhythm_level=rhythm_level,
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
