# -*- coding: utf-8 -*-
"""
统一响应格式定义

所有API响应都应该使用这些格式，确保前后端交互的一致性。
"""

from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """
    统一响应格式基类
    
    所有API响应都应该遵循这个格式：
    {
        "success": true/false,
        "code": 200,
        "message": "操作成功",
        "data": {...}
    }
    """
    success: bool = Field(..., description="操作是否成功")
    code: int = Field(..., description="响应代码（HTTP状态码或业务错误码）")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "code": 200,
                "message": "操作成功",
                "data": {}
            }
        }


class SuccessResponse(BaseResponse[T]):
    """
    成功响应
    
    用于所有成功的API响应
    
    Example:
        ```python
        return SuccessResponse(
            code=200,
            message="创建成功",
            data=project_data
        )
        ```
    """
    success: bool = Field(True, description="操作成功")
    code: int = Field(200, description="HTTP状态码")
    message: str = Field("操作成功", description="成功消息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "code": 200,
                "message": "操作成功",
                "data": {
                    "id": 1,
                    "name": "示例数据"
                }
            }
        }


class ErrorResponse(BaseResponse):
    """
    错误响应
    
    用于所有失败的API响应
    
    Example:
        ```python
        return ErrorResponse(
            code=404,
            message="资源不存在",
            data=None
        )
        ```
    """
    success: bool = Field(False, description="操作失败")
    code: int = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    data: None = Field(None, description="错误响应不包含数据")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "code": 404,
                "message": "资源不存在",
                "data": None
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应格式
    
    用于列表查询的分页响应
    
    Example:
        ```python
        return PaginatedResponse(
            items=[...],
            total=100,
            page=1,
            page_size=20,
            pages=5
        )
        ```
    """
    items: List[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, le=10000, description="每页记录数")
    pages: int = Field(..., ge=0, description="总页数")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"id": 1, "name": "项目1"},
                    {"id": 2, "name": "项目2"}
                ],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "pages": 5
            }
        }


class ListResponse(BaseModel, Generic[T]):
    """
    列表响应格式（无分页）
    
    用于不需要分页的列表响应
    
    Example:
        ```python
        return ListResponse(items=[...])
        ```
    """
    items: List[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总记录数")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"id": 1, "name": "选项1"},
                    {"id": 2, "name": "选项2"}
                ],
                "total": 2
            }
        }


# 便捷函数
def success_response(
    data: Optional[T] = None,
    message: str = "操作成功",
    code: int = 200
) -> SuccessResponse[T]:
    """
    创建成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
        code: HTTP状态码
    
    Returns:
        SuccessResponse: 成功响应对象
    """
    return SuccessResponse(code=code, message=message, data=data)


def error_response(
    message: str,
    code: int = 400,
    data: None = None
) -> ErrorResponse:
    """
    创建错误响应
    
    Args:
        message: 错误消息
        code: 错误代码
        data: 错误数据（通常为None）
    
    Returns:
        ErrorResponse: 错误响应对象
    """
    return ErrorResponse(code=code, message=message, data=data)


def paginated_response(
    items: List[T],
    total: int,
    page: int,
    page_size: int
) -> PaginatedResponse[T]:
    """
    创建分页响应
    
    Args:
        items: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页记录数
    
    Returns:
        PaginatedResponse: 分页响应对象
    """
    pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


def list_response(
    items: List[T],
    message: str = "获取成功",
    total: Optional[int] = None
) -> ListResponse[T]:
    """
    创建列表响应（无分页）
    
    Args:
        items: 数据列表
        message: 响应消息（可选，用于统一响应格式）
        total: 总记录数（如果不提供，则使用items的长度）
    
    Returns:
        ListResponse: 列表响应对象
    """
    if total is None:
        total = len(items)
    return ListResponse(items=items, total=total)


__all__ = [
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "ListResponse",
    "success_response",
    "error_response",
    "paginated_response",
    "list_response",
]
