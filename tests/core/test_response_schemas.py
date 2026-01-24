# -*- coding: utf-8 -*-
"""
统一响应格式测试
"""

import pytest
from app.core.schemas.response import (
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
    ListResponse,
    success_response,
    error_response,
    paginated_response,
)


def test_success_response():
    """测试成功响应"""
    response = success_response(
        data={"id": 1, "name": "测试"},
        message="操作成功"
    )
    
    assert response.success is True
    assert response.code == 200
    assert response.message == "操作成功"
    assert response.data == {"id": 1, "name": "测试"}


def test_error_response():
    """测试错误响应"""
    response = error_response(
        message="资源不存在",
        code=404
    )
    
    assert response.success is False
    assert response.code == 404
    assert response.message == "资源不存在"
    assert response.data is None


def test_paginated_response():
    """测试分页响应"""
    items = [{"id": i, "name": f"项目{i}"} for i in range(1, 21)]
    response = paginated_response(
        items=items,
        total=100,
        page=1,
        page_size=20
    )
    
    assert len(response.items) == 20
    assert response.total == 100
    assert response.page == 1
    assert response.page_size == 20
    assert response.pages == 5  # 100 / 20 = 5


def test_paginated_response_edge_cases():
    """测试分页响应边界情况"""
    # 空列表
    response = paginated_response(
        items=[],
        total=0,
        page=1,
        page_size=20
    )
    assert response.pages == 0
    
    # 最后一页
    response = paginated_response(
        items=[{"id": 1}],
        total=21,
        page=2,
        page_size=20
    )
    assert response.pages == 2


def test_response_serialization():
    """测试响应序列化"""
    response = success_response(data={"id": 1})
    json_data = response.model_dump()
    
    assert json_data["success"] is True
    assert json_data["code"] == 200
    assert "data" in json_data
