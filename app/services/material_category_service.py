# -*- coding: utf-8 -*-
"""
物料分类业务逻辑服务
基于统一的 BaseService 实现
"""

from typing import Any, List, Optional
from sqlalchemy.orm import Session

from app.common.crud.base import BaseService
from app.models.material import MaterialCategory
from app.schemas.material import MaterialCategoryCreate, MaterialCategoryResponse


class MaterialCategoryService(
    BaseService[MaterialCategory, MaterialCategoryCreate, Any, MaterialCategoryResponse]
):
    """
    物料分类服务类
    """

    def __init__(self, db: Session):
        super().__init__(
            model=MaterialCategory,
            db=db,
            response_schema=MaterialCategoryResponse,
            resource_name="物料分类",
        )

    def _to_response(self, obj: MaterialCategory) -> MaterialCategoryResponse:
        """
        转换为响应对象，处理层级和路径
        """
        return MaterialCategoryResponse.model_validate(obj)

    def get_tree(
        self, parent_id: Optional[int] = None
    ) -> List[MaterialCategoryResponse]:
        """
        获取分类树
        """
        query = self.db.query(self.model).filter(self.model.parent_id == parent_id)
        categories = query.order_by(self.model.sort_order).all()

        result = []
        for cat in categories:
            resp = self._to_response(cat)
            resp.children = self.get_tree(cat.id)
            result.append(resp)
        return result
