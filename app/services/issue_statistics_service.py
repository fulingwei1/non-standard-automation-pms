# -*- coding: utf-8 -*-
"""
问题统计服务
"""

from typing import Dict, Any
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.issue import Issue, IssueStatisticsSnapshot


def check_existing_snapshot(
    db: Session,
    snapshot_date: date
) -> bool:
    """
    检查指定日期是否已存在快照
    
    Returns:
        bool: 如果快照已存在返回True
    """
    existing = db.query(IssueStatisticsSnapshot).filter(
        IssueStatisticsSnapshot.snapshot_date == snapshot_date
    ).first()
    return existing is not None


def count_issues_by_status(db: Session) -> Dict[str, int]:
    """
    统计各状态问题数量
    
    Returns:
        Dict[str, int]: 状态统计字典
    """
    return {
        'total': db.query(Issue).filter(Issue.status != 'DELETED').count(),
        'open': db.query(Issue).filter(Issue.status == 'OPEN').count(),
        'processing': db.query(Issue).filter(Issue.status == 'PROCESSING').count(),
        'resolved': db.query(Issue).filter(Issue.status == 'RESOLVED').count(),
        'closed': db.query(Issue).filter(Issue.status == 'CLOSED').count(),
        'cancelled': db.query(Issue).filter(Issue.status == 'CANCELLED').count(),
        'deferred': db.query(Issue).filter(Issue.status == 'DEFERRED').count(),
    }


def count_issues_by_severity(db: Session) -> Dict[str, int]:
    """
    统计严重程度问题数量
    
    Returns:
        Dict[str, int]: 严重程度统计字典
    """
    base_filter = Issue.status != 'DELETED'
    
    return {
        'critical': db.query(Issue).filter(
            Issue.severity == 'CRITICAL',
            base_filter
        ).count(),
        'major': db.query(Issue).filter(
            Issue.severity == 'MAJOR',
            base_filter
        ).count(),
        'minor': db.query(Issue).filter(
            Issue.severity == 'MINOR',
            base_filter
        ).count(),
    }


def count_issues_by_priority(db: Session) -> Dict[str, int]:
    """
    统计优先级问题数量
    
    Returns:
        Dict[str, int]: 优先级统计字典
    """
    base_filter = Issue.status != 'DELETED'
    
    return {
        'urgent': db.query(Issue).filter(
            Issue.priority == 'URGENT',
            base_filter
        ).count(),
        'high': db.query(Issue).filter(
            Issue.priority == 'HIGH',
            base_filter
        ).count(),
        'medium': db.query(Issue).filter(
            Issue.priority == 'MEDIUM',
            base_filter
        ).count(),
        'low': db.query(Issue).filter(
            Issue.priority == 'LOW',
            base_filter
        ).count(),
    }


def count_issues_by_type(db: Session) -> Dict[str, int]:
    """
    统计类型问题数量
    
    Returns:
        Dict[str, int]: 类型统计字典
    """
    base_filter = Issue.status != 'DELETED'
    
    return {
        'defect': db.query(Issue).filter(
            Issue.issue_type == 'DEFECT',
            base_filter
        ).count(),
        'risk': db.query(Issue).filter(
            Issue.issue_type == 'RISK',
            base_filter
        ).count(),
        'blocker': db.query(Issue).filter(
            Issue.issue_type == 'BLOCKER',
            base_filter
        ).count(),
    }


def count_blocking_and_overdue_issues(
    db: Session,
    today: date
) -> Dict[str, int]:
    """
    统计阻塞和逾期问题数量
    
    Returns:
        Dict[str, int]: 阻塞和逾期统计字典
    """
    blocking_count = db.query(Issue).filter(
        Issue.is_blocking == True,
        Issue.status.in_(['OPEN', 'PROCESSING'])
    ).count()
    
    overdue_count = db.query(Issue).filter(
        Issue.status.in_(['OPEN', 'PROCESSING']),
        Issue.due_date.isnot(None),
        Issue.due_date < today
    ).count()
    
    return {
        'blocking': blocking_count,
        'overdue': overdue_count,
    }


def count_issues_by_category(db: Session) -> Dict[str, int]:
    """
    统计分类问题数量
    
    Returns:
        Dict[str, int]: 分类统计字典
    """
    base_filter = Issue.status != 'DELETED'
    
    return {
        'project': db.query(Issue).filter(
            Issue.category == 'PROJECT',
            base_filter
        ).count(),
        'task': db.query(Issue).filter(
            Issue.category == 'TASK',
            base_filter
        ).count(),
        'acceptance': db.query(Issue).filter(
            Issue.category == 'ACCEPTANCE',
            base_filter
        ).count(),
    }


