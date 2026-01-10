# -*- coding: utf-8 -*-
"""
变更影响分析服务
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.progress import Task
from app.models.pmo import PmoChangeRequest, PmoResourceAllocation


def analyze_schedule_impact(
    db: Session,
    change: PmoChangeRequest,
    project_id: int
) -> Optional[Dict[str, Any]]:
    """
    分析进度影响
    
    Returns:
        Optional[Dict]: 进度影响信息
    """
    if not change.schedule_impact:
        return None
    
    impact = {
        'description': change.schedule_impact,
        'affected_items': [],
        'severity': 'HIGH' if change.change_level == 'CRITICAL' else 'MEDIUM',
    }
    
    if change.status == 'APPROVED':
        affected_tasks = db.query(Task).filter(
            Task.project_id == project_id,
            Task.status.in_(['PENDING', 'IN_PROGRESS'])
        ).all()
        
        impact['affected_items'] = [
            {
                'task_id': task.id,
                'task_name': task.task_name,
                'plan_start': task.plan_start.isoformat() if task.plan_start else None,
                'plan_end': task.plan_end.isoformat() if task.plan_end else None,
            }
            for task in affected_tasks[:10]
        ]
    
    return impact


def analyze_cost_impact(
    change: PmoChangeRequest,
    project: Project
) -> Optional[Dict[str, Any]]:
    """
    分析成本影响
    
    Returns:
        Optional[Dict]: 成本影响信息
    """
    if not change.cost_impact:
        return None
    
    cost_impact_value = float(change.cost_impact or 0)
    budget_amount = float(project.budget_amount or 0)
    
    return {
        'cost_impact': cost_impact_value,
        'description': f"预计成本影响：{change.cost_impact}元",
        'severity': 'HIGH' if abs(cost_impact_value) > budget_amount * 0.1 else 'MEDIUM',
    }


def analyze_resource_impact(
    db: Session,
    change: PmoChangeRequest,
    project_id: int
) -> Optional[Dict[str, Any]]:
    """
    分析资源影响
    
    Returns:
        Optional[Dict]: 资源影响信息
    """
    if not change.resource_impact:
        return None
    
    impact = {
        'description': change.resource_impact,
        'affected_resources': [],
        'severity': 'MEDIUM',
    }
    
    if change.status == 'APPROVED':
        affected_allocations = db.query(PmoResourceAllocation).filter(
            PmoResourceAllocation.project_id == project_id,
            PmoResourceAllocation.status != 'CANCELLED'
        ).all()
        
        impact['affected_resources'] = [
            {
                'allocation_id': alloc.id,
                'resource_name': alloc.resource_name,
                'allocation_percent': alloc.allocation_percent,
                'start_date': alloc.start_date.isoformat() if alloc.start_date else None,
                'end_date': alloc.end_date.isoformat() if alloc.end_date else None,
            }
            for alloc in affected_allocations[:10]
        ]
    
    return impact


def analyze_related_project_impact(
    db: Session,
    change: PmoChangeRequest,
    project_id: int
) -> Dict[str, Any]:
    """
    分析关联项目影响
    
    Returns:
        Dict: 关联项目影响信息
    """
    related_project_impacts = []
    
    if change.resource_impact and change.status == 'APPROVED':
        project_resources = db.query(PmoResourceAllocation).filter(
            PmoResourceAllocation.project_id == project_id,
            PmoResourceAllocation.status != 'CANCELLED'
        ).all()
        
        resource_ids = [alloc.resource_id for alloc in project_resources]
        
        if resource_ids:
            shared_projects = (
                db.query(PmoResourceAllocation.project_id)
                .filter(
                    PmoResourceAllocation.resource_id.in_(resource_ids),
                    PmoResourceAllocation.project_id != project_id,
                    PmoResourceAllocation.status != 'CANCELLED'
                )
                .distinct()
                .all()
            )
            
            for (related_project_id,) in shared_projects:
                related_project = db.query(Project).filter(Project.id == related_project_id).first()
                if related_project:
                    related_project_impacts.append({
                        'project_id': related_project_id,
                        'project_code': related_project.project_code,
                        'project_name': related_project.project_name,
                        'impact_reason': '共享资源可能受影响',
                    })
    
    return {
        'affected_projects': related_project_impacts,
        'count': len(related_project_impacts),
    }


def build_impact_analysis(
    db: Session,
    change: PmoChangeRequest,
    project: Project,
    project_id: int
) -> Dict[str, Any]:
    """
    构建变更影响分析
    
    Returns:
        Dict: 影响分析信息
    """
    impacts = {
        'change_id': change.id,
        'change_no': change.change_no,
        'change_type': change.change_type,
        'change_level': change.change_level,
        'title': change.title,
        'status': change.status,
        'impacts': {}
    }
    
    # 进度影响
    schedule_impact = analyze_schedule_impact(db, change, project_id)
    if schedule_impact:
        impacts['impacts']['schedule'] = schedule_impact
    
    # 成本影响
    cost_impact = analyze_cost_impact(change, project)
    if cost_impact:
        impacts['impacts']['cost'] = cost_impact
    
    # 资源影响
    resource_impact = analyze_resource_impact(db, change, project_id)
    if resource_impact:
        impacts['impacts']['resource'] = resource_impact
    
    # 关联项目影响
    impacts['impacts']['related_projects'] = analyze_related_project_impact(db, change, project_id)
    
    return impacts


def calculate_change_statistics(
    changes: List[PmoChangeRequest],
    impact_analysis: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    计算变更统计信息
    
    Returns:
        Dict: 统计信息
    """
    total_cost_impact = sum(
        abs(float(change.cost_impact or 0)) 
        for change in changes 
        if change.cost_impact
    )
    
    affected_projects_count = len(set(
        proj['project_id'] 
        for impact in impact_analysis 
        for proj in impact.get('impacts', {}).get('related_projects', {}).get('affected_projects', [])
    ))
    
    stats = {
        'total_changes': len(changes),
        'by_type': {},
        'by_level': {},
        'by_status': {},
        'total_cost_impact': total_cost_impact,
        'affected_projects_count': affected_projects_count,
    }
    
    for change in changes:
        change_type = change.change_type or 'OTHER'
        if change_type not in stats['by_type']:
            stats['by_type'][change_type] = 0
        stats['by_type'][change_type] += 1
        
        change_level = change.change_level or 'MINOR'
        if change_level not in stats['by_level']:
            stats['by_level'][change_level] = 0
        stats['by_level'][change_level] += 1
        
        change_status = change.status or 'DRAFT'
        if change_status not in stats['by_status']:
            stats['by_status'][change_status] = 0
        stats['by_status'][change_status] += 1
    
    return stats
