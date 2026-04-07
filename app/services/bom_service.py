# -*- coding: utf-8 -*-
"""
BOM 业务逻辑服务
基于统一的 BaseService 实现
"""

from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.common.crud.base import BaseService
from app.models.material import BomHeader
from app.schemas.material import BomCreate, BomItemResponse, BomResponse, BomUpdate


class BomService(BaseService[BomHeader, BomCreate, BomUpdate, BomResponse]):
    """
    BOM 服务类
    """

    def __init__(self, db: Session):
        super().__init__(
            model=BomHeader,
            db=db,
            response_schema=BomResponse,
            resource_name="BOM",
        )

    def _to_response(self, obj: BomHeader) -> BomResponse:
        """
        转换为响应对象
        """
        # Populate project_name and machine_name from relationships
        project_name = obj.project.project_name if obj.project else None
        machine_name = obj.machine.machine_name if obj.machine else None
        
        # Populate items from relationship
        items = []
        if hasattr(obj, 'items') and obj.items is not None:
            # Handle both lazy dynamic relationship and loaded list
            bom_items = obj.items.all() if hasattr(obj.items, 'all') else obj.items
            for item in bom_items:
                items.append(BomItemResponse(
                    id=item.id,
                    bom_id=item.bom_id,
                    item_no=item.item_no,
                    parent_item_id=item.parent_item_id,
                    material_id=item.material_id,
                    material_code=item.material_code,
                    material_name=item.material_name,
                    specification=item.specification,
                    drawing_no=item.drawing_no,
                    unit=item.unit,
                    quantity=Decimal(str(item.quantity)) if item.quantity else Decimal("0"),
                    unit_price=Decimal(str(item.unit_price)) if item.unit_price else Decimal("0"),
                    amount=Decimal(str(item.amount)) if item.amount else Decimal("0"),
                    source_type=item.source_type,
                    supplier_id=item.supplier_id,
                    required_date=item.required_date,
                    purchased_qty=Decimal(str(item.purchased_qty)) if item.purchased_qty else Decimal("0"),
                    received_qty=Decimal(str(item.received_qty)) if item.received_qty else Decimal("0"),
                    level=item.level or 1,
                    sort_order=item.sort_order or 0,
                    is_key_item=item.is_key_item or False,
                    remark=item.remark,
                ))
        
        return BomResponse(
            id=obj.id,
            bom_no=obj.bom_no,
            bom_name=obj.bom_name,
            project_id=obj.project_id,
            project_name=project_name,
            machine_id=obj.machine_id,
            machine_name=machine_name,
            version=obj.version or "1.0",
            is_latest=obj.is_latest if obj.is_latest is not None else True,
            status=obj.status or "DRAFT",
            total_items=obj.total_items or 0,
            total_amount=Decimal(str(obj.total_amount)) if obj.total_amount else Decimal("0"),
            approved_by=obj.approved_by,
            approved_at=obj.approved_at.isoformat() if obj.approved_at else None,
            created_by=obj.created_by,
            remark=obj.remark,
            items=items,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    def list_boms(
        self,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[int] = None,
        machine_id: Optional[int] = None,
        is_latest: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        获取 BOM 列表
        """
        from app.common.crud.types import QueryParams

        filters = {}
        if project_id:
            filters["project_id"] = project_id
        if machine_id:
            filters["machine_id"] = machine_id
        if is_latest is not None:
            filters["is_latest"] = is_latest

        params = QueryParams(
            page=page,
            page_size=page_size,
            filters=filters,
            sort_by="created_at",
            sort_order="desc",
            load_relationships=["project", "machine"],
        )

        result = self.list(params)

        return {
            "items": result.items,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "pages": (result.total + result.page_size - 1) // result.page_size,
        }
