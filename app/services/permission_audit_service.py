# -*- coding: utf-8 -*-
"""
权限审计服务
记录权限相关的操作日志
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.user import PermissionAudit


class PermissionAuditService:
    """权限审计服务"""

    # 操作类型常量
    ACTION_USER_CREATED = "USER_CREATED"
    ACTION_USER_UPDATED = "USER_UPDATED"
    ACTION_USER_DELETED = "USER_DELETED"
    ACTION_USER_ACTIVATED = "USER_ACTIVATED"
    ACTION_USER_DEACTIVATED = "USER_DEACTIVATED"
    ACTION_USER_ROLE_ASSIGNED = "USER_ROLE_ASSIGNED"
    ACTION_USER_ROLE_REVOKED = "USER_ROLE_REVOKED"

    ACTION_ROLE_CREATED = "ROLE_CREATED"
    ACTION_ROLE_UPDATED = "ROLE_UPDATED"
    ACTION_ROLE_DELETED = "ROLE_DELETED"
    ACTION_ROLE_ACTIVATED = "ROLE_ACTIVATED"
    ACTION_ROLE_DEACTIVATED = "ROLE_DEACTIVATED"
    ACTION_ROLE_PERMISSION_ASSIGNED = "ROLE_PERMISSION_ASSIGNED"
    ACTION_ROLE_PERMISSION_REVOKED = "ROLE_PERMISSION_REVOKED"

    ACTION_PERMISSION_CREATED = "PERMISSION_CREATED"
    ACTION_PERMISSION_UPDATED = "PERMISSION_UPDATED"
    ACTION_PERMISSION_DELETED = "PERMISSION_DELETED"

    @staticmethod
    def log_audit(
        db: Session,
        operator_id: int,
        action: str,
        target_type: str,
        target_id: int,
        detail: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PermissionAudit:
        """
        记录审计日志

        Args:
            db: 数据库会话
            operator_id: 操作人ID
            action: 操作类型
            target_type: 目标类型（user/role/permission）
            target_id: 目标ID
            detail: 详细信息（字典，会被序列化为JSON）
            ip_address: 操作IP地址
            user_agent: 用户代理

        Returns:
            创建的审计记录
        """
        import json

        audit = PermissionAudit(
            operator_id=operator_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=json.dumps(detail, ensure_ascii=False) if detail else None,
            ip_address=ip_address,
            user_agent=user_agent
        )

        db.add(audit)
        db.commit()
        db.refresh(audit)

        return audit

    @staticmethod
    def log_user_role_assignment(
        db: Session,
        operator_id: int,
        user_id: int,
        role_ids: list,
        action: str = ACTION_USER_ROLE_ASSIGNED,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """记录用户角色分配"""
        PermissionAuditService.log_audit(
            db=db,
            operator_id=operator_id,
            action=action,
            target_type="user",
            target_id=user_id,
            detail={
                "role_ids": role_ids,
                "description": f"分配角色: {role_ids}"
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    def log_role_permission_assignment(
        db: Session,
        operator_id: int,
        role_id: int,
        permission_ids: list,
        action: str = ACTION_ROLE_PERMISSION_ASSIGNED,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """记录角色权限分配"""
        PermissionAuditService.log_audit(
            db=db,
            operator_id=operator_id,
            action=action,
            target_type="role",
            target_id=role_id,
            detail={
                "permission_ids": permission_ids,
                "description": f"分配权限: {permission_ids}"
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    def log_user_operation(
        db: Session,
        operator_id: int,
        user_id: int,
        action: str,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """记录用户操作"""
        PermissionAuditService.log_audit(
            db=db,
            operator_id=operator_id,
            action=action,
            target_type="user",
            target_id=user_id,
            detail={
                "changes": changes,
                "description": f"用户操作: {action}"
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    def log_role_operation(
        db: Session,
        operator_id: int,
        role_id: int,
        action: str,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """记录角色操作"""
        PermissionAuditService.log_audit(
            db=db,
            operator_id=operator_id,
            action=action,
            target_type="role",
            target_id=role_id,
            detail={
                "changes": changes,
                "description": f"角色操作: {action}"
            },
            ip_address=ip_address,
            user_agent=user_agent
        )



