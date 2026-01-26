# -*- coding: utf-8 -*-
"""
问题统计端点

包含：统计概览、工程师设计问题分析、原因分析、快照
"""

import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.issue import Issue, IssueStatisticsSnapshot
from app.models.user import User
from app.schemas.issue import (
    EngineerIssueStatistics,
    IssueResponse,
    IssueStatistics,
    IssueStatisticsSnapshotListResponse,
    IssueStatisticsSnapshotResponse,
)
from app.services.data_scope import DataScopeService
from app.services.issue_cost_service import IssueCostService

router = APIRouter()


@router.get("/statistics/overview", response_model=IssueStatistics)
def get_issue_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    project_id: Optional[int] = Query(None, description="项目ID"),
) -> Any:
    """获取问题统计"""
    query = db.query(Issue)
    query = query.filter(Issue.status != 'DELETED')
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)
    if project_id:
        query = query.filter(Issue.project_id == project_id)

    total = query.count()
    open_count = query.filter(Issue.status == 'OPEN').count()
    processing_count = query.filter(Issue.status == 'PROCESSING').count()
    resolved_count = query.filter(Issue.status == 'RESOLVED').count()
    closed_count = query.filter(Issue.status == 'CLOSED').count()
    overdue_count = query.filter(
        and_(
            Issue.due_date.isnot(None),
            Issue.due_date < date.today(),
            Issue.status.in_(['OPEN', 'PROCESSING'])
        )
    ).count()
    blocking_count = query.filter(Issue.is_blocking == True).count()

    # 按严重程度统计
    by_severity = {}
    for severity in ['CRITICAL', 'MAJOR', 'MINOR']:
        by_severity[severity] = query.filter(Issue.severity == severity).count()

    # 按分类统计
    by_category = {}
    categories = query.with_entities(Issue.category).distinct().all()
    for cat in categories:
        by_category[cat[0]] = query.filter(Issue.category == cat[0]).count()

    # 按类型统计
    by_type = {}
    types = query.with_entities(Issue.issue_type).distinct().all()
    for t in types:
        by_type[t[0]] = query.filter(Issue.issue_type == t[0]).count()

    return IssueStatistics(
        total=total,
        open=open_count,
        processing=processing_count,
        resolved=resolved_count,
        closed=closed_count,
        overdue=overdue_count,
        blocking=blocking_count,
        by_severity=by_severity,
        by_category=by_category,
        by_type=by_type,
    )


