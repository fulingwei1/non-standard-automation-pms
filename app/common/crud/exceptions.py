# -*- coding: utf-8 -*-
"""
CRUD相关异常定义
"""

from fastapi import HTTPException, status


class CRUDException(Exception):
    """CRUD基础异常"""
    pass


class NotFoundError(CRUDException):
    """资源不存在异常"""
    
    def __init__(self, resource_name: str, resource_id: int):
        self.resource_name = resource_name
        self.resource_id = resource_id
        super().__init__(f"{resource_name} (ID: {resource_id}) 不存在")


class AlreadyExistsError(CRUDException):
    """资源已存在异常"""
    
    def __init__(self, resource_name: str, field: str, value: str):
        self.resource_name = resource_name
        self.field = field
        self.value = value
        super().__init__(f"{resource_name} 的 {field}={value} 已存在")


class ValidationError(CRUDException):
    """验证错误"""
    
    def __init__(self, message: str, errors: dict = None):
        self.message = message
        self.errors = errors or {}
        super().__init__(message)


def raise_not_found(resource_name: str, resource_id: int):
    """抛出404异常"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource_name} (ID: {resource_id}) 不存在"
    )


def raise_already_exists(resource_name: str, field: str, value: str):
    """抛出409冲突异常"""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"{resource_name} 的 {field}={value} 已存在"
    )
