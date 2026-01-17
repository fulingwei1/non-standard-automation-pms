# -*- coding: utf-8 -*-
"""
API服务基类
提供统一的响应格式、错误处理和常用方法
"""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.schemas.common import PaginatedResponse, ResponseModel


class BaseAPIService:
    """API服务基类"""

    @staticmethod
    def success_response(
        data: Any = None,
        message: str = "success",
        code: int = 200
    ) -> ResponseModel:
        """
        创建成功响应

        Args:
            data: 响应数据
            message: 响应消息
            code: 响应代码

        Returns:
            ResponseModel: 统一响应格式
        """
        return ResponseModel(code=code, message=message, data=data)

    @staticmethod
    def error_response(
        message: str,
        code: int = 400,
        data: Any = None
    ) -> ResponseModel:
        """
        创建错误响应

        Args:
            message: 错误消息
            code: 错误代码
            data: 可选的错误数据

        Returns:
            ResponseModel: 统一响应格式
        """
        return ResponseModel(code=code, message=message, data=data)

    @staticmethod
    def paginated_response(
        items: List[Any],
        total: int,
        page: int,
        page_size: int
    ) -> PaginatedResponse:
        """
        创建分页响应

        Args:
            items: 数据列表
            total: 总记录数
            page: 当前页码
            page_size: 每页条数

        Returns:
            PaginatedResponse: 分页响应格式
        """
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )

    @staticmethod
    def raise_not_found(resource: str = "资源", resource_id: Any = None):
        """
        抛出404错误

        Args:
            resource: 资源名称
            resource_id: 资源ID
        """
        detail = f"{resource}不存在"
        if resource_id is not None:
            detail = f"{resource}（ID: {resource_id}）不存在"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

    @staticmethod
    def raise_bad_request(message: str):
        """
        抛出400错误

        Args:
            message: 错误消息
        """
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    @staticmethod
    def raise_forbidden(message: str = "权限不足"):
        """
        抛出403错误

        Args:
            message: 错误消息
        """
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )

    @staticmethod
    def raise_unauthorized(message: str = "未授权"):
        """
        抛出401错误

        Args:
            message: 错误消息
        """
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )

    @staticmethod
    def validate_exists(
        db: Session,
        model_class: Any,
        id: int,
        resource_name: str = "资源"
    ) -> Any:
        """
        验证资源是否存在，不存在则抛出404

        Args:
            db: 数据库会话
            model_class: 模型类
            id: 资源ID
            resource_name: 资源名称

        Returns:
            模型实例
        """
        instance = db.query(model_class).filter(model_class.id == id).first()
        if not instance:
            BaseAPIService.raise_not_found(resource_name, id)
        return instance

    @staticmethod
    def get_or_404(
        db: Session,
        model_class: Any,
        id: int,
        resource_name: str = "资源"
    ) -> Any:
        """
        获取资源，不存在则抛出404（validate_exists的别名）

        Args:
            db: 数据库会话
            model_class: 模型类
            id: 资源ID
            resource_name: 资源名称

        Returns:
            模型实例
        """
        return BaseAPIService.validate_exists(db, model_class, id, resource_name)
