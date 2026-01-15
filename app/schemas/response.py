# -*- coding: utf-8 -*-
"""
响应 Schema 定义
"""

from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """统一响应模型"""
    success: bool = Field(default=True, description="是否成功")
    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="操作成功", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")

    @classmethod
    def success(cls, data: Any = None, message: str = "操作成功"):
        """成功响应"""
        return cls(success=True, code=200, message=message, data=data)

    @classmethod
    def error(cls, message: str = "操作失败", code: int = 400, data: Any = None):
        """错误响应"""
        return cls(success=False, code=code, message=message, data=data)