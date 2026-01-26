# -*- coding: utf-8 -*-
"""
API响应测试辅助函数

用于处理统一响应格式的测试断言
"""

from typing import Any, Dict, List, Optional


def extract_data(response_data: Dict[str, Any]) -> Any:
    """
    从统一响应格式中提取数据
    
    支持两种格式：
    1. 新格式：{"success": true, "code": 200, "message": "...", "data": {...}}
    2. 旧格式：直接返回数据对象
    
    Args:
        response_data: API响应数据（字典）
    
    Returns:
        提取的数据对象
    """
    # 如果是新格式（有success字段）
    if "success" in response_data and "data" in response_data:
        return response_data["data"]
    # 如果是旧格式，直接返回
    return response_data


def extract_items(response_data: Dict[str, Any]) -> List[Any]:
    """
    从列表响应中提取items
    
    支持两种格式：
    1. 新格式（分页）：{"items": [...], "total": ..., "page": ...}
    2. 新格式（无分页）：{"items": [...], "total": ...}
    3. 旧格式：直接返回列表或 {"items": [...]}
    
    Args:
        response_data: API响应数据（字典）
    
    Returns:
        提取的items列表
    """
    # 如果直接是列表（旧格式）
    if isinstance(response_data, list):
        return response_data
    
    # 如果是字典，尝试提取items
    if isinstance(response_data, dict):
        # 新格式：有items字段
        if "items" in response_data:
            return response_data["items"]
        # 如果响应是SuccessResponse包装的ListResponse
        if "success" in response_data and "data" in response_data:
            data = response_data["data"]
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            if isinstance(data, list):
                return data
    
    return []


def assert_success_response(response_data: Dict[str, Any], expected_code: int = 200) -> Dict[str, Any]:
    """
    断言成功响应格式
    
    Args:
        response_data: API响应数据
        expected_code: 期望的状态码
    
    Returns:
        提取的数据对象
    
    Raises:
        AssertionError: 如果响应格式不正确
    """
    # 如果是新格式
    if "success" in response_data:
        assert response_data["success"] is True, f"响应应该成功，但 success={response_data.get('success')}"
        assert response_data["code"] == expected_code, f"期望状态码 {expected_code}，实际 {response_data.get('code')}"
        assert "data" in response_data, "响应应该包含data字段"
        return response_data["data"]
    
    # 如果是旧格式，直接返回（向后兼容）
    return response_data


def assert_paginated_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    断言分页响应格式
    
    Args:
        response_data: API响应数据
    
    Returns:
        包含items和total的字典
    
    Raises:
        AssertionError: 如果响应格式不正确
    """
    # 如果是新格式（PaginatedResponse）
    if "items" in response_data and "total" in response_data:
        assert "page" in response_data, "分页响应应该包含page字段"
        assert "page_size" in response_data, "分页响应应该包含page_size字段"
        return response_data
    
    # 如果是SuccessResponse包装的PaginatedResponse
    if "success" in response_data and "data" in response_data:
        data = response_data["data"]
        if isinstance(data, dict) and "items" in data:
            return data
    
    # 如果是旧格式，尝试兼容
    if isinstance(response_data, dict):
        return response_data
    
    raise AssertionError(f"无法识别分页响应格式: {response_data}")


def assert_list_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    断言列表响应格式（无分页）
    
    Args:
        response_data: API响应数据
    
    Returns:
        包含items和total的字典
    
    Raises:
        AssertionError: 如果响应格式不正确
    """
    # 如果直接是列表（旧格式）
    if isinstance(response_data, list):
        return {"items": response_data, "total": len(response_data)}
    
    # 如果是新格式（ListResponse）
    if "items" in response_data and "total" in response_data:
        return response_data
    
    # 如果是SuccessResponse包装的ListResponse
    if "success" in response_data and "data" in response_data:
        data = response_data["data"]
        if isinstance(data, dict) and "items" in data:
            return data
        if isinstance(data, list):
            return {"items": data, "total": len(data)}
    
    # 如果是旧格式字典，尝试兼容
    if isinstance(response_data, dict):
        return response_data
    
    raise AssertionError(f"无法识别列表响应格式: {response_data}")
