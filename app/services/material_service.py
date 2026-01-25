# -*- coding: utf-8 -*-
"""
物料管理业务逻辑服务
基于统一的 BaseService 实现
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.common.crud.base import BaseService
from app.models.material import Material, MaterialCategory
from app.schemas.material import MaterialCreate, MaterialUpdate, MaterialResponse


class MaterialService(
    BaseService[Material, MaterialCreate, MaterialUpdate, MaterialResponse]
):
    """
    物料服务类
    """

    def __init__(self, db: Session):
        super().__init__(
            model=Material,
            db=db,
            response_schema=MaterialResponse,
            resource_name="物料",
        )

    def _to_response(self, obj: Material) -> MaterialResponse:
        """
        重写自定义转换逻辑，处理 category_name 等关联字段
        """
        response = MaterialResponse.model_validate(obj)
        if obj.category:
            response.category_name = obj.category.category_name

        # 处理可能的 None 值
        response.standard_price = obj.standard_price or 0
        response.last_price = obj.last_price or 0
        response.safety_stock = obj.safety_stock or 0
        response.current_stock = obj.current_stock or 0
        response.lead_time_days = obj.lead_time_days or 0

        return response

    def list_materials(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        category_id: Optional[int] = None,
        material_type: Optional[str] = None,
        is_key_material: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        获取物料列表（支持分页、搜索、筛选）
        """
        from app.common.crud.types import QueryParams

        filters = {}
        if category_id:
            filters["category_id"] = category_id
        if material_type:
            filters["material_type"] = material_type
        if is_key_material is not None:
            filters["is_key_material"] = is_key_material
        if is_active is not None:
            filters["is_active"] = is_active

        params = QueryParams(
            page=page,
            page_size=page_size,
            search=keyword,
            search_fields=["material_code", "material_name"],
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

    def generate_code(self, category_id: Optional[int] = None) -> str:
        """
        生成物料编码
        """
        from app.utils.number_generator import generate_material_code

        category_code = None
        if category_id:
            category = (
                self.db.query(MaterialCategory)
                .filter(MaterialCategory.id == category_id)
                .first()
            )
            if category:
                category_code = category.category_code

        return generate_material_code(self.db, category_code)
