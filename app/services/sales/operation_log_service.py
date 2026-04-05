# -*- coding: utf-8 -*-
"""
销售业务操作日志服务

提供统一的操作日志记录和查询功能。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.sales.operation_log import (
    SalesEntityType,
    SalesOperationLog,
    SalesOperationType,
)
from app.models.user import User

logger = logging.getLogger(__name__)


class SalesOperationLogService:
    """销售操作日志服务类"""

    @staticmethod
    def log_operation(
        db: Session,
        entity_type: str,
        entity_id: int,
        operation_type: str,
        operator: User,
        *,
        entity_code: Optional[str] = None,
        operation_desc: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        changed_fields: Optional[List[str]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> SalesOperationLog:
        """
        记录一条操作日志

        Args:
            db: 数据库会话
            entity_type: 实体类型（LEAD/OPPORTUNITY/QUOTE/CONTRACT等）
            entity_id: 实体ID
            operation_type: 操作类型（CREATE/UPDATE/DELETE等）
            operator: 操作人用户对象
            entity_code: 实体编码（可选）
            operation_desc: 操作描述（可选）
            old_value: 变更前值（可选）
            new_value: 变更后值（可选）
            changed_fields: 变更字段列表（可选）
            ip_address: 操作IP地址（可选）
            user_agent: 浏览器UA（可选）
            request_id: 请求ID（可选）
            remark: 备注（可选）

        Returns:
            SalesOperationLog: 创建的日志记录
        """
        log_entry = SalesOperationLog(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_code=entity_code,
            operation_type=operation_type,
            operation_desc=operation_desc,
            old_value=old_value,
            new_value=new_value,
            changed_fields=changed_fields,
            operator_id=operator.id,
            operator_name=operator.real_name or operator.username,
            operator_dept=operator.department.name if operator.department else None,
            operation_time=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            remark=remark,
        )
        db.add(log_entry)
        db.flush()

        logger.debug(
            f"操作日志已记录: {entity_type}:{entity_id} {operation_type} by {operator.username}"
        )
        return log_entry

    @staticmethod
    def log_create(
        db: Session,
        entity_type: str,
        entity_id: int,
        operator: User,
        entity_code: Optional[str] = None,
        new_value: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SalesOperationLog:
        """记录创建操作"""
        return SalesOperationLogService.log_operation(
            db,
            entity_type=entity_type,
            entity_id=entity_id,
            operation_type=SalesOperationType.CREATE,
            operator=operator,
            entity_code=entity_code,
            operation_desc=f"创建{_get_entity_name(entity_type)}",
            new_value=new_value,
            **kwargs,
        )

    @staticmethod
    def log_update(
        db: Session,
        entity_type: str,
        entity_id: int,
        operator: User,
        old_value: Dict[str, Any],
        new_value: Dict[str, Any],
        entity_code: Optional[str] = None,
        **kwargs,
    ) -> SalesOperationLog:
        """记录更新操作"""
        # 计算变更字段
        changed_fields = []
        for key in new_value:
            if key in old_value and old_value[key] != new_value[key]:
                changed_fields.append(key)

        return SalesOperationLogService.log_operation(
            db,
            entity_type=entity_type,
            entity_id=entity_id,
            operation_type=SalesOperationType.UPDATE,
            operator=operator,
            entity_code=entity_code,
            operation_desc=f"更新{_get_entity_name(entity_type)}",
            old_value=old_value,
            new_value=new_value,
            changed_fields=changed_fields,
            **kwargs,
        )

    @staticmethod
    def log_status_change(
        db: Session,
        entity_type: str,
        entity_id: int,
        operator: User,
        old_status: str,
        new_status: str,
        entity_code: Optional[str] = None,
        **kwargs,
    ) -> SalesOperationLog:
        """记录状态变更"""
        return SalesOperationLogService.log_operation(
            db,
            entity_type=entity_type,
            entity_id=entity_id,
            operation_type=SalesOperationType.STATUS_CHANGE,
            operator=operator,
            entity_code=entity_code,
            operation_desc=f"{_get_entity_name(entity_type)}状态变更：{old_status} → {new_status}",
            old_value={"status": old_status},
            new_value={"status": new_status},
            changed_fields=["status"],
            **kwargs,
        )

    @staticmethod
    def log_approval(
        db: Session,
        entity_type: str,
        entity_id: int,
        operator: User,
        action: str,
        entity_code: Optional[str] = None,
        comment: Optional[str] = None,
        **kwargs,
    ) -> SalesOperationLog:
        """记录审批操作"""
        operation_type = (
            SalesOperationType.APPROVE if action == "approve" else SalesOperationType.REJECT
        )
        action_desc = "审批通过" if action == "approve" else "审批驳回"

        return SalesOperationLogService.log_operation(
            db,
            entity_type=entity_type,
            entity_id=entity_id,
            operation_type=operation_type,
            operator=operator,
            entity_code=entity_code,
            operation_desc=f"{_get_entity_name(entity_type)}{action_desc}",
            remark=comment,
            **kwargs,
        )

    @staticmethod
    def get_entity_logs(
        db: Session,
        entity_type: str,
        entity_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[SalesOperationLog], int]:
        """
        获取实体的操作日志列表

        Args:
            db: 数据库会话
            entity_type: 实体类型
            entity_id: 实体ID
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            (日志列表, 总数)
        """
        query = db.query(SalesOperationLog).filter(
            SalesOperationLog.entity_type == entity_type,
            SalesOperationLog.entity_id == entity_id,
        )

        total = query.count()
        logs = (
            query.order_by(desc(SalesOperationLog.operation_time))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return logs, total

    @staticmethod
    def search_logs(
        db: Session,
        *,
        entity_type: Optional[str] = None,
        operation_type: Optional[str] = None,
        operator_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[SalesOperationLog], int]:
        """
        搜索操作日志

        Args:
            db: 数据库会话
            entity_type: 实体类型筛选
            operation_type: 操作类型筛选
            operator_id: 操作人筛选
            start_time: 开始时间
            end_time: 结束时间
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            (日志列表, 总数)
        """
        query = db.query(SalesOperationLog)

        if entity_type:
            query = query.filter(SalesOperationLog.entity_type == entity_type)
        if operation_type:
            query = query.filter(SalesOperationLog.operation_type == operation_type)
        if operator_id:
            query = query.filter(SalesOperationLog.operator_id == operator_id)
        if start_time:
            query = query.filter(SalesOperationLog.operation_time >= start_time)
        if end_time:
            query = query.filter(SalesOperationLog.operation_time <= end_time)

        total = query.count()
        logs = (
            query.order_by(desc(SalesOperationLog.operation_time))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return logs, total


def _get_entity_name(entity_type: str) -> str:
    """获取实体类型的中文名称"""
    names = {
        SalesEntityType.LEAD: "线索",
        SalesEntityType.OPPORTUNITY: "商机",
        SalesEntityType.QUOTE: "报价",
        SalesEntityType.QUOTE_VERSION: "报价版本",
        SalesEntityType.CONTRACT: "合同",
        SalesEntityType.INVOICE: "发票",
        SalesEntityType.CUSTOMER: "客户",
    }
    return names.get(entity_type, entity_type)
