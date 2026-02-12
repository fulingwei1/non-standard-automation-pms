# -*- coding: utf-8 -*-
"""
项目关联关系服务

合并了原 project_relation_discovery_service.py 的发现功能。
旧模块（兼容层）已删除。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

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
        Project.is_active
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
        Project.is_active
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
        Project.is_active
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
        Project.is_active,
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


def calculate_discovery_relation_statistics(
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
