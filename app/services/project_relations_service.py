# -*- coding: utf-8 -*-
"""
项目关联关系服务
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.project import Project
from app.models.shortage import MaterialTransfer


def get_material_transfer_relations(
    db: Session,
    project_id: int,
    relation_type: Optional[str]
) -> List[Dict[str, Any]]:
    """
    获取物料转移关联关系
    
    Returns:
        List[Dict]: 关联关系列表
    """
    relations = []
    
    if relation_type and relation_type != 'MATERIAL_TRANSFER':
        return relations
    
    # 出库转移
    outbound_transfers = db.query(MaterialTransfer).filter(
        MaterialTransfer.from_project_id == project_id,
        MaterialTransfer.status.in_(['APPROVED', 'EXECUTED'])
    ).all()
    
    for transfer in outbound_transfers:
        if transfer.to_project_id:
            to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
            if to_project:
                relations.append({
                    'type': 'MATERIAL_TRANSFER_OUT',
                    'related_project_id': transfer.to_project_id,
                    'related_project_code': to_project.project_code,
                    'related_project_name': to_project.project_name,
                    'relation_detail': {
                        'transfer_no': transfer.transfer_no,
                        'material_code': transfer.material_code,
                        'material_name': transfer.material_name,
                        'transfer_qty': float(transfer.transfer_qty),
                    },
                    'strength': 'MEDIUM',
                })
    
    # 入库转移
    inbound_transfers = db.query(MaterialTransfer).filter(
        MaterialTransfer.to_project_id == project_id,
        MaterialTransfer.status.in_(['APPROVED', 'EXECUTED'])
    ).all()
    
    for transfer in inbound_transfers:
        if transfer.from_project_id:
            from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first()
            if from_project:
                relations.append({
                    'type': 'MATERIAL_TRANSFER_IN',
                    'related_project_id': transfer.from_project_id,
                    'related_project_code': from_project.project_code,
                    'related_project_name': from_project.project_name,
                    'relation_detail': {
                        'transfer_no': transfer.transfer_no,
                        'material_code': transfer.material_code,
                        'material_name': transfer.material_name,
                        'transfer_qty': float(transfer.transfer_qty),
                    },
                    'strength': 'MEDIUM',
                })
    
    return relations


def get_shared_resource_relations(
    db: Session,
    project_id: int,
    relation_type: Optional[str]
) -> List[Dict[str, Any]]:
    """
    获取共享资源关联关系
    
    Returns:
        List[Dict]: 关联关系列表
    """
    relations = []
    
    if relation_type and relation_type != 'SHARED_RESOURCE':
        return relations
    
    try:
        from app.models.pmo import PmoResourceAllocation
        
        project_resources = db.query(PmoResourceAllocation).filter(
            PmoResourceAllocation.project_id == project_id,
            PmoResourceAllocation.status != 'CANCELLED'
        ).all()
        
        resource_ids = [alloc.resource_id for alloc in project_resources]
        if not resource_ids:
            return relations
        
        shared_resource_projects = (
            db.query(PmoResourceAllocation.project_id, func.count(PmoResourceAllocation.id).label('shared_count'))
            .filter(
                PmoResourceAllocation.resource_id.in_(resource_ids),
                PmoResourceAllocation.project_id != project_id,
                PmoResourceAllocation.status != 'CANCELLED'
            )
            .group_by(PmoResourceAllocation.project_id)
            .all()
        )
        
        for shared_project_id, shared_count in shared_resource_projects:
            shared_project = db.query(Project).filter(Project.id == shared_project_id).first()
            if shared_project:
                shared_resources = (
                    db.query(PmoResourceAllocation)
                    .filter(
                        PmoResourceAllocation.project_id == shared_project_id,
                        PmoResourceAllocation.resource_id.in_(resource_ids),
                        PmoResourceAllocation.status != 'CANCELLED'
                    )
                    .all()
                )
                
                relations.append({
                    'type': 'SHARED_RESOURCE',
                    'related_project_id': shared_project_id,
                    'related_project_code': shared_project.project_code,
                    'related_project_name': shared_project.project_name,
                    'relation_detail': {
                        'shared_resource_count': shared_count,
                        'shared_resources': [
                            {
                                'resource_id': r.resource_id,
                                'resource_name': r.resource_name,
                                'allocation_percent': r.allocation_percent,
                            }
                            for r in shared_resources
                        ],
                    },
                    'strength': 'HIGH' if shared_count >= 3 else 'MEDIUM',
                })
    except ImportError:
        # 如果模型不存在，跳过
        pass
    
    return relations


def get_shared_customer_relations(
    db: Session,
    project: Project,
    project_id: int,
    relation_type: Optional[str]
) -> List[Dict[str, Any]]:
    """
    获取共享客户关联关系
    
    Returns:
        List[Dict]: 关联关系列表
    """
    relations = []
    
    if relation_type and relation_type != 'SHARED_CUSTOMER':
        return relations
    
    if not project.customer_id:
        return relations
    
    customer_projects = db.query(Project).filter(
        Project.customer_id == project.customer_id,
        Project.id != project_id,
        Project.is_active == True
    ).all()
    
    for customer_project in customer_projects:
        relations.append({
            'type': 'SHARED_CUSTOMER',
            'related_project_id': customer_project.id,
            'related_project_code': customer_project.project_code,
            'related_project_name': customer_project.project_name,
            'relation_detail': {
                'customer_id': project.customer_id,
                'customer_name': project.customer_name,
            },
            'strength': 'LOW',
        })
    
    return relations


def calculate_relation_statistics(
    relations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    计算关联关系统计信息
    
    Returns:
        Dict[str, Any]: 统计信息
    """
    relation_stats = {
        'total_relations': len(relations),
        'by_type': {},
        'by_strength': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    }
    
    for relation in relations:
        rel_type = relation['type']
        strength = relation['strength']
        
        if rel_type not in relation_stats['by_type']:
            relation_stats['by_type'][rel_type] = 0
        relation_stats['by_type'][rel_type] += 1
        
        relation_stats['by_strength'][strength] += 1
    
    return relation_stats
