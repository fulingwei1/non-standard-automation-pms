# -*- coding: utf-8 -*-
"""
BOM 业务逻辑服务
基于统一的 BaseService 实现
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.common.crud.base import BaseService
from app.models.material import BomHeader
from app.schemas.material import BomCreate, BomUpdate, BomResponse


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
        return BomResponse.model_validate(obj)

    def list_boms(
        self,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[int] = None,
        machine_id: Optional[int] = None,
        is_latest: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        获取BOM列表
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