@router.get("/statistics/engineer-design-issues", response_model=List[EngineerIssueStatistics])
def get_engineer_design_issues_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    engineer_id: Optional[int] = Query(None, description="工程师ID（可选，不提供则统计所有工程师）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID"),
) -> Any:
    """
    按工程师统计设计问题及其导致的损失

    统计root_cause='DESIGN_ERROR'的问题，按responsible_engineer_id分组，
    汇总库存损失和额外工时
    """
    # 查询设计问题
    query = db.query(Issue).filter(
        Issue.root_cause == 'DESIGN_ERROR',
        Issue.status != 'DELETED'
    )
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)

    # 筛选条件
    if engineer_id:
        query = query.filter(Issue.responsible_engineer_id == engineer_id)
    if project_id:
        query = query.filter(Issue.project_id == project_id)
    if start_date:
        query = query.filter(Issue.report_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Issue.report_date <= datetime.combine(end_date, datetime.max.time()))

    issues = query.all()

    # 按工程师分组统计
    engineer_stats = {}
    for issue in issues:
        if not issue.responsible_engineer_id:
            continue

        eng_id = issue.responsible_engineer_id
        if eng_id not in engineer_stats:
            engineer_stats[eng_id] = {
                'engineer_id': eng_id,
                'engineer_name': issue.responsible_engineer_name or '未知',
                'total_issues': 0,
                'design_issues': 0,
                'total_inventory_loss': Decimal(0),
                'total_extra_hours': Decimal(0),
                'issues': []
            }

        stats = engineer_stats[eng_id]
        stats['total_issues'] += 1
        stats['design_issues'] += 1

        # 累加预估的库存损失和额外工时
        if issue.estimated_inventory_loss:
            stats['total_inventory_loss'] += issue.estimated_inventory_loss or Decimal(0)
        if issue.estimated_extra_hours:
            stats['total_extra_hours'] += issue.estimated_extra_hours or Decimal(0)

        # 从关联的成本和工时记录中获取实际损失
        try:
            cost_summary = IssueCostService.get_issue_cost_summary(db, issue.issue_no)
            if cost_summary.get('inventory_loss', 0) > 0:
                stats['total_inventory_loss'] += cost_summary['inventory_loss']
            if cost_summary.get('total_hours', 0) > 0:
                stats['total_extra_hours'] += cost_summary['total_hours']
        except Exception as e:
            # 如果查询失败，只记录错误，不影响统计
            logging.warning(f"Failed to get cost summary for issue {issue.issue_no}: {e}")

        # 构建问题响应
        issue_response = IssueResponse(
            id=issue.id,
            issue_no=issue.issue_no,
            category=issue.category,
            project_id=issue.project_id,
            machine_id=issue.machine_id,
            task_id=issue.task_id,
            acceptance_order_id=issue.acceptance_order_id,
            related_issue_id=issue.related_issue_id,
            issue_type=issue.issue_type,
            severity=issue.severity,
            priority=issue.priority,
            title=issue.title,
            description=issue.description,
            reporter_id=issue.reporter_id,
            reporter_name=issue.reporter_name,
            report_date=issue.report_date,
            assignee_id=issue.assignee_id,
            assignee_name=issue.assignee_name,
            due_date=issue.due_date,
            status=issue.status,
            solution=issue.solution,
            resolved_at=issue.resolved_at,
            resolved_by=issue.resolved_by,
            resolved_by_name=issue.resolved_by_name,
            verified_at=issue.verified_at,
            verified_by=issue.verified_by,
            verified_by_name=issue.verified_by_name,
            verified_result=issue.verified_result,
            follow_up_count=issue.follow_up_count,
            last_follow_up_at=issue.last_follow_up_at,
            impact_scope=issue.impact_scope,
            impact_level=issue.impact_level,
            is_blocking=issue.is_blocking,
            attachments=json.loads(issue.attachments) if issue.attachments else [],
            tags=json.loads(issue.tags) if issue.tags else [],
            root_cause=issue.root_cause,
            responsible_engineer_id=issue.responsible_engineer_id,
            responsible_engineer_name=issue.responsible_engineer_name,
            estimated_inventory_loss=issue.estimated_inventory_loss,
            estimated_extra_hours=issue.estimated_extra_hours,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            project_code=issue.project.project_code if issue.project else None,
            project_name=issue.project.project_name if issue.project else None,
            machine_code=issue.machine.machine_code if issue.machine else None,
            machine_name=issue.machine.machine_name if issue.machine else None,
        )
        stats['issues'].append(issue_response)

    # 转换为响应列表
    result = [EngineerIssueStatistics(**stats) for stats in engineer_stats.values()]

    # 按设计问题数降序排序
    result.sort(key=lambda x: x.design_issues, reverse=True)

    return result


@router.get("/statistics/cause-analysis", response_model=dict)
def get_issue_cause_analysis(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    top_n: int = Query(10, ge=1, le=50, description="返回Top N原因"),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """获取问题原因分析（Top N原因统计）"""
    query = db.query(Issue).filter(Issue.status != 'DELETED')
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)

    if project_id:
        query = query.filter(Issue.project_id == project_id)
    if start_date:
        query = query.filter(Issue.report_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Issue.report_date <= datetime.combine(end_date, datetime.max.time()))

    issues = query.all()

    # 分析问题原因（从描述、解决方案、影响范围等字段提取）
    # 这里使用简单的关键词匹配，实际可以使用NLP技术
    cause_keywords = {
        '设计': ['设计', '图纸', '规格', '参数', '方案'],
        '工艺': ['工艺', '加工', '装配', '焊接', '涂装'],
        '物料': ['物料', '材料', '零件', '配件', '缺料'],
        '质量': ['质量', '缺陷', '不合格', '不良', '瑕疵'],
        '进度': ['进度', '延期', '延迟', '时间', '计划'],
        '人员': ['人员', '人力', '技能', '培训', '经验'],
        '设备': ['设备', '机器', '工具', '故障', '维护'],
        '沟通': ['沟通', '协调', '配合', '信息', '反馈'],
        '其他': []
    }

    cause_stats = {}
    for keyword, patterns in cause_keywords.items():
        cause_stats[keyword] = {
            "cause": keyword,
            "count": 0,
            "issues": []
        }

    for issue in issues:
        # 合并所有文本字段进行分析
        text_content = f"{issue.description or ''} {issue.solution or ''} {issue.impact_scope or ''}".lower()

        matched = False
        for keyword, patterns in cause_keywords.items():
            if keyword == '其他':
                continue
            for pattern in patterns:
                if pattern in text_content:
                    cause_stats[keyword]["count"] += 1
                    cause_stats[keyword]["issues"].append({
                        "issue_id": issue.id,
                        "issue_no": issue.issue_no,
                        "title": issue.title,
                    })
                    matched = True
                    break
            if matched:
                break

        if not matched:
            cause_stats['其他']["count"] += 1
            cause_stats['其他']["issues"].append({
                "issue_id": issue.id,
                "issue_no": issue.issue_no,
                "title": issue.title,
            })

    # 按数量排序，取Top N
    sorted_causes = sorted(
        [stats for stats in cause_stats.values() if stats["count"] > 0],
        key=lambda x: x["count"],
        reverse=True
    )[:top_n]

    # 计算百分比
    total_issues = len(issues)
    for cause in sorted_causes:
        cause["percentage"] = round((cause["count"] / total_issues * 100) if total_issues > 0 else 0, 2)
        # 只返回问题ID列表，不返回完整问题信息（避免响应过大）
        cause["issue_ids"] = [item["issue_id"] for item in cause["issues"]]
        cause.pop("issues", None)

    return {
        "total_issues": total_issues,
        "top_causes": sorted_causes,
        "analysis_period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
    }


