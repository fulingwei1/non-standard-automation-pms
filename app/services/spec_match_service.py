# -*- coding: utf-8 -*-
"""
规格匹配检查服务
"""

from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.material import BomItem
from app.models.purchase import PurchaseOrderItem
from app.models.technical_spec import SpecMatchRecord, TechnicalSpecRequirement
from app.schemas.technical_spec import SpecMatchResult
from app.utils.spec_matcher import SpecMatcher


def get_project_requirements(
    db: Session,
    project_id: int
) -> List[TechnicalSpecRequirement]:
    """
    获取项目的所有规格要求

    Returns:
        List[TechnicalSpecRequirement]: 规格要求列表
    """
    return db.query(TechnicalSpecRequirement).filter(
        TechnicalSpecRequirement.project_id == project_id
    ).all()


def check_po_item_match(
    db: Session,
    po_item: PurchaseOrderItem,
    requirements: List[TechnicalSpecRequirement],
    project_id: int,
    matcher: SpecMatcher
) -> List[SpecMatchResult]:
    """
    检查单个采购订单项的匹配

    Returns:
        List[SpecMatchResult]: 匹配结果列表
    """
    results = []

    for req in requirements:
        # 如果规格要求有物料编码，需要匹配
        if req.material_code and req.material_code != po_item.material_code:
            continue

        match_result = matcher.match_specification(
            requirement=req,
            actual_spec=po_item.specification or '',
            actual_brand=None,  # 采购订单可能没有品牌字段
            actual_model=None
        )

        # 保存匹配记录
        match_record = SpecMatchRecord(
            project_id=project_id,
            spec_requirement_id=req.id,
            match_type='PURCHASE_ORDER',
            match_target_id=po_item.id,
            match_status=match_result.match_status,
            match_score=match_result.match_score,
            differences=match_result.differences
        )
        db.add(match_record)

        results.append(SpecMatchResult(
            spec_requirement_id=req.id,
            material_name=req.material_name,
            match_status=match_result.match_status,
            match_score=match_result.match_score,
            differences=match_result.differences
        ))

    return results


def check_bom_item_match(
    db: Session,
    bom_item: BomItem,
    requirements: List[TechnicalSpecRequirement],
    project_id: int,
    matcher: SpecMatcher
) -> List[SpecMatchResult]:
    """
    检查单个BOM项的匹配

    Returns:
        List[SpecMatchResult]: 匹配结果列表
    """
    results = []

    for req in requirements:
        # 如果规格要求有物料编码，需要匹配
        if req.material_code and req.material_code != bom_item.material.material_code:
            continue

        match_result = matcher.match_specification(
            requirement=req,
            actual_spec=bom_item.specification or '',
            actual_brand=bom_item.material.brand if bom_item.material else None,
            actual_model=None
        )

        match_record = SpecMatchRecord(
            project_id=project_id,
            spec_requirement_id=req.id,
            match_type='BOM',
            match_target_id=bom_item.id,
            match_status=match_result.match_status,
            match_score=match_result.match_score,
            differences=match_result.differences
        )
        db.add(match_record)

        results.append(SpecMatchResult(
            spec_requirement_id=req.id,
            material_name=req.material_name,
            match_status=match_result.match_status,
            match_score=match_result.match_score,
            differences=match_result.differences
        ))

    return results


def check_all_po_items(
    db: Session,
    project_id: int,
    requirements: List[TechnicalSpecRequirement],
    matcher: SpecMatcher
) -> List[SpecMatchResult]:
    """
    检查所有采购订单项

    Returns:
        List[SpecMatchResult]: 匹配结果列表
    """
    po_items = db.query(PurchaseOrderItem).join(
        PurchaseOrderItem.order
    ).filter(
        PurchaseOrderItem.order.has(project_id=project_id)
    ).all()

    all_results = []
    for po_item in po_items:
        results = check_po_item_match(db, po_item, requirements, project_id, matcher)
        all_results.extend(results)

    return all_results


def check_all_bom_items(
    db: Session,
    project_id: int,
    requirements: List[TechnicalSpecRequirement],
    matcher: SpecMatcher
) -> List[SpecMatchResult]:
    """
    检查所有BOM项

    Returns:
        List[SpecMatchResult]: 匹配结果列表
    """
    bom_items = db.query(BomItem).join(
        BomItem.header
    ).filter(
        BomItem.header.has(project_id=project_id)
    ).all()

    all_results = []
    for bom_item in bom_items:
        results = check_bom_item_match(db, bom_item, requirements, project_id, matcher)
        all_results.extend(results)

    return all_results


def calculate_match_statistics(results: List[SpecMatchResult]) -> Dict[str, int]:
    """
    计算匹配统计

    Returns:
        dict: 包含总数、匹配数、不匹配数、未知数的字典
    """
    matched_count = sum(1 for r in results if r.match_status == 'MATCHED')
    mismatched_count = sum(1 for r in results if r.match_status == 'MISMATCHED')
    unknown_count = sum(1 for r in results if r.match_status == 'UNKNOWN')

    return {
        'total': len(results),
        'matched': matched_count,
        'mismatched': mismatched_count,
        'unknown': unknown_count
    }
