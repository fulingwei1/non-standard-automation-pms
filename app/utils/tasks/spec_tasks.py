# -*- coding: utf-8 -*-
"""
规格匹配定时任务

包含每日规格匹配检查等任务
"""

import logging
from datetime import datetime

from app.models.base import get_db_session
from app.models.project import Project
from app.models.technical_spec import SpecMatchRecord
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.material import BomHeader, BomItem
from app.utils.spec_match_service import SpecMatchService

logger = logging.getLogger(__name__)


def daily_spec_match_check():
    """
    每日规格匹配检查
    每天上午9点执行，检查所有活跃项目的采购订单和BOM
    """
    service = SpecMatchService()

    with get_db_session() as db:
        # 查询所有活跃项目
        projects = db.query(Project).filter(
            Project.is_active == True,
            Project.is_archived == False
        ).all()

        total_checked = 0
        total_mismatched = 0

        for project in projects:
            # 检查项目的采购订单
            po_items = db.query(PurchaseOrderItem).join(
                PurchaseOrder
            ).filter(
                PurchaseOrder.project_id == project.id,
                PurchaseOrder.status.in_(['APPROVED', 'ORDERED', 'PARTIAL_RECEIVED'])
            ).all()

            for po_item in po_items:
                # 检查是否已有匹配记录（避免重复检查）
                existing_record = db.query(SpecMatchRecord).filter(
                    SpecMatchRecord.project_id == project.id,
                    SpecMatchRecord.match_type == 'PURCHASE_ORDER',
                    SpecMatchRecord.match_target_id == po_item.id
                ).first()

                if existing_record:
                    continue

                # 执行匹配检查
                match_record = service.check_po_item_spec_match(
                    db=db,
                    project_id=project.id,
                    po_item_id=po_item.id,
                    material_code=po_item.material_code,
                    specification=po_item.specification or '',
                    brand=None,
                    model=None
                )

                if match_record and match_record.match_status == 'MISMATCHED':
                    total_mismatched += 1
                total_checked += 1

            # 检查项目的BOM
            bom_items = db.query(BomItem).join(
                BomHeader
            ).filter(
                BomHeader.project_id == project.id,
                BomHeader.status.in_(['APPROVED', 'RELEASED'])
            ).all()

            for bom_item in bom_items:
                # 检查是否已有匹配记录
                existing_record = db.query(SpecMatchRecord).filter(
                    SpecMatchRecord.project_id == project.id,
                    SpecMatchRecord.match_type == 'BOM',
                    SpecMatchRecord.match_target_id == bom_item.id
                ).first()

                if existing_record:
                    continue

                # 执行匹配检查
                material_code = bom_item.material.material_code if bom_item.material else None
                if not material_code:
                    continue

                match_record = service.check_bom_item_spec_match(
                    db=db,
                    project_id=project.id,
                    bom_item_id=bom_item.id,
                    material_code=material_code,
                    specification=bom_item.specification or '',
                    brand=bom_item.material.brand if bom_item.material else None,
                    model=None
                )

                if match_record and match_record.match_status == 'MISMATCHED':
                    total_mismatched += 1
                total_checked += 1

        db.commit()

        logger.info(f"[{datetime.now()}] 规格匹配检查完成: 检查 {total_checked} 项, 发现 {total_mismatched} 项不匹配")

        return {
            'checked': total_checked,
            'mismatched': total_mismatched,
            'timestamp': datetime.now().isoformat()
        }
