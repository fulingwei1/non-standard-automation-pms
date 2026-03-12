# -*- coding: utf-8 -*-
"""
API 响应帮助模块

提供统一的响应格式创建函数，确保所有 API 返回一致的格式
"""

from typing import Any, Dict, List

from app.schemas.common import PaginatedResponse, ResponseModel


def success_response(
    data: Any = None,
    message: str = "success",
    code: int = 200,
) -> ResponseModel:
    """
    创建成功响应

    Args:
        data: 响应数据
        message: 响应消息
        code: 响应代码

    Returns:
        ResponseModel: 统一格式的成功响应

    Examples:
        >>> return success_response({"id": 1}, "创建成功", 201)
        >>> return success_response(user_data)
    """
    return ResponseModel(code=code, message=message, data=data)


def error_response(
    message: str,
    code: int = 400,
    data: Any = None,
) -> ResponseModel:
    """
    创建错误响应

    Args:
        message: 错误消息
        code: 错误代码
        data: 错误详情数据

    Returns:
        ResponseModel: 统一格式的错误响应

    Examples:
        >>> return error_response("参数无效", 400)
        >>> return error_response("未授权", 401)
    """
    return ResponseModel(code=code, message=message, data=data)


def paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse:
    """
    创建分页响应

    Args:
        items: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页条数

    Returns:
        PaginatedResponse: 统一格式的分页响应

    Examples:
        >>> return paginated_response(leads, total=100, page=1, page_size=20)
    """
    pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def list_response(
    items: List[Any],
    message: str = "success",
) -> ResponseModel:
    """
    创建列表响应（不分页）

    Args:
        items: 数据列表
        message: 响应消息

    Returns:
        ResponseModel: 包含列表数据的统一响应

    Examples:
        >>> return list_response(tags)
    """
    return ResponseModel(
        code=200,
        message=message,
        data={"items": items, "total": len(items)},
    )


def created_response(
    data: Any,
    message: str = "创建成功",
) -> ResponseModel:
    """
    创建资源创建成功响应

    Args:
        data: 创建的资源数据
        message: 响应消息

    Returns:
        ResponseModel: 201 创建成功响应
    """
    return ResponseModel(code=201, message=message, data=data)


def deleted_response(
    message: str = "删除成功",
) -> ResponseModel:
    """
    创建资源删除成功响应

    Args:
        message: 响应消息

    Returns:
        ResponseModel: 204 删除成功响应
    """
    return ResponseModel(code=200, message=message, data=None)


def batch_response(
    total: int,
    success_count: int,
    results: List[Dict[str, Any]],
) -> ResponseModel:
    """
    创建批量操作响应

    Args:
        total: 总操作数
        success_count: 成功数
        results: 每项操作结果详情

    Returns:
        ResponseModel: 批量操作响应
    """
    return ResponseModel(
        code=200,
        message=f"批量操作完成: {success_count}/{total} 成功",
        data={
            "total": total,
            "success_count": success_count,
            "failed_count": total - success_count,
            "results": results,
        },
    )


# ==================== 类型化响应工厂 ====================


class ApiResponse:
    """
    API 响应工厂类

    提供链式调用和类型提示支持

    Examples:
        >>> return ApiResponse.ok(user_data)
        >>> return ApiResponse.created({"id": 1})
        >>> return ApiResponse.error("Not found", 404)
        >>> return ApiResponse.paginate(items, total, page, page_size)
    """

    @staticmethod
    def ok(data: Any = None, message: str = "success") -> ResponseModel:
        """200 成功响应"""
        return success_response(data, message, 200)

    @staticmethod
    def created(data: Any, message: str = "创建成功") -> ResponseModel:
        """201 创建成功响应"""
        return created_response(data, message)

    @staticmethod
    def deleted(message: str = "删除成功") -> ResponseModel:
        """删除成功响应"""
        return deleted_response(message)

    @staticmethod
    def error(message: str, code: int = 400, data: Any = None) -> ResponseModel:
        """错误响应"""
        return error_response(message, code, data)

    @staticmethod
    def not_found(message: str = "资源不存在") -> ResponseModel:
        """404 未找到响应"""
        return error_response(message, 404)

    @staticmethod
    def forbidden(message: str = "无权限访问") -> ResponseModel:
        """403 禁止访问响应"""
        return error_response(message, 403)

    @staticmethod
    def paginate(
        items: List[Any],
        total: int,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """分页响应"""
        return paginated_response(items, total, page, page_size)

    @staticmethod
    def batch(
        total: int,
        success_count: int,
        results: List[Dict[str, Any]],
    ) -> ResponseModel:
        """批量操作响应"""
        return batch_response(total, success_count, results)
