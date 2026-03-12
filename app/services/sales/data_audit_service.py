# -*- coding: utf-8 -*-
"""
销售数据审核服务

提供数据变更审核的完整工作流：
- 提交审核请求
- 查询待审核列表
- 审核通过/驳回
- 撤销审核请求
- 应用已审核的变更
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.sales.data_audit import (
    AUDIT_REQUIRED_FIELDS,
    DataAuditPriorityEnum,
    DataAuditStatusEnum,
    DataChangeType,
    SalesDataAuditRequest,
)
from app.models.sales.operation_log import SalesEntityType, SalesOperationType
from app.models.user import User
from app.services.sales.operation_log_service import SalesOperationLogService
from app.utils.status_helpers import assert_status_allows

logger = logging.getLogger(__name__)


class SalesDataAuditService:
    """销售数据审核服务类"""

    def __init__(self, db: Session):
        self.db = db

    def requires_audit(
        self, entity_type: str, changed_fields: List[str]
    ) -> bool:
        """
        判断数据变更是否需要审核

        Args:
            entity_type: 实体类型
            changed_fields: 变更的字段列表

        Returns:
            是否需要审核
        """
        audit_fields = AUDIT_REQUIRED_FIELDS.get(entity_type.upper(), [])
        # 如果变更字段中有任何一个需要审核的字段，则需要审核
        return any(field in audit_fields for field in changed_fields)

    def submit_audit_request(
        self,
        entity_type: str,
        entity_id: int,
        old_value: Dict[str, Any],
        new_value: Dict[str, Any],
        requester: User,
        *,
        entity_code: Optional[str] = None,
        change_type: str = DataChangeType.FIELD_UPDATE,
        change_reason: Optional[str] = None,
        priority: str = DataAuditPriorityEnum.NORMAL.value,
    ) -> SalesDataAuditRequest:
        """
        提交数据审核请求

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            old_value: 变更前值
            new_value: 变更后值
            requester: 申请人
            entity_code: 实体编码
            change_type: 变更类型
            change_reason: 变更原因
            priority: 优先级

        Returns:
            创建的审核请求
        """
        # 计算变更字段
        changed_fields = []
        for key in new_value:
            if key in old_value and old_value[key] != new_value[key]:
                changed_fields.append(key)

        # 检查是否有待处理的相同请求
        existing = (
            self.db.query(SalesDataAuditRequest)
            .filter(
                SalesDataAuditRequest.entity_type == entity_type.upper(),
                SalesDataAuditRequest.entity_id == entity_id,
                SalesDataAuditRequest.status == DataAuditStatusEnum.PENDING.value,
            )
            .first()
        )

        if existing:
            raise ValueError(f"该{_get_entity_name(entity_type)}已有待审核的变更请求，请等待审核完成")

        audit_request = SalesDataAuditRequest(
            entity_type=entity_type.upper(),
            entity_id=entity_id,
            entity_code=entity_code,
            change_type=change_type,
            change_reason=change_reason,
            old_value=old_value,
            new_value=new_value,
            changed_fields=changed_fields,
            status=DataAuditStatusEnum.PENDING.value,
            priority=priority,
            requester_id=requester.id,
            requester_dept=requester.department.name if requester.department else None,
            requested_at=datetime.now(),
        )

        self.db.add(audit_request)
        self.db.flush()

        logger.info(
            f"数据审核请求已创建: {entity_type}:{entity_id} by {requester.username}"
        )

        return audit_request

    def get_pending_requests(
        self,
        reviewer_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        priority: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[SalesDataAuditRequest], int]:
        """
        获取待审核请求列表

        Args:
            reviewer_id: 审核人ID（如果指定，返回该用户可审核的请求）
            entity_type: 实体类型筛选
            priority: 优先级筛选
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            (请求列表, 总数)
        """
        query = self.db.query(SalesDataAuditRequest).filter(
            SalesDataAuditRequest.status == DataAuditStatusEnum.PENDING.value
        )

        if entity_type:
            query = query.filter(
                SalesDataAuditRequest.entity_type == entity_type.upper()
            )

        if priority:
            query = query.filter(SalesDataAuditRequest.priority == priority.upper())

        total = query.count()
        requests = (
            query.order_by(
                SalesDataAuditRequest.priority,
                desc(SalesDataAuditRequest.requested_at),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return requests, total

    def approve_request(
        self,
        request_id: int,
        reviewer: User,
        comment: Optional[str] = None,
        apply_immediately: bool = True,
    ) -> SalesDataAuditRequest:
        """
        审核通过

        Args:
            request_id: 审核请求ID
            reviewer: 审核人
            comment: 审核意见
            apply_immediately: 是否立即应用变更

        Returns:
            更新后的审核请求
        """
        request = self._get_request(request_id)

        assert_status_allows(request, DataAuditStatusEnum.PENDING.value, "只能审核待处理的请求")

        if request.requester_id == reviewer.id:
            raise ValueError("不能审核自己提交的请求")

        request.status = DataAuditStatusEnum.APPROVED.value
        request.reviewer_id = reviewer.id
        request.reviewed_at = datetime.now()
        request.review_comment = comment

        if apply_immediately:
            self._apply_change(request, reviewer)

        self.db.flush()

        logger.info(
            f"数据审核请求已通过: {request.entity_type}:{request.entity_id} "
            f"by {reviewer.username}"
        )

        return request

    def reject_request(
        self,
        request_id: int,
        reviewer: User,
        comment: str,
    ) -> SalesDataAuditRequest:
        """
        审核驳回

        Args:
            request_id: 审核请求ID
            reviewer: 审核人
            comment: 驳回原因（必填）

        Returns:
            更新后的审核请求
        """
        if not comment:
            raise ValueError("驳回时必须填写原因")

        request = self._get_request(request_id)

        assert_status_allows(request, DataAuditStatusEnum.PENDING.value, "只能审核待处理的请求")

        request.status = DataAuditStatusEnum.REJECTED.value
        request.reviewer_id = reviewer.id
        request.reviewed_at = datetime.now()
        request.review_comment = comment

        self.db.flush()

        logger.info(
            f"数据审核请求已驳回: {request.entity_type}:{request.entity_id} "
            f"by {reviewer.username}, reason: {comment}"
        )

        return request

    def cancel_request(
        self,
        request_id: int,
        user: User,
        reason: Optional[str] = None,
    ) -> SalesDataAuditRequest:
        """
        撤销审核请求

        Args:
            request_id: 审核请求ID
            user: 操作用户
            reason: 撤销原因

        Returns:
            更新后的审核请求
        """
        request = self._get_request(request_id)

        assert_status_allows(request, DataAuditStatusEnum.PENDING.value, "只能撤销待处理的请求")

        if request.requester_id != user.id:
            raise ValueError("只能撤销自己提交的请求")

        request.status = DataAuditStatusEnum.CANCELLED.value
        request.review_comment = f"申请人撤销: {reason}" if reason else "申请人撤销"

        self.db.flush()

        logger.info(
            f"数据审核请求已撤销: {request.entity_type}:{request.entity_id} "
            f"by {user.username}"
        )

        return request

    def get_request_detail(self, request_id: int) -> SalesDataAuditRequest:
        """获取审核请求详情"""
        return self._get_request(request_id)

    def get_entity_audit_history(
        self,
        entity_type: str,
        entity_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[SalesDataAuditRequest], int]:
        """
        获取实体的审核历史

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            (审核历史列表, 总数)
        """
        query = self.db.query(SalesDataAuditRequest).filter(
            SalesDataAuditRequest.entity_type == entity_type.upper(),
            SalesDataAuditRequest.entity_id == entity_id,
        )

        total = query.count()
        requests = (
            query.order_by(desc(SalesDataAuditRequest.requested_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return requests, total

    def _get_request(self, request_id: int) -> SalesDataAuditRequest:
        """获取审核请求，不存在则抛出异常"""
        request = (
            self.db.query(SalesDataAuditRequest)
            .filter(SalesDataAuditRequest.id == request_id)
            .first()
        )

        if not request:
            raise ValueError(f"审核请求不存在: {request_id}")

        return request

    def _apply_change(
        self, request: SalesDataAuditRequest, applier: User
    ) -> None:
        """
        应用已审核的变更到实际数据

        Args:
            request: 审核请求
            applier: 执行人
        """
        entity_type = request.entity_type
        entity_id = request.entity_id
        new_value = request.new_value

        # 根据实体类型获取对应的模型类
        model_class = self._get_model_class(entity_type)
        if not model_class:
            logger.warning(f"未知的实体类型: {entity_type}")
            return

        entity = self.db.query(model_class).filter(model_class.id == entity_id).first()
        if not entity:
            logger.warning(f"实体不存在: {entity_type}:{entity_id}")
            return

        # 应用变更
        for field, value in new_value.items():
            if hasattr(entity, field):
                setattr(entity, field, value)

        request.applied_at = datetime.now()
        request.applied_by = applier.id

        # 记录操作日志
        SalesOperationLogService.log_operation(
            self.db,
            entity_type=entity_type,
            entity_id=entity_id,
            operation_type=SalesOperationType.UPDATE,
            operator=applier,
            entity_code=request.entity_code,
            operation_desc=f"审核通过后应用变更",
            old_value=request.old_value,
            new_value=request.new_value,
            changed_fields=request.changed_fields,
            remark=f"审核请求ID: {request.id}",
        )

        logger.info(
            f"数据变更已应用: {entity_type}:{entity_id}, "
            f"fields: {request.changed_fields}"
        )

    def _get_model_class(self, entity_type: str):
        """根据实体类型获取模型类"""
        from app.models.sales import Contract, Customer, Opportunity
        from app.models.sales.quotes import Quote

        model_map = {
            SalesEntityType.OPPORTUNITY: Opportunity,
            SalesEntityType.CONTRACT: Contract,
            SalesEntityType.CUSTOMER: Customer,
            SalesEntityType.QUOTE: Quote,
        }

        return model_map.get(entity_type)


def _get_entity_name(entity_type: str) -> str:
    """获取实体类型的中文名称"""
    names = {
        SalesEntityType.LEAD: "线索",
        SalesEntityType.OPPORTUNITY: "商机",
        SalesEntityType.QUOTE: "报价",
        SalesEntityType.CONTRACT: "合同",
        SalesEntityType.INVOICE: "发票",
        SalesEntityType.CUSTOMER: "客户",
    }
    return names.get(entity_type, entity_type)
