# -*- coding: utf-8 -*-
"""
项目关联发现服务
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.project import Project
from app.models.shortage import MaterialTransfer


def discover_same_customer_relations(
    db: Session,
    project: Project,
    project_id: int
) -> List[Dict[str, Any]]:
    """
    发现相同客户的项目关联
    
    Returns:
        List[Dict]: 关联关系列表
    """
    relations = []
    
    if not project.customer_id:
        return relations
    
    customer_projects = db.query(Project).filter(
        Project.customer_id == project.customer_id,
        Project.id != project_id,
        Project.is_active == True
    ).all()
    
    for related_project in customer_projects:
        relations.append({
            'related_project_id': related_project.id,
            'related_project_code': related_project.project_code,
            'related_project_name': related_project.project_name,
            'relation_type': 'SAME_CUSTOMER',
            'confidence': 0.8,
            'reason': f'相同客户：{project.customer_name}',
        })
    
    return relations


def discover_same_pm_relations(
    db: Session,
    project: Project,
    project_id: int
) -> List[Dict[str, Any]]:
    """
    发现相同项目经理的项目关联
    
    Returns:
        List[Dict]: 关联关系列表
    """
    relations = []
    
    if not project.pm_id:
        return relations
    
    pm_projects = db.query(Project).filter(
        Project.pm_id == project.pm_id,
        Project.id != project_id,
        Project.is_active == True
    ).all()
    
    for related_project in pm_projects:
        relations.append({
            'related_project_id': related_project.id,
            'related_project_code': related_project.project_code,
            'related_project_name': related_project.project_name,
            'relation_type': 'SAME_PM',
            'confidence': 0.7,
            'reason': f'相同项目经理：{project.pm_name}',
        })
    
    return relations


def discover_time_overlap_relations(
    db: Session,
    project: Project,
    project_id: int
) -> List[Dict[str, Any]]:
    """
    发现时间重叠的项目关联
    
    Returns:
        List[Dict]: 关联关系列表
    """
    relations = []
    
    if not (project.planned_start_date and project.planned_end_date):
        return relations
    
    overlapping_projects = db.query(Project).filter(
        Project.id != project_id,
        Project.is_active == True,
        Project.planned_start_date <= project.planned_end_date,
        Project.planned_end_date >= project.planned_start_date
    ).all()
    
    for related_project in overlapping_projects:
        relations.append({
            'related_project_id': related_project.id,
            'related_project_code': related_project.project_code,
            'related_project_name': related_project.project_name,
            'relation_type': 'TIME_OVERLAP',
            'confidence': 0.6,
            'reason': '项目时间重叠',
        })
    
    return relations


def discover_material_transfer_relations(
    db: Session,
    project_id: int
) -> List[Dict[str, Any]]:
    """
    发现物料转移的项目关联
    
    Returns:
        List[Dict]: 关联关系列表
    """
    relations = []
    
    material_transfers = db.query(MaterialTransfer).filter(
        or_(
            MaterialTransfer.from_project_id == project_id,
            MaterialTransfer.to_project_id == project_id
        ),
        MaterialTransfer.status.in_(['APPROVED', 'EXECUTED'])
    ).all()
    
    for transfer in material_transfers:
        related_project_id = (
            transfer.to_project_id if transfer.from_project_id == project_id
            else transfer.from_project_id
        )
        
        if related_project_id:
            related_project = db.query(Project).filter(Project.id == related_project_id).first()
            if related_project:
                relations.append({
                    'related_project_id': related_project.id,
                    'related_project_code': related_project.project_code,
                    'related_project_name': related_project.project_name,
                    'relation_type': 'MATERIAL_TRANSFER',
                    'confidence': 0.9,
                    'reason': f'物料转移：{transfer.material_name}',
                })
    
    return relations


def discover_shared_resource_relations(
    db: Session,
    project_id: int
) -> List[Dict[str, Any]]:
    """
    发现共享资源的项目关联
    
    Returns:
        List[Dict]: 关联关系列表
    """
    relations = []
    
    try:
        from app.models.pmo import PmoResourceAllocation
        
        project_resources = db.query(PmoResourceAllocation).filter(
            PmoResourceAllocation.project_id == project_id,
            PmoResourceAllocation.status != 'CANCELLED'
        ).all()
        
        resource_ids = [alloc.resource_id for alloc in project_resources]
        if not resource_ids:
            return relations
        
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
                relations.append({
                    'related_project_id': related_project.id,
                    'related_project_code': related_project.project_code,
                    'related_project_name': related_project.project_name,
                    'relation_type': 'SHARED_RESOURCE',
                    'confidence': 0.75,
                    'reason': '共享资源',
                })
    except ImportError:
        # 如果模型不存在，跳过
        pass
    
    return relations


def discover_shared_rd_project_relations(
    db: Session,
    project_id: int
) -> List[Dict[str, Any]]:
    """
    发现关联相同研发项目的项目关联
    
    Returns:
        List[Dict]: 关联关系列表
    """
    relations = []
    
    try:
        from app.models.rd_project import RdProject
        
        linked_rd_projects = db.query(RdProject).filter(
            RdProject.linked_project_id == project_id
        ).all()
        
        for rd_project in linked_rd_projects:
            # 查找其他关联到相同研发项目的非标项目
            other_linked_projects = db.query(RdProject).filter(
                RdProject.id == rd_project.id,
                RdProject.linked_project_id != project_id,
                RdProject.linked_project_id.isnot(None)
            ).all()
            
            for other_rd in other_linked_projects:
                if other_rd.linked_project_id:
                    related_project = db.query(Project).filter(
                        Project.id == other_rd.linked_project_id
                    ).first()
                    if related_project:
                        relations.append({
                            'related_project_id': related_project.id,
                            'related_project_code': related_project.project_code,
                            'related_project_name': related_project.project_name,
                            'relation_type': 'SHARED_RD_PROJECT',
                            'confidence': 0.85,
                            'reason': f'关联相同研发项目：{rd_project.project_name}',
                        })
    except ImportError:
        # 如果模型不存在，跳过
        pass
    
    return relations


def deduplicate_and_filter_relations(
    relations: List[Dict[str, Any]],
    min_confidence: float
) -> List[Dict[str, Any]]:
    """
    去重并过滤置信度
    
    Returns:
        List[Dict]: 去重后的关联关系列表（按置信度排序）
    """
    unique_relations = {}
    
    for relation in relations:
        if relation['confidence'] >= min_confidence:
            key = relation['related_project_id']
            if key not in unique_relations or relation['confidence'] > unique_relations[key]['confidence']:
                unique_relations[key] = relation
    
    # 按置信度排序
    return sorted(unique_relations.values(), key=lambda x: x['confidence'], reverse=True)


def calculate_relation_statistics(
    relations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    计算关联关系统计信息
    
    Returns:
        Dict[str, Any]: 统计信息
    """
    by_type = {}
    for relation in relations:
        rel_type = relation['relation_type']
        by_type[rel_type] = by_type.get(rel_type, 0) + 1
    
    return {
        'by_type': by_type,
        'by_confidence_range': {
            'high': len([r for r in relations if r['confidence'] >= 0.8]),
            'medium': len([r for r in relations if 0.5 <= r['confidence'] < 0.8]),
            'low': len([r for r in relations if r['confidence'] < 0.5]),
        }
    }
