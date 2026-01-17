# -*- coding: utf-8 -*-
"""
问题分析端点

包含：看板数据、趋势分析
"""

from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.issue import Issue
from app.models.user import User
from app.services.data_scope_service import DataScopeService

router = APIRouter()


@router.get("/board", response_model=dict)
def get_issue_board(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """获取问题看板数据（按状态分组）"""
    query = db.query(Issue).filter(Issue.status != 'DELETED')
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)

    if project_id:
        query = query.filter(Issue.project_id == project_id)

    issues = query.all()

    # 按状态分组
    board = {
        "OPEN": [],
        "PROCESSING": [],
        "RESOLVED": [],
        "VERIFIED": [],
        "CLOSED": [],
        "CANCELLED": [],
    }

    for issue in issues:
        status = issue.status or "OPEN"
        if status not in board:
            status = "OPEN"

        board[status].append({
            "id": issue.id,
            "issue_no": issue.issue_no,
            "title": issue.title,
            "severity": issue.severity,
            "priority": issue.priority,
            "assignee_name": issue.assignee_name,
            "due_date": issue.due_date.isoformat() if issue.due_date else None,
            "is_blocking": issue.is_blocking,
            "project_name": issue.project.project_name if issue.project else None,
        })

    return {
        "columns": [
            {"key": "OPEN", "title": "待处理", "count": len(board["OPEN"])},
            {"key": "PROCESSING", "title": "处理中", "count": len(board["PROCESSING"])},
            {"key": "RESOLVED", "title": "已解决", "count": len(board["RESOLVED"])},
            {"key": "VERIFIED", "title": "已验证", "count": len(board["VERIFIED"])},
            {"key": "CLOSED", "title": "已关闭", "count": len(board["CLOSED"])},
            {"key": "CANCELLED", "title": "已取消", "count": len(board["CANCELLED"])},
        ],
        "issues": board,
    }


@router.get("/statistics/trend", response_model=dict)
def get_issue_trend(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    group_by: str = Query("day", description="分组方式：day/week/month"),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """获取问题趋势分析数据"""
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    query = db.query(Issue).filter(
        Issue.report_date >= datetime.combine(start_date, datetime.min.time()),
        Issue.report_date <= datetime.combine(end_date, datetime.max.time())
    )
    query = query.filter(Issue.status != 'DELETED')
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)

    if project_id:
        query = query.filter(Issue.project_id == project_id)

    issues = query.all()

    # 按日期分组统计
    trend_data = {}
    for issue in issues:
        report_date = issue.report_date.date() if issue.report_date else date.today()

        # 根据group_by确定分组键
        if group_by == "week":
            days_since_monday = report_date.weekday()
            week_start = report_date - timedelta(days=days_since_monday)
            key = week_start.isoformat()
        elif group_by == "month":
            key = date(report_date.year, report_date.month, 1).isoformat()
        else:  # day
            key = report_date.isoformat()

        if key not in trend_data:
            trend_data[key] = {
                "date": key,
                "created": 0,
                "resolved": 0,
                "closed": 0,
            }

        trend_data[key]["created"] += 1

        if issue.resolved_at:
            resolved_date = issue.resolved_at.date()
            if group_by == "week":
                days_since_monday = resolved_date.weekday()
                week_start = resolved_date - timedelta(days=days_since_monday)
                resolved_key = week_start.isoformat()
            elif group_by == "month":
                resolved_key = date(resolved_date.year, resolved_date.month, 1).isoformat()
            else:
                resolved_key = resolved_date.isoformat()

            if resolved_key not in trend_data:
                trend_data[resolved_key] = {
                    "date": resolved_key,
                    "created": 0,
                    "resolved": 0,
                    "closed": 0,
                }
            trend_data[resolved_key]["resolved"] += 1

        if issue.status == "CLOSED":
            # 假设关闭时间就是更新时间（实际应该有closed_at字段）
            closed_date = issue.updated_at.date() if issue.updated_at else None
            if closed_date:
                if group_by == "week":
                    days_since_monday = closed_date.weekday()
                    week_start = closed_date - timedelta(days=days_since_monday)
                    closed_key = week_start.isoformat()
                elif group_by == "month":
                    closed_key = date(closed_date.year, closed_date.month, 1).isoformat()
                else:
                    closed_key = closed_date.isoformat()

                if closed_key not in trend_data:
                    trend_data[closed_key] = {
                        "date": closed_key,
                        "created": 0,
                        "resolved": 0,
                        "closed": 0,
                    }
                trend_data[closed_key]["closed"] += 1

    # 排序并填充缺失日期
    result = []
    current_date = start_date
    while current_date <= end_date:
        if group_by == "week":
            days_since_monday = current_date.weekday()
            week_start = current_date - timedelta(days=days_since_monday)
            key = week_start.isoformat()
        elif group_by == "month":
            key = date(current_date.year, current_date.month, 1).isoformat()
        else:
            key = current_date.isoformat()

        if key in trend_data:
            result.append(trend_data[key])
        else:
            result.append({
                "date": key,
                "created": 0,
                "resolved": 0,
                "closed": 0,
            })

        if group_by == "week":
            current_date += timedelta(days=7)
        elif group_by == "month":
            # 移动到下个月
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
        else:
            current_date += timedelta(days=1)

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "group_by": group_by,
        "trend": result,
    }
