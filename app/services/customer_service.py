# -*- coding: utf-8 -*-
"""
客户业务逻辑服务
基于统一的 BaseService 实现
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.common.crud.base import BaseService
from app.models.project.customer import Customer
from app.schemas.project.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
)


class CustomerService(
    BaseService[Customer, CustomerCreate, CustomerUpdate, CustomerResponse]
):
    """
    客户服务类
    """

    def __init__(self, db: Session):
        super().__init__(
            model=Customer,
            db=db,
            response_schema=CustomerResponse,
            resource_name="客户",
        )

    def list_customers(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        customer_type: Optional[str] = None,
        industry: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取客户列表
        """
        from app.common.crud.types import QueryParams

        filters = {}
        if customer_type:
            filters["customer_type"] = customer_type
        if industry:
            filters["industry"] = industry
        if status:
            filters["status"] = status

        params = QueryParams(
            page=page,
            page_size=page_size,
            search=keyword,
            search_fields=["customer_name", "customer_code", "short_name"],
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

    def _before_delete(self, object_id: int) -> None:
        """删除前检查是否有关联项目"""
        from app.models.project.core import Project
        from fastapi import HTTPException

        project_count = (
            self.db.query(Project).filter(Project.customer_id == object_id).count()
        )
        if project_count > 0:
            raise HTTPException(
                status_code=400, detail=f"该客户下还有 {project_count} 个项目，无法删除"
            )

    def set_auto_sync(self, auto_sync: bool):
        self._auto_sync = auto_sync

    def _after_update(self, db_obj: Customer) -> Customer:
        """更新后尝试同步数据到项目和合同"""
        if getattr(self, "_auto_sync", True):
            try:
                from app.services.data_sync_service import DataSyncService
                import logging

                logger = logging.getLogger(__name__)

                sync_service = DataSyncService(self.db)
                # 同步到项目
                sync_service.sync_customer_to_projects(db_obj.id)
                # 同步到合同
                sync_service.sync_customer_to_contracts(db_obj.id)
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"客户信息自动同步失败: {str(e)}", exc_info=True)
        return db_obj

    def generate_code(self) -> str:
        """
        生成客户编码
        """
        from app.utils.number_generator import generate_customer_code

        return generate_customer_code(self.db)
