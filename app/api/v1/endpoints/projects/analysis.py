# -*- coding: utf-8 -*-
"""
项目高级分析端点

包含资源优化、关联分析、风险矩阵、变更影响分析等端点
"""

from typing import Any, Optional
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.models.pmo import PmoResourceAllocation, PmoProjectRisk, PmoChangeRequest

router = APIRouter()


# ==================== 项目资源分配优化 ====================

@router.get("/{project_id}/resource-optimization", response_model=dict)
def get_resource_optimization(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    start_date: Optional[date] = Query(None, description="开始日期（默认：项目开始日期）"),
    end_date: Optional[date] = Query(None, description="结束日期（默认：项目结束日期）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目资源分配优化分析
    分析项目资源分配情况，提供优化建议
    """
    from app.models.progress import Task
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    if not start_date:
        start_date = project.planned_start_date or date.today()
    if not end_date:
        end_date = project.planned_end_date or (date.today() + timedelta(days=90))

    # 获取项目资源分配
    allocations = db.query(PmoResourceAllocation).filter(
        PmoResourceAllocation.project_id == project_id,
        PmoResourceAllocation.start_date <= end_date,
        PmoResourceAllocation.end_date >= start_date,
        PmoResourceAllocation.status != 'CANCELLED'
    ).all()

    # 获取项目任务
    tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.plan_start <= end_date,
        Task.plan_end >= start_date,
        Task.status != 'CANCELLED'
    ).all()

    # 分析资源负荷
    resource_load = {}
    for alloc in allocations:
        resource_id = alloc.resource_id
        if resource_id not in resource_load:
            resource_load[resource_id] = {
                'resource_id': resource_id,
                'resource_name': alloc.resource_name,
                'resource_dept': alloc.resource_dept,
                'total_allocation': 0,
                'allocations': [],
            }

        resource_load[resource_id]['total_allocation'] += alloc.allocation_percent
        resource_load[resource_id]['allocations'].append({
            'id': alloc.id,
            'start_date': alloc.start_date.isoformat() if alloc.start_date else None,
            'end_date': alloc.end_date.isoformat() if alloc.end_date else None,
            'allocation_percent': alloc.allocation_percent,
            'planned_hours': alloc.planned_hours,
            'status': alloc.status,
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
