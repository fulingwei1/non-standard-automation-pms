# -*- coding: utf-8 -*-
"""
经验教训 API
从 projects/extended.py 拆分
"""

from typing import Any, List, Optional, Dict

from datetime import date, datetime, timedelta

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path, status

from sqlalchemy.orm import Session, joinedload

from sqlalchemy import desc, or_, func

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.project import (


from fastapi import APIRouter

router = APIRouter(
    prefix="/project-lessons",
    tags=["lessons"]
)

# ==================== 路由定义 ====================
# 共 7 个路由

        })

    # 检查资源冲突
    conflicts = []
    recommendations = []

    for resource_id, data in resource_load.items():
        if data['total_allocation'] > 100:
            recommendations.append({
                'type': 'OVER_ALLOCATION',
                'resource_id': resource_id,
                'resource_name': data['resource_name'],
                'current_allocation': data['total_allocation'],
                'recommendation': f"资源 {data['resource_name']} 总分配率 {data['total_allocation']}%，建议调整分配比例或延期部分任务",
                'priority': 'HIGH' if data['total_allocation'] > 150 else 'MEDIUM'
            })

    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'analysis_period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        },
        'resource_summary': {
            'total_resources': len(resource_load),
            'over_allocated_resources': len([r for r in resource_load.values() if r['total_allocation'] > 100]),
            'total_conflicts': len(conflicts),
        },
        'resource_load': list(resource_load.values()),
        'conflicts': conflicts,
        'recommendations': recommendations,
    }


# ==================== 项目关联分析 ====================

@router.get("/{project_id}/relations", response_model=dict)
def get_project_relations(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    relation_type: Optional[str] = Query(None, description="关联类型筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目关联分析
    分析项目之间的关联关系（物料转移、共享资源、共享客户等）
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    relations = []

    # 查找同客户项目
    if project.customer_id:
        same_customer_projects = db.query(Project).filter(
            Project.customer_id == project.customer_id,
            Project.id != project_id,
            Project.is_active == True
        ).limit(10).all()

        for p in same_customer_projects:
            relations.append({
                'relation_type': 'SAME_CUSTOMER',
                'related_project_id': p.id,
                'related_project_code': p.project_code,
                'related_project_name': p.project_name,
                'description': f'同客户项目: {project.customer_name}'
            })

    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'relations': relations,
    }


@router.post("/{project_id}/auto-discover-relations", response_model=dict, status_code=status.HTTP_200_OK)
def auto_discover_project_relations(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    min_confidence: float = Query(0.3, ge=0.0, le=1.0, description="最小置信度阈值"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    自动发现项目关联关系
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    discovered_relations = []

    # 相同客户的项目
    if project.customer_id:
        same_customer = db.query(Project).filter(
            Project.customer_id == project.customer_id,
            Project.id != project_id,
            Project.is_active == True
        ).all()
        for p in same_customer:
            discovered_relations.append({
                'relation_type': 'SAME_CUSTOMER',
                'related_project_id': p.id,
                'related_project_code': p.project_code,
                'confidence': 0.8,
            })

    # 相同项目经理的项目
    if project.pm_id:
        same_pm = db.query(Project).filter(
            Project.pm_id == project.pm_id,
            Project.id != project_id,
            Project.is_active == True
        ).all()
        for p in same_pm:
            discovered_relations.append({
                'relation_type': 'SAME_PM',
                'related_project_id': p.id,
                'related_project_code': p.project_code,
                'confidence': 0.7,
            })

    # 过滤置信度
    final_relations = [r for r in discovered_relations if r['confidence'] >= min_confidence]

    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'min_confidence': min_confidence,
        'total_discovered': len(final_relations),
        'relations': final_relations,
    }


# ==================== 项目风险矩阵 ====================

@router.get("/{project_id}/risk-matrix", response_model=dict)
def get_project_risk_matrix(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    include_closed: bool = Query(False, description="是否包含已关闭风险"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目风险矩阵
    生成项目风险矩阵，按概率和影响程度分类
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    query = db.query(PmoProjectRisk).filter(PmoProjectRisk.project_id == project_id)

    if not include_closed:
        query = query.filter(PmoProjectRisk.status != 'CLOSED')

    risks = query.all()

    risk_matrix = {
        'LOW_LOW': [], 'LOW_MEDIUM': [], 'LOW_HIGH': [],
        'MEDIUM_LOW': [], 'MEDIUM_MEDIUM': [], 'MEDIUM_HIGH': [],
        'HIGH_LOW': [], 'HIGH_MEDIUM': [], 'HIGH_HIGH': [],
    }

    risk_by_level = {'LOW': [], 'MEDIUM': [], 'HIGH': [], 'CRITICAL': []}

    for risk in risks:
        risk_info = {
            'id': risk.id,
            'risk_no': risk.risk_no,
            'risk_name': risk.risk_name,
            'risk_category': risk.risk_category,
            'probability': risk.probability,
            'impact': risk.impact,
            'risk_level': risk.risk_level,
            'status': risk.status,
        }

        prob = risk.probability or 'LOW'
        impact = risk.impact or 'LOW'
        matrix_key = f"{prob}_{impact}"
        if matrix_key in risk_matrix:
            risk_matrix[matrix_key].append(risk_info)

        level = risk.risk_level or 'LOW'
        if level in risk_by_level:
            risk_by_level[level].append(risk_info)

    stats = {
        'total_risks': len(risks),
        'by_level': {level: len(items) for level, items in risk_by_level.items()},
        'critical_risks': len(risk_by_level.get('CRITICAL', [])),
    }

    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'stats': stats,
        'risk_matrix': risk_matrix,
        'risk_by_level': risk_by_level,
    }


# ==================== 项目变更影响分析 ====================

@router.get("/{project_id}/change-impact", response_model=dict)
def get_change_impact_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    change_id: Optional[int] = Query(None, description="变更ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目变更影响分析
    分析项目变更对其他项目、资源、成本等的影响
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    query = db.query(PmoChangeRequest).filter(PmoChangeRequest.project_id == project_id)

    if change_id:
        query = query.filter(PmoChangeRequest.id == change_id)

    changes = query.all()

    impact_analysis = []
    for change in changes:
        impact_analysis.append({
            'change_id': change.id,
            'change_no': change.change_no,
            'change_type': change.change_type,
            'status': change.status,
            'impact_scope': change.impact_scope,
            'cost_impact': float(change.cost_impact) if change.cost_impact else 0,
            'schedule_impact': change.schedule_impact,
        })

    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'total_changes': len(changes),
        'impact_analysis': impact_analysis,
    }


# ==================== 项目概览数据 ====================

@router.get("/{project_id}/summary", response_model=ResponseModel)
def get_project_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目概览数据
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.models.progress import Task
    from app.models.alert import Alert
    from app.models.issue import Issue
    from app.models.project import ProjectDocument, ProjectCost

    project = check_project_access_or_raise(db, current_user, project_id)

    machine_count = db.query(Machine).filter(Machine.project_id == project_id).count()
    milestone_count = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).count()
    completed_milestone_count = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "COMPLETED"
    ).count()

    task_count = db.query(Task).filter(Task.project_id == project_id).count()
    completed_task_count = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == "COMPLETED"
    ).count()

    member_count = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).count()

    alert_count = db.query(Alert).filter(
        Alert.project_id == project_id,
        Alert.status != "RESOLVED"
    ).count()

    issue_count = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status != "CLOSED"
    ).count()

    document_count = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).count()

    costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()
    total_cost = float(sum(cost.cost_amount or 0 for cost in costs))

    return ResponseModel(
        code=200,
        message="获取项目概览成功",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "customer_name": project.customer_name,
            "pm_name": project.pm_name,
            "stage": project.stage or "S1",
            "status": project.status or "ST01",
            "health": project.health,
            "progress_pct": float(project.progress_pct or 0),
            "contract_amount": float(project.contract_amount or 0),
            "machine_count": machine_count,
            "milestone_count": milestone_count,
            "completed_milestone_count": completed_milestone_count,
            "task_count": task_count,
            "completed_task_count": completed_task_count,
            "member_count": member_count,
            "alert_count": alert_count,
            "issue_count": issue_count,
            "document_count": document_count,
            "total_cost": total_cost,
        }
    )


