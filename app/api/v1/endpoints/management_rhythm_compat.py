# -*- coding: utf-8 -*-
"""Compatibility routes for management rhythm demo pages."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from app.api import deps
from app.models.user import User

router = APIRouter()


def _meetings() -> List[Dict[str, Any]]:
    today = date.today()
    return [
        {
            "id": 1,
            "rhythm_level": "STRATEGIC",
            "cycle_type": "QUARTERLY",
            "meeting_name": "季度战略复盘会",
            "meeting_date": (today - timedelta(days=5)).isoformat(),
            "start_time": "09:00:00",
            "status": "COMPLETED",
            "organizer_name": "总经理办公室",
            "action_items_count": 8,
            "completed_action_items_count": 6,
        },
        {
            "id": 2,
            "rhythm_level": "OPERATIONAL",
            "cycle_type": "MONTHLY",
            "meeting_name": "月度经营分析会",
            "meeting_date": (today + timedelta(days=2)).isoformat(),
            "start_time": "14:00:00",
            "status": "SCHEDULED",
            "organizer_name": "经营管理部",
            "action_items_count": 6,
            "completed_action_items_count": 2,
        },
        {
            "id": 3,
            "rhythm_level": "OPERATION",
            "cycle_type": "WEEKLY",
            "meeting_name": "交付与生产协同周会",
            "meeting_date": (today + timedelta(days=4)).isoformat(),
            "start_time": "10:30:00",
            "status": "SCHEDULED",
            "organizer_name": "项目管理部",
            "action_items_count": 10,
            "completed_action_items_count": 7,
        },
        {
            "id": 4,
            "rhythm_level": "TASK",
            "cycle_type": "DAILY",
            "meeting_name": "重点项目站会",
            "meeting_date": today.isoformat(),
            "start_time": "08:45:00",
            "status": "ONGOING",
            "organizer_name": "项目经理",
            "action_items_count": 5,
            "completed_action_items_count": 3,
        },
    ]


def _filtered_meetings(rhythm_level: Optional[str] = None, cycle_type: Optional[str] = None) -> List[Dict[str, Any]]:
    items = _meetings()
    if rhythm_level:
        items = [item for item in items if item["rhythm_level"] == rhythm_level]
    if cycle_type:
        items = [item for item in items if item["cycle_type"] == cycle_type]
    return items


def _group_by(items: List[Dict[str, Any]], field: str) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault(str(item[field]), []).append(item)
    return grouped


def _reports() -> List[Dict[str, Any]]:
    today = date.today()
    month_start = today.replace(day=1)
    last_month_end = month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    year_start = today.replace(month=1, day=1)
    return [
        {
            "id": 1,
            "report_no": f"MR-{today.year}-{today.month:02d}-001",
            "report_type": "MONTHLY",
            "report_title": f"{today.year}年{today.month}月管理节奏报告",
            "period_year": today.year,
            "period_month": today.month,
            "period_start": month_start.isoformat(),
            "period_end": today.isoformat(),
            "rhythm_level": "OPERATIONAL",
            "status": "GENERATED",
            "generated_at": today.isoformat(),
            "published_at": None,
            "report_data": {
                "summary": {
                    "total_meetings": 18,
                    "completed_meetings": 14,
                    "total_action_items": 62,
                    "completed_action_items": 49,
                    "action_completion_rate": "79.0%",
                }
            },
            "comparison_data": {
                "previous_period": f"{last_month_start.isoformat()} ~ {last_month_end.isoformat()}",
                "meetings_comparison": {"change": 3, "change_rate": "20.0%"},
                "completed_meetings_comparison": {"change": 2, "change_rate": "16.7%"},
                "action_items_comparison": {"change": 8, "change_rate": "14.8%"},
                "completion_rate_comparison": {
                    "current": "79.0%",
                    "previous": "75.4%",
                    "change": "+3.6pct",
                    "change_value": 3.6,
                },
            },
        },
        {
            "id": 2,
            "report_no": f"MR-{today.year}-YTD",
            "report_type": "ANNUAL",
            "report_title": f"{today.year}年度管理节奏执行看板",
            "period_year": today.year,
            "period_month": None,
            "period_start": year_start.isoformat(),
            "period_end": today.isoformat(),
            "rhythm_level": "STRATEGIC",
            "status": "PUBLISHED",
            "generated_at": (today - timedelta(days=1)).isoformat(),
            "published_at": today.isoformat(),
            "report_data": {
                "summary": {
                    "total_meetings": 96,
                    "completed_meetings": 82,
                    "total_action_items": 318,
                    "completed_action_items": 266,
                    "action_completion_rate": "83.6%",
                }
            },
            "comparison_data": None,
        },
    ]


@router.get("/meeting-reports")
def list_meeting_reports(
    page: int = 1,
    page_size: int = 20,
    report_type: Optional[str] = None,
    period_year: Optional[int] = None,
    rhythm_level: Optional[str] = None,
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    items = _reports()
    if report_type:
        items = [item for item in items if item["report_type"] == report_type]
    if period_year:
        items = [item for item in items if item["period_year"] == period_year]
    if rhythm_level:
        items = [item for item in items if item["rhythm_level"] == rhythm_level]

    total = len(items)
    start = max(page - 1, 0) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/meeting-reports/{report_id}")
def get_meeting_report(
    report_id: int,
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    return next((item for item in _reports() if item["id"] == report_id), _reports()[0])


@router.post("/meeting-reports/generate")
def generate_meeting_report(
    _payload: Dict[str, Any],
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    return {"message": "报告已生成", "report": _reports()[0]}


@router.get("/meeting-reports/{report_id}/export-docx")
def export_meeting_report(
    report_id: int,
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    report = next((item for item in _reports() if item["id"] == report_id), _reports()[0])
    return {"message": "演示环境已生成导出任务", "report_id": report["id"]}
