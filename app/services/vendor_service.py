# -*- coding: utf-8 -*-
"""
供应商业务逻辑服务
基于统一的 BaseService 实现
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from app.common.crud.base import BaseService
from app.models.vendor import Vendor
from app.schemas.material import SupplierCreate, SupplierUpdate, SupplierResponse


class VendorService(
    BaseService[Vendor, SupplierCreate, SupplierUpdate, SupplierResponse]
):
    """
    供应商服务类 (Vendor/Supplier)
    """

    def __init__(self, db: Session):
        super().__init__(
            model=Vendor,
            db=db,
            response_schema=SupplierResponse,
            resource_name="供应商",
        )

    def _to_response(self, obj: Vendor) -> SupplierResponse:
        """
        转换为响应对象，处理 Decimal 和默认值
        """
        return SupplierResponse(
            id=obj.id,
            supplier_code=obj.supplier_code,
            supplier_name=obj.supplier_name,
            supplier_short_name=obj.supplier_short_name,
            supplier_type=obj.supplier_type,
            contact_person=obj.contact_person,
            contact_phone=obj.contact_phone,
            contact_email=obj.contact_email,
            address=obj.address,
            quality_rating=obj.quality_rating or Decimal("0"),
            delivery_rating=obj.delivery_rating or Decimal("0"),
            service_rating=obj.service_rating or Decimal("0"),
            overall_rating=obj.overall_rating or Decimal("0"),
            supplier_level=obj.supplier_level or "B",
            status=obj.status or "ACTIVE",
            cooperation_start=obj.cooperation_start,
            last_order_date=obj.last_order_date,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    def list_suppliers(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        supplier_type: Optional[str] = None,
        status: Optional[str] = None,
        supplier_level: Optional[str] = None,
        vendor_type: str = "MATERIAL",
    ) -> Dict[str, Any]:
        """
        获取供应商列表
        """
        from app.common.crud.types import QueryParams

        filters = {"vendor_type": vendor_type}
        if supplier_type:
            filters["supplier_type"] = supplier_type
        if status:
            filters["status"] = status
        if supplier_level:
            filters["supplier_level"] = supplier_level

        params = QueryParams(
            page=page,
            page_size=page_size,
            search=keyword,
            search_fields=["supplier_name", "supplier_code", "supplier_short_name"],
            filters=filters,
            sort_by="created_at",
            sort_order="desc",
        )

        result = self.list(params)

        return {
            "items": result.items,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "pages": (result.total + result.page_size - 1) // result.page_size,
        }
