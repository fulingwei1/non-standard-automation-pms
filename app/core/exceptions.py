# -*- coding: utf-8 -*-
"""
业务异常定义

FIXME: 这是一个临时实现，用于修复导入错误
TODO: 完善异常体系
"""

from fastapi import HTTPException


class BusinessException(HTTPException):
    """业务异常基类"""
    
    def __init__(self, message: str, code: int = 400):
        super().__init__(status_code=code, detail=message)
        self.message = message
        self.code = code
