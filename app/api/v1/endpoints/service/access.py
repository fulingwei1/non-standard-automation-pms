# -*- coding: utf-8 -*-
"""
售后服务模块访问控制辅助函数

集中处理两类访问控制：
1. 基于项目的数据范围（工单、服务记录）
2. 基于创建人/作者的数据范围（沟通、满意度、模板等）
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.service import ServiceRecord, ServiceTicket
from app.models.user import User
from app.services.data_scope import DataScopeService
from app.services.data_scope.config import DataScopeConfig
from app.utils.db_helpers import get_or_404
from app.utils.permission_helpers import check_project_access_or_raise, filter_by_project_access


def filter_service_project_query(db: Session, query, current_user: User, project_id_column):
    """按项目数据范围过滤售后模块查询。"""
    return filter_by_project_access(db, query, current_user, project_id_column)


def ensure_project_ids_access_or_raise(
    db: Session,
    current_user: User,
    project_ids: list[int],
    error_message: Optional[str] = None,
) -> None:
    """校验当前用户对一组项目都有访问权限。"""
    for project_id in sorted({pid for pid in project_ids if pid is not None}):
        check_project_access_or_raise(
            db,
            current_user,
            project_id,
            error_message or "您没有权限访问该项目关联的售后数据",
        )


def ensure_service_ticket_access_or_raise(
    db: Session,
    current_user: User,
    ticket_id: int,
    error_message: Optional[str] = None,
) -> ServiceTicket:
    """校验工单访问权限。"""
    ticket = get_or_404(db, ServiceTicket, ticket_id, "服务工单不存在")
    check_project_access_or_raise(
        db,
        current_user,
        ticket.project_id,
        error_message or "您没有权限访问该服务工单",
    )
    return ticket


def ensure_service_record_access_or_raise(
    db: Session,
    current_user: User,
    record_id: int,
    error_message: Optional[str] = None,
) -> ServiceRecord:
    """校验服务记录访问权限。"""
    record = get_or_404(db, ServiceRecord, record_id, "服务记录不存在")
    check_project_access_or_raise(
        db,
        current_user,
        record.project_id,
        error_message or "您没有权限访问该服务记录",
    )
    return record


def filter_owned_service_query(
    db: Session,
    query,
    model,
    current_user: User,
    *,
    owner_field: str,
    additional_owner_fields: Optional[list[str]] = None,
):
    """按 owner 型数据范围过滤查询。"""
    return DataScopeService.filter_by_scope(
        db,
        query,
        model,
        current_user,
        DataScopeConfig(
            owner_field=owner_field,
            additional_owner_fields=additional_owner_fields,
            project_field=None,
            dept_through_project=False,
        ),
    )


def get_owned_service_object_or_404(
    db: Session,
    model,
    object_id: int,
    current_user: User,
    not_found_message: str,
    *,
    owner_field: str,
    additional_owner_fields: Optional[list[str]] = None,
):
    """获取当前用户数据范围内的 owner 型对象。"""
    query = db.query(model).filter(model.id == object_id)
    query = filter_owned_service_query(
        db,
        query,
        model,
        current_user,
        owner_field=owner_field,
        additional_owner_fields=additional_owner_fields,
    )
    obj = query.first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_message)
    return obj


def ensure_author_or_superuser(
    current_user: User,
    author_id: Optional[int],
    error_message: str = "您没有权限修改该知识库文章",
) -> None:
    """限制知识库写操作仅作者或超级管理员可执行。"""
    if current_user.is_superuser or author_id == current_user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