def count_today_issues(db: Session, today: date) -> Dict[str, int]:
    """
    统计今日新增/解决/关闭问题数量
    
    Returns:
        Dict[str, int]: 今日统计字典
    """
    today_start = datetime.combine(today, datetime.min.time())
    
    new_today = db.query(Issue).filter(
        Issue.created_at >= today_start,
        Issue.status != 'DELETED'
    ).count()
    
    resolved_today = db.query(Issue).filter(
        Issue.resolved_at >= today_start,
        Issue.status.in_(['RESOLVED', 'CLOSED'])
    ).count()
    
    closed_today = db.query(Issue).filter(
        Issue.status == 'CLOSED',
        Issue.updated_at >= today_start
    ).count()
    
    return {
        'new': new_today,
        'resolved': resolved_today,
        'closed': closed_today,
    }


def calculate_avg_resolve_time(db: Session) -> float:
    """
    计算平均处理时间（小时）
    
    Returns:
        float: 平均处理时间（小时）
    """
    resolved_issues = db.query(Issue).filter(
        Issue.status.in_(['RESOLVED', 'CLOSED']),
        Issue.resolved_at.isnot(None),
        Issue.report_date.isnot(None)
    ).all()
    
    if not resolved_issues:
        return 0.0
    
    resolve_times = []
    for issue in resolved_issues:
        if issue.resolved_at and issue.report_date:
            delta = issue.resolved_at - issue.report_date
            resolve_times.append(delta.total_seconds() / 3600)  # 转换为小时
    
    return sum(resolve_times) / len(resolve_times) if resolve_times else 0.0


def build_distribution_data(
    status_counts: Dict[str, int],
    severity_counts: Dict[str, int],
    priority_counts: Dict[str, int],
    category_counts: Dict[str, int]
) -> Dict[str, Dict[str, int]]:
    """
    构建分布数据字典
    
    Returns:
        Dict[str, Dict[str, int]]: 分布数据字典
    """
    return {
        'status': {
            'OPEN': status_counts['open'],
            'PROCESSING': status_counts['processing'],
            'RESOLVED': status_counts['resolved'],
            'CLOSED': status_counts['closed'],
            'CANCELLED': status_counts['cancelled'],
            'DEFERRED': status_counts['deferred'],
        },
        'severity': {
            'CRITICAL': severity_counts['critical'],
            'MAJOR': severity_counts['major'],
            'MINOR': severity_counts['minor'],
        },
        'priority': {
            'URGENT': priority_counts['urgent'],
            'HIGH': priority_counts['high'],
            'MEDIUM': priority_counts['medium'],
            'LOW': priority_counts['low'],
        },
        'category': {
            'PROJECT': category_counts['project'],
            'TASK': category_counts['task'],
            'ACCEPTANCE': category_counts['acceptance'],
        },
    }


def create_snapshot_record(
    db: Session,
    snapshot_date: date,
    status_counts: Dict[str, int],
    severity_counts: Dict[str, int],
    priority_counts: Dict[str, int],
    type_counts: Dict[str, int],
    blocking_overdue: Dict[str, int],
    category_counts: Dict[str, int],
    today_counts: Dict[str, int],
    avg_resolve_time: float,
    distributions: Dict[str, Dict[str, int]]
) -> IssueStatisticsSnapshot:
    """
    创建快照记录
    
    Returns:
        IssueStatisticsSnapshot: 快照对象
    """
    import json
    
    snapshot = IssueStatisticsSnapshot(
        snapshot_date=snapshot_date,
        total_issues=status_counts['total'],
        open_issues=status_counts['open'],
        processing_issues=status_counts['processing'],
        resolved_issues=status_counts['resolved'],
        closed_issues=status_counts['closed'],
        cancelled_issues=status_counts['cancelled'],
        deferred_issues=status_counts['deferred'],
        critical_issues=severity_counts['critical'],
        major_issues=severity_counts['major'],
        minor_issues=severity_counts['minor'],
        urgent_issues=priority_counts['urgent'],
        high_priority_issues=priority_counts['high'],
        medium_priority_issues=priority_counts['medium'],
        low_priority_issues=priority_counts['low'],
        defect_issues=type_counts['defect'],
        risk_issues=type_counts['risk'],
        blocker_issues=type_counts['blocker'],
        blocking_issues=blocking_overdue['blocking'],
        overdue_issues=blocking_overdue['overdue'],
        project_issues=category_counts['project'],
        task_issues=category_counts['task'],
        acceptance_issues=category_counts['acceptance'],
        avg_resolve_time=avg_resolve_time,
        status_distribution=json.dumps(distributions['status']),
        severity_distribution=json.dumps(distributions['severity']),
        priority_distribution=json.dumps(distributions['priority']),
        category_distribution=json.dumps(distributions['category']),
        new_issues_today=today_counts['new'],
        resolved_today=today_counts['resolved'],
        closed_today=today_counts['closed'],
    )
    
    db.add(snapshot)
    return snapshot
