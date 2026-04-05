# -*- coding: utf-8 -*-
"""
合同服务子模块

将合同管理功能拆分为独立的服务：
- approval_service: 审批流程
- status_service: 状态流转
- term_service: 条款管理
- attachment_service: 附件管理
- analyzer: 统计分析
"""

from app.services.sales.contract.analyzer import ContractAnalyzer
from app.services.sales.contract.approval_service import ContractApprovalService
from app.services.sales.contract.attachment_service import ContractAttachmentService
from app.services.sales.contract.status_service import ContractStatusService
from app.services.sales.contract.term_service import ContractTermService

__all__ = [
    "ContractApprovalService",
    "ContractStatusService",
    "ContractTermService",
    "ContractAttachmentService",
    "ContractAnalyzer",
]
