# -*- coding: utf-8 -*-
"""
业务异常定义

提供分层的业务异常体系，覆盖常见的业务错误场景：
- BusinessException: 通用业务异常 (400)
- NotFoundException: 资源不存在 (404)
- AlreadyExistsException: 资源已存在/冲突 (409)
- ValidationException: 业务验证失败 (400)
- OperationNotAllowedException: 操作不允许 (400)
- InsufficientDataException: 数据不足 (400)
"""

from fastapi import HTTPException


class BusinessException(HTTPException):
    """业务异常基类"""

    def __init__(self, message: str, code: int = 400):
        super().__init__(status_code=code, detail=message)
        self.message = message
        self.code = code


class NotFoundException(BusinessException):
    """资源不存在异常 (404)"""

    def __init__(self, resource_name: str, resource_id=None):
        if resource_id is not None:
            message = f"{resource_name} (ID={resource_id}) 不存在"
        else:
            message = f"{resource_name}不存在"
        super().__init__(message=message, code=404)
        self.resource_name = resource_name
        self.resource_id = resource_id


class AlreadyExistsException(BusinessException):
    """资源已存在/冲突异常 (409)"""

    def __init__(self, resource_name: str, field: str = None, value=None):
        if field and value is not None:
            message = f"{resource_name}的 {field}={value} 已存在"
        else:
            message = f"{resource_name}已存在"
        super().__init__(message=message, code=409)
        self.resource_name = resource_name


class ValidationException(BusinessException):
    """业务验证失败异常 (400)"""

    def __init__(self, message: str):
        super().__init__(message=message, code=400)


class OperationNotAllowedException(BusinessException):
    """操作不允许异常 (400)

    用于业务规则阻止的操作，例如：系统预置角色不允许删除、只有草稿状态才能编辑等。
    """

    def __init__(self, message: str):
        super().__init__(message=message, code=400)


class InsufficientDataException(BusinessException):
    """数据不足异常 (400)

    用于数据量不足以完成操作的场景，例如：历史数据不足无法预测。
    """

    def __init__(self, message: str):
        super().__init__(message=message, code=400)
