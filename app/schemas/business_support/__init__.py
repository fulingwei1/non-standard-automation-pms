# -*- coding: utf-8 -*-
"""
商务支持模块 Schema - 按业务域聚合
"""

# 验收单跟踪
from .acceptance import (
    AcceptanceTrackingCreate,
    AcceptanceTrackingRecordResponse,
    AcceptanceTrackingResponse,
    AcceptanceTrackingUpdate,
    ConditionCheckRequest,
    ReminderRequest,
)

# 投标管理
from .bidding import (
    BiddingDocumentCreate,
    BiddingDocumentResponse,
    BiddingProjectCreate,
    BiddingProjectResponse,
    BiddingProjectUpdate,
)

# 合同相关
from .contract import (
    ContractReviewCreate,
    ContractReviewResponse,
    ContractReviewUpdate,
    ContractSealRecordCreate,
    ContractSealRecordResponse,
    ContractSealRecordUpdate,
)

# 工作台统计
from .dashboard import (
    BusinessSupportDashboardResponse,
    PerformanceMetricsResponse,
)

# 发货管理
from .delivery import (
    DeliveryApprovalRequest,
    DeliveryOrderCreate,
    DeliveryOrderResponse,
    DeliveryOrderUpdate,
    DeliveryStatistics,
)

# 文档归档
from .document import (
    DocumentArchiveCreate,
    DocumentArchiveResponse,
    DocumentArchiveUpdate,
)

# 开票申请
from .invoice import (
    InvoiceRequestApproveRequest,
    InvoiceRequestCreate,
    InvoiceRequestRejectRequest,
    InvoiceRequestResponse,
    InvoiceRequestUpdate,
)

# 回款催收
from .payment import (
    PaymentReminderCreate,
    PaymentReminderResponse,
    PaymentReminderUpdate,
)

# 客户对账单
from .reconciliation import (
    ReconciliationCreate,
    ReconciliationResponse,
    ReconciliationUpdate,
)

# 客户供应商入驻
from .registration import (
    CustomerSupplierRegistrationCreate,
    CustomerSupplierRegistrationResponse,
    CustomerSupplierRegistrationUpdate,
    SupplierRegistrationReviewRequest,
)

# 销售报表
from .report import (
    ContractReportResponse,
    InvoiceReportResponse,
    PaymentReportResponse,
    SalesReportResponse,
)

# 销售订单管理
from .sales_order import (
    AssignProjectRequest,
    SalesOrderCreate,
    SalesOrderItemCreate,
    SalesOrderItemResponse,
    SalesOrderResponse,
    SalesOrderUpdate,
    SendNoticeRequest,
)

__all__ = [
    # 投标管理
    "BiddingProjectCreate",
    "BiddingProjectUpdate",
    "BiddingProjectResponse",
    "BiddingDocumentCreate",
    "BiddingDocumentResponse",
    # 合同相关
    "ContractReviewCreate",
    "ContractReviewUpdate",
    "ContractReviewResponse",
    "ContractSealRecordCreate",
    "ContractSealRecordUpdate",
    "ContractSealRecordResponse",
    # 回款催收
    "PaymentReminderCreate",
    "PaymentReminderUpdate",
    "PaymentReminderResponse",
    # 文档归档
    "DocumentArchiveCreate",
    "DocumentArchiveUpdate",
    "DocumentArchiveResponse",
    # 工作台统计
    "BusinessSupportDashboardResponse",
    "PerformanceMetricsResponse",
    # 销售订单管理
    "SalesOrderItemCreate",
    "SalesOrderItemResponse",
    "SalesOrderCreate",
    "SalesOrderUpdate",
    "SalesOrderResponse",
    "AssignProjectRequest",
    "SendNoticeRequest",
    # 发货管理
    "DeliveryOrderCreate",
    "DeliveryOrderUpdate",
    "DeliveryOrderResponse",
    "DeliveryApprovalRequest",
    "DeliveryStatistics",
    # 验收单跟踪
    "AcceptanceTrackingCreate",
    "AcceptanceTrackingUpdate",
    "AcceptanceTrackingResponse",
    "ConditionCheckRequest",
    "ReminderRequest",
    "AcceptanceTrackingRecordResponse",
    # 客户对账单
    "ReconciliationCreate",
    "ReconciliationUpdate",
    "ReconciliationResponse",
    # 销售报表
    "SalesReportResponse",
    "PaymentReportResponse",
    "ContractReportResponse",
    "InvoiceReportResponse",
    # 开票申请
    "InvoiceRequestCreate",
    "InvoiceRequestUpdate",
    "InvoiceRequestResponse",
    "InvoiceRequestApproveRequest",
    "InvoiceRequestRejectRequest",
    # 客户供应商入驻
    "CustomerSupplierRegistrationCreate",
    "CustomerSupplierRegistrationUpdate",
    "CustomerSupplierRegistrationResponse",
    "SupplierRegistrationReviewRequest",
]