@router.get("/statistics/snapshots", response_model=IssueStatisticsSnapshotListResponse)
def get_issue_statistics_snapshots(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> Any:
    """获取问题统计快照列表"""
    query = db.query(IssueStatisticsSnapshot)
    total = query.count()

    snapshots = (
        query.order_by(
            desc(IssueStatisticsSnapshot.snapshot_date),
            desc(IssueStatisticsSnapshot.id),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items: List[IssueStatisticsSnapshotResponse] = []
    for snapshot in snapshots:
        status_distribution = snapshot.status_distribution or {
            "OPEN": snapshot.open_issues or 0,
            "IN_PROGRESS": snapshot.processing_issues or 0,
            "RESOLVED": snapshot.resolved_issues or 0,
            "CLOSED": snapshot.closed_issues or 0,
            "CANCELLED": snapshot.cancelled_issues or 0,
            "DEFERRED": snapshot.deferred_issues or 0,
        }
        severity_distribution = snapshot.severity_distribution or {
            "CRITICAL": snapshot.critical_issues or 0,
            "MAJOR": snapshot.major_issues or 0,
            "MINOR": snapshot.minor_issues or 0,
        }
        priority_distribution = snapshot.priority_distribution or {
            "URGENT": snapshot.urgent_issues or 0,
            "HIGH": snapshot.high_priority_issues or 0,
            "MEDIUM": snapshot.medium_priority_issues or 0,
            "LOW": snapshot.low_priority_issues or 0,
        }
        category_distribution = snapshot.category_distribution or {
            "PROJECT": snapshot.project_issues or 0,
            "TASK": snapshot.task_issues or 0,
            "ACCEPTANCE": snapshot.acceptance_issues or 0,
        }

        item = IssueStatisticsSnapshotResponse(
            id=snapshot.id,
            snapshot_date=snapshot.snapshot_date,
            total_issues=snapshot.total_issues or 0,
            open_issues=snapshot.open_issues or 0,
            processing_issues=snapshot.processing_issues or 0,
            resolved_issues=snapshot.resolved_issues or 0,
            closed_issues=snapshot.closed_issues or 0,
            cancelled_issues=snapshot.cancelled_issues or 0,
            deferred_issues=snapshot.deferred_issues or 0,
            critical_issues=snapshot.critical_issues or 0,
            major_issues=snapshot.major_issues or 0,
            minor_issues=snapshot.minor_issues or 0,
            urgent_issues=snapshot.urgent_issues or 0,
            high_priority_issues=snapshot.high_priority_issues or 0,
            medium_priority_issues=snapshot.medium_priority_issues or 0,
            low_priority_issues=snapshot.low_priority_issues or 0,
            defect_issues=snapshot.defect_issues or 0,
            risk_issues=snapshot.risk_issues or 0,
            blocker_issues=snapshot.blocker_issues or 0,
            blocking_issues=snapshot.blocking_issues or 0,
            overdue_issues=snapshot.overdue_issues or 0,
            project_issues=snapshot.project_issues or 0,
            task_issues=snapshot.task_issues or 0,
            acceptance_issues=snapshot.acceptance_issues or 0,
            avg_response_time=snapshot.avg_response_time,
            avg_resolve_time=snapshot.avg_resolve_time,
            avg_verify_time=getattr(snapshot, "avg_verify_time", None),
            status_distribution=status_distribution,
            severity_distribution=severity_distribution,
            priority_distribution=priority_distribution,
            category_distribution=category_distribution,
            project_distribution=snapshot.project_distribution or {},
            new_issues_today=snapshot.new_issues_today or 0,
            resolved_today=snapshot.resolved_today or 0,
            closed_today=snapshot.closed_today or 0,
            created_at=snapshot.created_at,
            updated_at=snapshot.updated_at,
        )
        items.append(item)

    pages = (total + page_size - 1) // page_size if page_size else 0
    return IssueStatisticsSnapshotListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
