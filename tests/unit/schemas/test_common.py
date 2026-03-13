# -*- coding: utf-8 -*-
"""
common schema 单元测试

测试通用响应模型。
"""

import pytest

from app.schemas.common import ResponseModel


class TestResponseModel:
    """ResponseModel 测试"""

    def test_success_response(self):
        """200 响应自动设置 success=True"""
        r = ResponseModel(code=200, message="OK", data={"id": 1})
        assert r.success is True
        assert r.code == 200
        assert r.data == {"id": 1}

    def test_error_response(self):
        """400+ 响应自动设置 success=False"""
        r = ResponseModel(code=400, message="Bad Request")
        assert r.success is False
        assert r.code == 400

    def test_server_error_response(self):
        """500 响应自动设置 success=False"""
        r = ResponseModel(code=500, message="Internal Error")
        assert r.success is False

    def test_explicit_success_override(self):
        """显式指定 success 覆盖自动计算"""
        r = ResponseModel(success=False, code=200, message="Special case")
        assert r.success is False
        assert r.code == 200

    def test_default_values(self):
        """默认值测试"""
        r = ResponseModel()
        assert r.success is True
        assert r.code == 200
        assert r.message == "success"
        assert r.data is None

    def test_json_output(self):
        """JSON 输出包含 success 字段"""
        r = ResponseModel(code=200, data={"test": 1})
        json_dict = r.model_dump()
        assert "success" in json_dict
        assert json_dict["success"] is True

    def test_301_redirect_is_success(self):
        """3xx 重定向码视为成功"""
        r = ResponseModel(code=301, message="Redirect")
        assert r.success is True

    def test_201_created_is_success(self):
        """201 创建响应视为成功"""
        r = ResponseModel(code=201, message="Created", data={"id": 42})
        assert r.success is True
        assert r.data["id"] == 42
