# -*- coding: utf-8 -*-
"""
BOM版本管理 - 从 bom.py 拆分
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import BomHeader
from app.models.user import User
from app.schemas.material import BomResponse
from app.utils.db_helpers import get_or_404
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/{bom_id}/versions", response_model=List[BomResponse])
def get_bom_versions(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    current_user: User = Depends(security.get_current_active_user),
):
    """获取BOM的所有版本列表
    基于BOM编号查找所有版本
    """
    bom = get_or_404(db, BomHeader, bom_id, "BOM不存在")

    # 查找相同BOM编号的所有版本
    versions = (
        db.query(BomHeader)
        .filter(BomHeader.bom_no == bom.bom_no)
        .order_by(BomHeader.created_at.desc())
        .all()
    )

    result = []
    for version in versions:
        # 获取BOM明细数量（简化版，不加载完整明细）
        version.items.count()

        result.append(
            BomResponse(
                id=version.id,
                bom_no=version.bom_no,
                bom_name=version.bom_name,
                project_id=version.project_id,
                project_name=version.project.project_name if version.project else None,
                machine_id=version.machine_id,
                machine_name=version.machine.machine_name if version.machine else None,
                version=version.version,
                is_latest=version.is_latest,
                status=version.status,
                total_items=version.total_items,
                total_amount=version.total_amount or 0,
                items=[],
            )
        )

    return result


@router.get("/{bom_id}/versions/compare", response_model=dict)
def compare_bom_versions(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    version1_id: Optional[int] = Query(None, description="版本1的BOM ID"),
    version2_id: Optional[int] = Query(None, description="版本2的BOM ID"),
    current_user: User = Depends(security.get_current_active_user),
):
    """对比BOM的两个版本
    如果不提供version1_id和version2_id，则对比当前版本和最新发布版本
    """
    bom = get_or_404(db, BomHeader, bom_id, "BOM不存在")

    # 确定要对比的两个版本
    if version1_id and version2_id:
        v1 = db.query(BomHeader).filter(BomHeader.id == version1_id).first()
        v2 = db.query(BomHeader).filter(BomHeader.id == version2_id).first()
    else:
        # 默认对比当前版本和最新发布版本
        v1 = bom
        v2 = (
            db.query(BomHeader)
            .filter(
                BomHeader.bom_no == bom.bom_no,
                BomHeader.status == "RELEASED",
                BomHeader.is_latest,
            )
            .first()
        )
        if not v2:
            v2 = bom

    if not v1 or not v2:
        raise HTTPException(status_code=404, detail="要对比的版本不存在")

    # 获取两个版本的明细
    items1 = {item.material_code: item for item in v1.items.all()}
    items2 = {item.material_code: item for item in v2.items.all()}

    # 找出新增、删除、修改的物料
    added = []
    deleted = []
    modified = []
    unchanged = []

    all_materials = set(items1.keys()) | set(items2.keys())

    for material_code in all_materials:
        if material_code in items1 and material_code not in items2:
            deleted.append(
                {
                    "material_code": material_code,
                    "material_name": items1[material_code].material_name,
                    "quantity": float(items1[material_code].quantity),
                    "unit_price": float(items1[material_code].unit_price)
                    if items1[material_code].unit_price
                    else 0,
                }
            )
        elif material_code not in items1 and material_code in items2:
            added.append(
                {
                    "material_code": material_code,
                    "material_name": items2[material_code].material_name,
                    "quantity": float(items2[material_code].quantity),
                    "unit_price": float(items2[material_code].unit_price)
                    if items2[material_code].unit_price
                    else 0,
                }
            )
        else:
            item1 = items1[material_code]
            item2 = items2[material_code]
            if (
                item1.quantity != item2.quantity
                or item1.unit_price != item2.unit_price
                or item1.specification != item2.specification
            ):
                modified.append(
                    {
                        "material_code": material_code,
                        "material_name": item1.material_name,
                        "v1": {
                            "quantity": float(item1.quantity),
                            "unit_price": float(item1.unit_price)
                            if item1.unit_price
                            else 0,
                            "specification": item1.specification,
                        },
                        "v2": {
                            "quantity": float(item2.quantity),
                            "unit_price": float(item2.unit_price)
                            if item2.unit_price
                            else 0,
                            "specification": item2.specification,
                        },
                    }
                )
            else:
                unchanged.append(
                    {
                        "material_code": material_code,
                        "material_name": item1.material_name,
                        "quantity": float(item1.quantity),
                        "unit_price": float(item1.unit_price)
                        if item1.unit_price
                        else 0,
                    }
                )

    return {
        "version1": {
            "id": v1.id,
            "version": v1.version,
            "status": v1.status,
            "total_items": v1.total_items,
            "total_amount": float(v1.total_amount) if v1.total_amount else 0,
        },
        "version2": {
            "id": v2.id,
            "version": v2.version,
            "status": v2.status,
            "total_items": v2.total_items,
            "total_amount": float(v2.total_amount) if v2.total_amount else 0,
        },
        "comparison": {
            "added": added,
            "deleted": deleted,
            "modified": modified,
            "unchanged": unchanged,
            "summary": {
                "added_count": len(added),
                "deleted_count": len(deleted),
                "modified_count": len(modified),
                "unchanged_count": len(unchanged),
            },
        },
    }