@router.get("/in-production/summary", response_model=ResponseModel)
def get_in_production_projects_summary(
    db: Session = Depends(deps.get_db),
    stage: Optional[str] = Query(None, description="阶段筛选：S4-S8"),
    health: Optional[str] = Query(None, description="健康度筛选：H1-H3"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    在产项目进度汇总（专门给生产总监/经理看）
    """
    query = db.query(Project).filter(
        Project.stage.in_(["S4", "S5", "S6", "S7", "S8"]),
        Project.is_active == True
    )

    from app.services.data_scope_service import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    if stage:
        query = query.filter(Project.stage == stage)
    if health:
        query = query.filter(Project.health == health)

    projects = query.all()

    result = []
    for project in projects:
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project.id,
            ProjectMilestone.status != "COMPLETED"
        ).order_by(ProjectMilestone.planned_date).limit(5).all()

        today = date.today()
        overdue_milestones = [
            m for m in milestones
            if m.planned_date and m.planned_date < today and m.status != "COMPLETED"
        ]

        next_milestone = milestones[0].milestone_name if milestones else None
        next_milestone_date = milestones[0].planned_date if milestones else None

        result.append({
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "stage": project.stage or "S4",
            "health": project.health,
            "progress": float(project.progress_pct or 0),
            "planned_end_date": project.planned_end_date.isoformat() if project.planned_end_date else None,
            "overdue_milestones_count": len(overdue_milestones),
            "next_milestone": next_milestone,
            "next_milestone_date": next_milestone_date.isoformat() if next_milestone_date else None,
        })

    return ResponseModel(
        code=200,
        message="获取在产项目汇总成功",
        data={"total": len(result), "projects": result}
    )


@router.get("/{project_id}/project-dashboard", response_model=ResponseModel)
def get_single_project_dashboard(
    *,
    db: Session = Depends(deps.get_db),

