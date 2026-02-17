# -*- coding: utf-8 -*-
"""
BOM发布 - 从 bom.py 拆分
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import BomHeader
from app.models.vendor import Vendor
from app.models.project import Project
from app.models.user import User
from app.schemas.material import BomResponse
from app.utils.db_helpers import get_or_404

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{bom_id}/release", response_model=BomResponse)
def release_bom(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    change_note: Optional[str] = Query(None, description="变更说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> BomResponse:
    """发布BOM版本
    将BOM状态从DRAFT改为RELEASED，并标记为最新版本
    """
    bom = get_or_404(db, BomHeader, bom_id, "BOM不存在")

    # 只有草稿状态才能发布
    if bom.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的BOM才能发布")

    # 检查是否有明细
    item_count = bom.items.count()
    if item_count == 0:
        raise HTTPException(status_code=400, detail="BOM没有明细，无法发布")

    # 将同一BOM编号的其他版本标记为非最新版本
    db.query(BomHeader).filter(
        BomHeader.bom_no == bom.bom_no, BomHeader.id != bom_id
    ).update({"is_latest": False})

    # 更新BOM状态和版本信息
    bom.status = "RELEASED"
    bom.is_latest = True
    bom.approved_by = current_user.id
    bom.approved_at = datetime.now()
    if change_note:
        bom.remark = change_note

    db.add(bom)

    # BOM发布时自动归集材料成本
    try:
        from app.services.cost_collection_service import CostCollectionService

        CostCollectionService.collect_from_bom(db, bom_id, created_by=current_user.id)
    except Exception as e:
        # 成本归集失败不影响BOM发布，只记录错误
        import logging

        logging.warning(f"BOM发布后成本归集失败：{str(e)}")

    # BOM审核通过后自动生成采购需求
    try:
        from app.api.v1.endpoints.purchase import generate_request_no
        from app.services.purchase_request_from_bom_service import (
            build_request_items,
            create_purchase_request,
            get_purchase_items_from_bom,
            group_items_by_supplier,
        )

        # 获取需要采购的物料
        purchase_items = get_purchase_items_from_bom(bom)

        if purchase_items:
            # 按供应商分组
            supplier_items = group_items_by_supplier(db, purchase_items, None)

            created_requests = []
            for supplier_id, items in supplier_items.items():
                # 构建申请明细
                request_items, total_amount = build_request_items(items)

                if not request_items:
                    continue

                # 获取供应商名称
                supplier_name = "未指定供应商"
                if supplier_id and supplier_id != 0:
                    supplier = (
                        db.query(Vendor).filter(Vendor.id == supplier_id, Vendor.vendor_type == 'MATERIAL').first()
                    )
                    if supplier:
                        supplier_name = supplier.supplier_name

                # 创建采购申请
                pr = create_purchase_request(
                    db=db,
                    bom=bom,
                    supplier_id=supplier_id,
                    supplier_name=supplier_name,
                    request_items=request_items,
                    total_amount=total_amount,
                    current_user_id=current_user.id,
                    generate_request_no=generate_request_no,
                )
                created_requests.append(pr)

            if created_requests:
                import logging

                logger.info(
                    f"BOM审核通过，已自动创建 {len(created_requests)} 个采购需求。"
                    f"BOM ID: {bom_id}"
                )
    except Exception as e:
        # 自动生成采购需求失败不影响BOM发布，记录日志
        import logging

        logging.warning(f"BOM审核通过后自动生成采购需求失败：{str(e)}")

    # BOM发布后自动触发阶段流转检查（S4→S5）
    if bom.project_id:
        try:
            from app.services.status_transition_service import StatusTransitionService

            transition_service = StatusTransitionService(db)

            # 调用BOM发布完成处理
            transition_service.handle_bom_published(bom.project_id, bom.machine_id)

            # 检查是否可以自动推进阶段
            project = db.query(Project).filter(Project.id == bom.project_id).first()
            if project and project.stage == "S4":
                auto_transition_result = transition_service.check_auto_stage_transition(
                    bom.project_id, auto_advance=True
                )

                if auto_transition_result.get("auto_advanced"):
                    import logging

                    transition_logger = logging.getLogger(__name__)
                    transition_logger.info(
                        f"BOM发布后自动推进项目 {bom.project_id} 至 {auto_transition_result.get('target_stage')} 阶段"
                    )
        except Exception as e:
            # 自动流转失败不影响BOM发布，记录日志
            import logging

            logging.warning(f"BOM发布后自动阶段流转失败：{str(e)}")

    db.commit()
    db.refresh(bom)

    return BomResponse(
        id=bom.id,
        bom_no=bom.bom_no,
        bom_name=bom.bom_name,
        project_id=bom.project_id,
        project_name=bom.project_name if bom.project else None,
        machine_id=bom.machine_id,
        machine_name=bom.machine_name if bom.machine else None,
        version=bom.version,
        is_latest=bom.is_latest,
        status=bom.status,
        total_items=bom.total_items,
        total_amount=bom.total_amount or 0,
        items=bom.items or [],
        created_at=bom.created_at,
        updated_at=bom.updated_at,
    )
