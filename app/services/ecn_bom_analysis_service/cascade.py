# -*- coding: utf-8 -*-
"""
ECN BOM影响分析服务 - 级联分析
"""
from typing import TYPE_CHECKING, Any, Dict, List, Set

from app.models.material import BomItem

if TYPE_CHECKING:
    from app.services.ecn_bom_analysis_service import EcnBomAnalysisService


def analyze_cascade_impact(
    service: "EcnBomAnalysisService",
    bom_items: List[BomItem],
    affected_item_ids: Set[int]
) -> List[Dict[str, Any]]:
    """分析级联影响（父子关系）"""
    cascade_impact = []

    # 构建父子关系映射
    parent_to_children = {}
    item_id_to_item = {}

    for item in bom_items:
        item_id_to_item[item.id] = item
        if item.parent_item_id:
            if item.parent_item_id not in parent_to_children:
                parent_to_children[item.parent_item_id] = []
            parent_to_children[item.parent_item_id].append(item)

    # 向上追溯：如果子物料受影响，父物料也可能受影响
    processed_ids = set(affected_item_ids)
    queue = list(affected_item_ids)

    while queue:
        item_id = queue.pop(0)
        item = item_id_to_item.get(item_id)
        if not item:
            continue

        # 找到父物料
        if item.parent_item_id and item.parent_item_id not in processed_ids:
            parent_item = item_id_to_item.get(item.parent_item_id)
            if parent_item:
                cascade_impact.append({
                    "bom_item_id": parent_item.id,
                    "material_code": parent_item.material_code,
                    "material_name": parent_item.material_name,
                    "impact": "因子物料变更可能受影响",
                    "cascade_type": "UPWARD"
                })
                processed_ids.add(item.parent_item_id)
                queue.append(item.parent_item_id)

        # 向下追溯：如果父物料受影响，子物料也可能受影响
        if item_id in parent_to_children:
            for child_item in parent_to_children[item_id]:
                if child_item.id not in processed_ids:
                    cascade_impact.append({
                        "bom_item_id": child_item.id,
                        "material_code": child_item.material_code,
                        "material_name": child_item.material_name,
                        "impact": "因父物料变更可能受影响",
                        "cascade_type": "DOWNWARD"
                    })
                    processed_ids.add(child_item.id)

    return cascade_impact
