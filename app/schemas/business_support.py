# -*- coding: utf-8 -*-
"""
商务支持模块 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

from .common import BaseSchema, TimestampSchema


# ==================== 投标管理 ====================


class BiddingProjectCreate(BaseModel):
    """创建投标项目"""

    bidding_no: str = Field(max_length=50, description="投标编号")
    project_name: str = Field(max_length=500, description="项目名称")
    customer_id: Optional[int] = Field(default=None, description="客户ID")
    customer_name: Optional[str] = Field(default=None, max_length=200, description="客户名称")
    tender_no: Optional[str] = Field(default=None, max_length=100, description="招标编号")
    tender_type: Optional[str] = Field(default=None, max_length=20, description="招标类型")
    tender_platform: Optional[str] = Field(default=None, max_length=200, description="招标平台")
    tender_url: Optional[str] = Field(default=None, max_length=500, description="招标链接")
    publish_date: Optional[date] = Field(default=None, description="发布日期")
    deadline_date: Optional[datetime] = Field(default=None, description="投标截止时间")
    bid_opening_date: Optional[datetime] = Field(default=None, description="开标时间")
    bid_bond: Optional[Decimal] = Field(default=None, description="投标保证金")
    bid_bond_status: Optional[str] = Field(default="not_required", max_length=20, description="保证金状态")
    estimated_amount: Optional[Decimal] = Field(default=None, description="预估金额")
    submission_method: Optional[str] = Field(default=None, max_length=20, description="投递方式")
    submission_address: Optional[str] = Field(default=None, max_length=500, description="投递地址")
    sales_person_id: Optional[int] = Field(default=None, description="业务员ID")
    sales_person_name: Optional[str] = Field(default=None, max_length=50, description="业务员")
    support_person_id: Optional[int] = Field(default=None, description="商务支持ID")
    support_person_name: Optional[str] = Field(default=None, max_length=50, description="商务支持")
    remark: Optional[str] = Field(default=None, description="备注")


class BiddingProjectUpdate(BaseModel):
    """更新投标项目"""

    project_name: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    tender_no: Optional[str] = None
    tender_type: Optional[str] = None
    tender_platform: Optional[str] = None
    tender_url: Optional[str] = None
    publish_date: Optional[date] = None
    deadline_date: Optional[datetime] = None
    bid_opening_date: Optional[datetime] = None
    bid_bond: Optional[Decimal] = None
    bid_bond_status: Optional[str] = None
    estimated_amount: Optional[Decimal] = None
    bid_document_status: Optional[str] = None
    technical_doc_ready: Optional[bool] = None
    commercial_doc_ready: Optional[bool] = None
    qualification_doc_ready: Optional[bool] = None
    submission_method: Optional[str] = None
    submission_address: Optional[str] = None
    sales_person_id: Optional[int] = None
    sales_person_name: Optional[str] = None
    support_person_id: Optional[int] = None
    support_person_name: Optional[str] = None
    bid_result: Optional[str] = None
    bid_price: Optional[Decimal] = None
    win_price: Optional[Decimal] = None
    result_date: Optional[date] = None
    result_remark: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class BiddingProjectResponse(TimestampSchema):
    """投标项目响应"""

    id: int
    bidding_no: str
    project_name: str
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    tender_no: Optional[str] = None
    tender_type: Optional[str] = None
    tender_platform: Optional[str] = None
    tender_url: Optional[str] = None
    publish_date: Optional[date] = None
    deadline_date: Optional[datetime] = None
    bid_opening_date: Optional[datetime] = None
    bid_bond: Optional[Decimal] = None
    bid_bond_status: Optional[str] = None
    estimated_amount: Optional[Decimal] = None
    bid_document_status: Optional[str] = None
    technical_doc_ready: Optional[bool] = None
    commercial_doc_ready: Optional[bool] = None
    qualification_doc_ready: Optional[bool] = None
    submission_method: Optional[str] = None
    submission_address: Optional[str] = None
    sales_person_id: Optional[int] = None
    sales_person_name: Optional[str] = None
    support_person_id: Optional[int] = None
    support_person_name: Optional[str] = None
    bid_result: Optional[str] = None
    bid_price: Optional[Decimal] = None
    win_price: Optional[Decimal] = None
    result_date: Optional[date] = None
    result_remark: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class BiddingDocumentCreate(BaseModel):
    """创建投标文件"""

    bidding_project_id: int = Field(description="投标项目ID")
    document_type: str = Field(max_length=50, description="文件类型")
    document_name: str = Field(max_length=200, description="文件名称")
    file_path: str = Field(max_length=500, description="文件路径")
    file_size: Optional[int] = Field(default=None, description="文件大小(字节)")
    version: Optional[str] = Field(default=None, max_length=20, description="版本号")
    remark: Optional[str] = Field(default=None, description="备注")


class BiddingDocumentResponse(TimestampSchema):
    """投标文件响应"""

    id: int
    bidding_project_id: int
    document_type: Optional[str] = None
    document_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    version: Optional[str] = None
    status: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    remark: Optional[str] = None


# ==================== 合同审核 ====================


class ContractReviewCreate(BaseModel):
    """创建合同审核"""

    contract_id: int = Field(description="合同ID")
    review_type: str = Field(max_length=20, description="审核类型")
    review_comment: Optional[str] = Field(default=None, description="审核意见")
    risk_items: Optional[dict] = Field(default=None, description="风险项列表")


class ContractReviewUpdate(BaseModel):
    """更新合同审核"""

    review_status: Optional[str] = None
    review_comment: Optional[str] = None
    risk_items: Optional[dict] = None


class ContractReviewResponse(TimestampSchema):
    """合同审核响应"""

    id: int
    contract_id: int
    review_type: Optional[str] = None
    review_status: Optional[str] = None
    reviewer_id: Optional[int] = None
    review_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    risk_items: Optional[dict] = None


# ==================== 合同盖章邮寄 ====================


class ContractSealRecordCreate(BaseModel):
    """创建合同盖章记录"""

    contract_id: int = Field(description="合同ID")
    seal_date: Optional[date] = Field(default=None, description="盖章日期")
    send_date: Optional[date] = Field(default=None, description="邮寄日期")
    tracking_no: Optional[str] = Field(default=None, max_length=50, description="快递单号")
    courier_company: Optional[str] = Field(default=None, max_length=50, description="快递公司")
    remark: Optional[str] = Field(default=None, description="备注")


class ContractSealRecordUpdate(BaseModel):
    """更新合同盖章记录"""

    seal_status: Optional[str] = None
    seal_date: Optional[date] = None
    send_date: Optional[date] = None
    tracking_no: Optional[str] = None
    courier_company: Optional[str] = None
    receive_date: Optional[date] = None
    archive_date: Optional[date] = None
    archive_location: Optional[str] = None
    remark: Optional[str] = None


class ContractSealRecordResponse(TimestampSchema):
    """合同盖章记录响应"""

    id: int
    contract_id: int
    seal_status: Optional[str] = None
    seal_date: Optional[date] = None
    seal_operator_id: Optional[int] = None
    send_date: Optional[date] = None
    tracking_no: Optional[str] = None
    courier_company: Optional[str] = None
    receive_date: Optional[date] = None
    archive_date: Optional[date] = None
    archive_location: Optional[str] = None
    remark: Optional[str] = None


# ==================== 回款催收 ====================


class PaymentReminderCreate(BaseModel):
    """创建回款催收记录"""

    contract_id: int = Field(description="合同ID")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    payment_node: Optional[str] = Field(default=None, max_length=50, description="付款节点")
    payment_amount: Optional[Decimal] = Field(default=None, description="应回款金额")
    plan_date: Optional[date] = Field(default=None, description="计划回款日期")
    reminder_type: str = Field(max_length=20, description="催收类型")
    reminder_content: str = Field(description="催收内容")
    reminder_date: date = Field(description="催收日期")
    customer_response: Optional[str] = Field(default=None, description="客户反馈")
    next_reminder_date: Optional[date] = Field(default=None, description="下次催收日期")
    remark: Optional[str] = Field(default=None, description="备注")


class PaymentReminderUpdate(BaseModel):
    """更新回款催收记录"""

    reminder_type: Optional[str] = None
    reminder_content: Optional[str] = None
    reminder_date: Optional[date] = None
    customer_response: Optional[str] = None
    next_reminder_date: Optional[date] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class PaymentReminderResponse(TimestampSchema):
    """回款催收记录响应"""

    id: int
    contract_id: int
    project_id: Optional[int] = None
    payment_node: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    plan_date: Optional[date] = None
    reminder_type: Optional[str] = None
    reminder_content: Optional[str] = None
    reminder_date: Optional[date] = None
    reminder_person_id: Optional[int] = None
    customer_response: Optional[str] = None
    next_reminder_date: Optional[date] = None
    status: Optional[str] = None
    remark: Optional[str] = None


# ==================== 文件归档 ====================


class DocumentArchiveCreate(BaseModel):
    """创建文件归档"""

    archive_no: str = Field(max_length=50, description="归档编号")
    document_type: str = Field(max_length=50, description="文件类型")
    related_type: str = Field(max_length=50, description="关联类型")
    related_id: int = Field(description="关联ID")
    document_name: str = Field(max_length=200, description="文件名称")
    file_path: str = Field(max_length=500, description="文件路径")
    file_size: Optional[int] = Field(default=None, description="文件大小(字节)")
    archive_location: Optional[str] = Field(default=None, max_length=200, description="归档位置")
    archive_date: date = Field(description="归档日期")
    remark: Optional[str] = Field(default=None, description="备注")


class DocumentArchiveUpdate(BaseModel):
    """更新文件归档"""

    document_name: Optional[str] = None
    archive_location: Optional[str] = None
    archive_date: Optional[date] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class DocumentArchiveResponse(TimestampSchema):
    """文件归档响应"""

    id: int
    archive_no: str
    document_type: Optional[str] = None
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    document_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    archive_location: Optional[str] = None
    archive_date: Optional[date] = None
    archiver_id: Optional[int] = None
    status: Optional[str] = None
    remark: Optional[str] = None


# ==================== 工作台统计 ====================


class BusinessSupportDashboardResponse(BaseModel):
    """商务支持工作台统计响应"""

    active_contracts_count: int = Field(description="进行中合同数")
    pending_amount: Decimal = Field(description="待回款金额")
    overdue_amount: Decimal = Field(description="逾期款项")
    invoice_rate: Decimal = Field(description="本月开票率")
    active_bidding_count: int = Field(description="进行中投标数")
    acceptance_rate: Decimal = Field(description="验收按期率")
    urgent_tasks: List[dict] = Field(default_factory=list, description="紧急任务列表")
    today_todos: List[dict] = Field(default_factory=list, description="今日待办列表")


class PerformanceMetricsResponse(BaseModel):
    """本月绩效指标响应"""

    new_contracts_count: int = Field(description="新签合同数（本月签订的合同）")
    payment_completion_rate: Decimal = Field(description="回款完成率（本月实际回款/计划回款）")
    invoice_timeliness_rate: Decimal = Field(description="开票及时率（按时开票数/应开票数）")
    document_flow_count: int = Field(description="文件流转数（本月处理的文件数）")
    month: str = Field(description="统计月份（YYYY-MM格式）")


# ==================== 销售订单管理 ====================


class SalesOrderItemCreate(BaseModel):
    """创建销售订单明细"""

    item_name: str = Field(max_length=200, description="明细名称")
    item_spec: Optional[str] = Field(default=None, max_length=200, description="规格型号")
    qty: Decimal = Field(description="数量")
    unit: Optional[str] = Field(default=None, max_length=20, description="单位")
    unit_price: Decimal = Field(description="单价")
    amount: Decimal = Field(description="金额")
    remark: Optional[str] = Field(default=None, description="备注")


class SalesOrderItemResponse(TimestampSchema):
    """销售订单明细响应"""

    id: int
    sales_order_id: int
    item_name: Optional[str] = None
    item_spec: Optional[str] = None
    qty: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    remark: Optional[str] = None


class SalesOrderCreate(BaseModel):
    """创建销售订单"""

    order_no: Optional[str] = Field(default=None, max_length=50, description="订单编号（不提供则自动生成）")
    contract_id: Optional[int] = Field(default=None, description="合同ID")
    customer_id: int = Field(description="客户ID")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    order_type: Optional[str] = Field(default="standard", max_length=20, description="订单类型")
    order_amount: Decimal = Field(description="订单金额")
    currency: Optional[str] = Field(default="CNY", max_length=10, description="币种")
    required_date: Optional[date] = Field(default=None, description="客户要求日期")
    promised_date: Optional[date] = Field(default=None, description="承诺交期")
    sales_person_id: Optional[int] = Field(default=None, description="业务员ID")
    sales_person_name: Optional[str] = Field(default=None, max_length=50, description="业务员")
    remark: Optional[str] = Field(default=None, description="备注")
    items: Optional[List[SalesOrderItemCreate]] = Field(default_factory=list, description="订单明细")


class SalesOrderUpdate(BaseModel):
    """更新销售订单"""

    order_type: Optional[str] = None
    order_amount: Optional[Decimal] = None
    required_date: Optional[date] = None
    promised_date: Optional[date] = None
    order_status: Optional[str] = None
    erp_order_no: Optional[str] = None
    remark: Optional[str] = None


class SalesOrderResponse(TimestampSchema):
    """销售订单响应"""

    id: int
    order_no: str
    contract_id: Optional[int] = None
    contract_no: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    project_id: Optional[int] = None
    project_no: Optional[str] = None
    order_type: Optional[str] = None
    order_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    required_date: Optional[date] = None
    promised_date: Optional[date] = None
    order_status: Optional[str] = None
    project_no_assigned: Optional[bool] = None
    project_no_assigned_date: Optional[datetime] = None
    project_notice_sent: Optional[bool] = None
    project_notice_date: Optional[datetime] = None
    erp_order_no: Optional[str] = None
    erp_sync_status: Optional[str] = None
    sales_person_id: Optional[int] = None
    sales_person_name: Optional[str] = None
    support_person_id: Optional[int] = None
    remark: Optional[str] = None
    items: Optional[List[SalesOrderItemResponse]] = None


class AssignProjectRequest(BaseModel):
    """分配项目号请求"""

    project_id: int = Field(description="项目ID")
    project_no: Optional[str] = Field(default=None, max_length=50, description="项目号（不提供则使用项目编码）")


class SendNoticeRequest(BaseModel):
    """发送项目通知单请求"""

    notice_content: Optional[str] = Field(default=None, description="通知内容")
    recipients: Optional[List[int]] = Field(default_factory=list, description="接收人ID列表")


# ==================== 发货管理 ====================


class DeliveryOrderCreate(BaseModel):
    """创建发货单"""

    delivery_no: Optional[str] = Field(default=None, max_length=50, description="送货单号（不提供则自动生成）")
    order_id: int = Field(description="销售订单ID")
    delivery_date: date = Field(description="发货日期")
    delivery_type: str = Field(max_length=20, description="发货方式")
    logistics_company: Optional[str] = Field(default=None, max_length=100, description="物流公司")
    tracking_no: Optional[str] = Field(default=None, max_length=100, description="物流单号")
    receiver_name: Optional[str] = Field(default=None, max_length=50, description="收货人")
    receiver_phone: Optional[str] = Field(default=None, max_length=20, description="收货电话")
    receiver_address: Optional[str] = Field(default=None, max_length=500, description="收货地址")
    delivery_amount: Decimal = Field(description="本次发货金额")
    special_approval: Optional[bool] = Field(default=False, description="是否特殊审批")
    special_approval_reason: Optional[str] = Field(default=None, description="特殊审批原因")
    remark: Optional[str] = Field(default=None, description="备注")


class DeliveryOrderUpdate(BaseModel):
    """更新发货单"""

    delivery_date: Optional[date] = None
    delivery_type: Optional[str] = None
    logistics_company: Optional[str] = None
    tracking_no: Optional[str] = None
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    receiver_address: Optional[str] = None
    delivery_amount: Optional[Decimal] = None
    delivery_status: Optional[str] = None
    remark: Optional[str] = None


class DeliveryOrderResponse(TimestampSchema):
    """发货单响应"""

    id: int
    delivery_no: str
    order_id: int
    order_no: Optional[str] = None
    contract_id: Optional[int] = None
    customer_id: int
    customer_name: Optional[str] = None
    project_id: Optional[int] = None
    delivery_date: Optional[date] = None
    delivery_type: Optional[str] = None
    logistics_company: Optional[str] = None
    tracking_no: Optional[str] = None
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    receiver_address: Optional[str] = None
    delivery_amount: Optional[Decimal] = None
    approval_status: Optional[str] = None
    approval_comment: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    special_approval: Optional[bool] = None
    special_approver_id: Optional[int] = None
    special_approval_reason: Optional[str] = None
    delivery_status: Optional[str] = None
    print_date: Optional[datetime] = None
    ship_date: Optional[datetime] = None
    receive_date: Optional[date] = None
    return_status: Optional[str] = None
    return_date: Optional[date] = None
    remark: Optional[str] = None


class DeliveryApprovalRequest(BaseModel):
    """发货审批请求"""

    approved: bool = Field(description="是否审批通过")
    approval_comment: Optional[str] = Field(default=None, description="审批意见")


# ==================== 验收单跟踪 ====================


class AcceptanceTrackingCreate(BaseModel):
    """创建验收单跟踪记录"""

    acceptance_order_id: int = Field(description="验收单ID")
    contract_id: Optional[int] = Field(default=None, description="合同ID")
    sales_person_id: Optional[int] = Field(default=None, description="业务员ID")
    remark: Optional[str] = Field(default=None, description="备注")


class AcceptanceTrackingUpdate(BaseModel):
    """更新验收单跟踪记录"""

    condition_check_status: Optional[str] = None
    condition_check_result: Optional[str] = None
    tracking_status: Optional[str] = None
    received_date: Optional[date] = None
    report_status: Optional[str] = None
    warranty_start_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    remark: Optional[str] = None


class AcceptanceTrackingResponse(TimestampSchema):
    """验收单跟踪响应"""

    id: int
    acceptance_order_id: int
    acceptance_order_no: Optional[str] = None
    project_id: int
    project_code: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    condition_check_status: Optional[str] = None
    condition_check_result: Optional[str] = None
    condition_check_date: Optional[datetime] = None
    condition_checker_id: Optional[int] = None
    tracking_status: Optional[str] = None
    reminder_count: Optional[int] = None
    last_reminder_date: Optional[datetime] = None
    last_reminder_by: Optional[int] = None
    received_date: Optional[date] = None
    signed_file_id: Optional[int] = None
    report_status: Optional[str] = None
    report_generated_date: Optional[datetime] = None
    report_signed_date: Optional[datetime] = None
    report_archived_date: Optional[datetime] = None
    warranty_start_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    warranty_status: Optional[str] = None
    warranty_expiry_reminded: Optional[bool] = None
    contract_id: Optional[int] = None
    contract_no: Optional[str] = None
    sales_person_id: Optional[int] = None
    sales_person_name: Optional[str] = None
    support_person_id: Optional[int] = None
    remark: Optional[str] = None
    tracking_records: Optional[List[dict]] = None


class ConditionCheckRequest(BaseModel):
    """验收条件检查请求"""

    condition_check_status: str = Field(description="检查状态：met/not_met")
    condition_check_result: str = Field(description="检查结果")
    remark: Optional[str] = Field(default=None, description="备注")


class ReminderRequest(BaseModel):
    """催签请求"""

    reminder_content: Optional[str] = Field(default=None, description="催签内容")
    remark: Optional[str] = Field(default=None, description="备注")


class AcceptanceTrackingRecordResponse(TimestampSchema):
    """验收单跟踪记录明细响应"""

    id: int
    tracking_id: int
    record_type: str
    record_content: Optional[str] = None
    record_date: datetime
    operator_id: int
    operator_name: Optional[str] = None
    result: Optional[str] = None
    remark: Optional[str] = None


# ==================== 客户对账单 ====================


class ReconciliationCreate(BaseModel):
    """创建客户对账单"""

    customer_id: int = Field(description="客户ID")
    period_start: date = Field(description="对账开始日期")
    period_end: date = Field(description="对账结束日期")
    remark: Optional[str] = Field(default=None, description="备注")


class ReconciliationUpdate(BaseModel):
    """更新客户对账单"""

    status: Optional[str] = None
    sent_date: Optional[date] = None
    customer_confirmed: Optional[bool] = None
    customer_confirm_date: Optional[date] = None
    customer_difference: Optional[Decimal] = None
    difference_reason: Optional[str] = None
    remark: Optional[str] = None


class ReconciliationResponse(TimestampSchema):
    """客户对账单响应"""

    id: int
    reconciliation_no: str
    customer_id: int
    customer_name: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    opening_balance: Optional[Decimal] = None
    period_sales: Optional[Decimal] = None
    period_receipt: Optional[Decimal] = None
    closing_balance: Optional[Decimal] = None
    status: Optional[str] = None
    sent_date: Optional[date] = None
    confirm_date: Optional[date] = None
    customer_confirmed: Optional[bool] = None
    customer_confirm_date: Optional[date] = None
    customer_difference: Optional[Decimal] = None
    difference_reason: Optional[str] = None
    reconciliation_file_id: Optional[int] = None
    confirmed_file_id: Optional[int] = None
    remark: Optional[str] = None


# ==================== 销售报表 ====================


class SalesReportResponse(BaseModel):
    """销售报表响应"""

    report_date: str = Field(description="报表日期（YYYY-MM-DD或YYYY-MM或YYYY-WW格式）")
    report_type: str = Field(description="报表类型：daily/weekly/monthly")
    
    # 合同统计
    new_contracts_count: int = Field(description="新签合同数")
    new_contracts_amount: Decimal = Field(description="新签合同金额")
    active_contracts_count: int = Field(description="进行中合同数")
    completed_contracts_count: int = Field(description="已完成合同数")
    
    # 订单统计
    new_orders_count: int = Field(description="新订单数")
    new_orders_amount: Decimal = Field(description="新订单金额")
    
    # 回款统计
    planned_receipt_amount: Decimal = Field(description="计划回款金额")
    actual_receipt_amount: Decimal = Field(description="实际回款金额")
    receipt_completion_rate: Decimal = Field(description="回款完成率")
    overdue_amount: Decimal = Field(description="逾期金额")
    
    # 开票统计
    invoices_count: int = Field(description="开票数量")
    invoices_amount: Decimal = Field(description="开票金额")
    invoice_rate: Decimal = Field(description="开票率")
    
    # 投标统计
    new_bidding_count: int = Field(description="新增投标数")
    won_bidding_count: int = Field(description="中标数")
    bidding_win_rate: Decimal = Field(description="中标率")


class PaymentReportResponse(BaseModel):
    """回款统计报表响应"""

    report_date: str = Field(description="报表日期")
    report_type: str = Field(description="报表类型")
    
    # 回款汇总
    total_planned_amount: Decimal = Field(description="总计划回款金额")
    total_actual_amount: Decimal = Field(description="总实际回款金额")
    total_pending_amount: Decimal = Field(description="总待回款金额")
    total_overdue_amount: Decimal = Field(description="总逾期金额")
    completion_rate: Decimal = Field(description="回款完成率")
    
    # 按类型统计
    prepayment_planned: Decimal = Field(description="预付款计划金额")
    prepayment_actual: Decimal = Field(description="预付款实际金额")
    delivery_payment_planned: Decimal = Field(description="发货款计划金额")
    delivery_payment_actual: Decimal = Field(description="发货款实际金额")
    acceptance_payment_planned: Decimal = Field(description="验收款计划金额")
    acceptance_payment_actual: Decimal = Field(description="验收款实际金额")
    warranty_payment_planned: Decimal = Field(description="质保款计划金额")
    warranty_payment_actual: Decimal = Field(description="质保款实际金额")
    
    # 按客户统计（前10名）
    top_customers: List[dict] = Field(default_factory=list, description="回款前10名客户")


class ContractReportResponse(BaseModel):
    """合同执行报表响应"""

    report_date: str = Field(description="报表日期")
    report_type: str = Field(description="报表类型")
    
    # 合同状态统计
    draft_count: int = Field(description="草稿合同数")
    signed_count: int = Field(description="已签合同数")
    executing_count: int = Field(description="执行中合同数")
    completed_count: int = Field(description="已完成合同数")
    cancelled_count: int = Field(description="已取消合同数")
    
    # 合同金额统计
    total_contract_amount: Decimal = Field(description="合同总金额")
    signed_amount: Decimal = Field(description="已签合同金额")
    executing_amount: Decimal = Field(description="执行中合同金额")
    completed_amount: Decimal = Field(description="已完成合同金额")
    
    # 执行进度
    average_execution_rate: Decimal = Field(description="平均执行进度")
    
    # 按客户统计（前10名）
    top_customers: List[dict] = Field(default_factory=list, description="合同金额前10名客户")


class InvoiceReportResponse(BaseModel):
    """开票统计报表响应"""

    report_date: str = Field(description="报表日期")
    report_type: str = Field(description="报表类型")
    
    # 开票汇总
    total_invoices_count: int = Field(description="开票总数")
    total_invoices_amount: Decimal = Field(description="开票总金额")
    total_tax_amount: Decimal = Field(description="总税额")
    
    # 按类型统计
    special_invoice_count: int = Field(description="专票数量")
    special_invoice_amount: Decimal = Field(description="专票金额")
    normal_invoice_count: int = Field(description="普票数量")
    normal_invoice_amount: Decimal = Field(description="普票金额")
    electronic_invoice_count: int = Field(description="电子发票数量")
    electronic_invoice_amount: Decimal = Field(description="电子发票金额")
    
    # 开票及时率
    on_time_invoices_count: int = Field(description="按时开票数")
    overdue_invoices_count: int = Field(description="逾期开票数")
    timeliness_rate: Decimal = Field(description="开票及时率")
    
    # 按客户统计（前10名）
    top_customers: List[dict] = Field(default_factory=list, description="开票金额前10名客户")


# ==================== 开票申请 ====================


class InvoiceRequestCreate(BaseModel):
    """创建开票申请"""

    contract_id: int = Field(description="合同ID")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    payment_plan_id: Optional[int] = Field(default=None, description="关联回款计划ID")
    customer_id: Optional[int] = Field(default=None, description="客户ID")
    invoice_type: Optional[str] = Field(default=None, description="发票类型")
    invoice_title: Optional[str] = Field(default=None, description="发票抬头")
    tax_rate: Optional[Decimal] = Field(default=None, description="税率")
    amount: Decimal = Field(description="不含税金额")
    tax_amount: Optional[Decimal] = Field(default=None, description="税额")
    total_amount: Optional[Decimal] = Field(default=None, description="含税金额")
    currency: Optional[str] = Field(default="CNY", description="币种")
    expected_issue_date: Optional[date] = Field(default=None, description="预计开票日期")
    expected_payment_date: Optional[date] = Field(default=None, description="预计回款日期")
    reason: Optional[str] = Field(default=None, description="开票事由")
    attachments: Optional[List[str]] = Field(default=None, description="附件列表")
    remark: Optional[str] = Field(default=None, description="备注")


class InvoiceRequestUpdate(BaseModel):
    """更新开票申请"""

    project_id: Optional[int] = None
    payment_plan_id: Optional[int] = None
    invoice_type: Optional[str] = None
    invoice_title: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    expected_issue_date: Optional[date] = None
    expected_payment_date: Optional[date] = None
    reason: Optional[str] = None
    attachments: Optional[List[str]] = None
    remark: Optional[str] = None


class InvoiceRequestResponse(TimestampSchema):
    """开票申请响应"""

    id: int
    request_no: str
    contract_id: int
    contract_code: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    payment_plan_id: Optional[int] = None
    invoice_type: Optional[str] = None
    invoice_title: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    amount: Decimal
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    expected_issue_date: Optional[date] = None
    expected_payment_date: Optional[date] = None
    reason: Optional[str] = None
    attachments: Optional[List[str]] = None
    remark: Optional[str] = None
    status: str
    approval_comment: Optional[str] = None
    requested_by: int
    requested_by_name: Optional[str] = None
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    invoice_id: Optional[int] = None
    invoice_code: Optional[str] = None
    receipt_status: Optional[str] = None
    receipt_updated_at: Optional[datetime] = None


class InvoiceRequestApproveRequest(BaseModel):
    """审批开票申请"""

    approval_comment: Optional[str] = Field(default=None, description="审批意见")
    issue_date: Optional[date] = Field(default=None, description="实际开票日期")
    invoice_code: Optional[str] = Field(default=None, description="实际发票号")
    total_amount: Optional[Decimal] = Field(default=None, description="实际开票金额")


class InvoiceRequestRejectRequest(BaseModel):
    """驳回开票申请"""

    approval_comment: Optional[str] = Field(default=None, description="驳回原因")


# ==================== 客户供应商入驻 ====================


class CustomerSupplierRegistrationCreate(BaseModel):
    """创建客户供应商入驻申请"""

    customer_id: int = Field(description="客户ID")
    customer_name: Optional[str] = Field(default=None, description="客户名称")
    platform_name: str = Field(max_length=100, description="平台名称")
    platform_url: Optional[str] = Field(default=None, description="平台链接")
    application_date: Optional[date] = Field(default=None, description="申请日期")
    contact_person: Optional[str] = Field(default=None, description="联系人")
    contact_phone: Optional[str] = Field(default=None, description="联系电话")
    contact_email: Optional[str] = Field(default=None, description="联系邮箱")
    required_docs: Optional[List[str]] = Field(default=None, description="提交资料")
    remark: Optional[str] = Field(default=None, description="备注")


class CustomerSupplierRegistrationUpdate(BaseModel):
    """更新入驻记录"""

    platform_name: Optional[str] = None
    platform_url: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    application_date: Optional[date] = None
    expire_date: Optional[date] = None
    required_docs: Optional[List[str]] = None
    registration_status: Optional[str] = None
    remark: Optional[str] = None


class CustomerSupplierRegistrationResponse(TimestampSchema):
    """入驻记录响应"""

    id: int
    registration_no: str
    customer_id: int
    customer_name: Optional[str] = None
    platform_name: str
    platform_url: Optional[str] = None
    registration_status: str
    application_date: Optional[date] = None
    approved_date: Optional[date] = None
    expire_date: Optional[date] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    required_docs: Optional[List[str]] = None
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    review_comment: Optional[str] = None
    external_sync_status: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    remark: Optional[str] = None


class SupplierRegistrationReviewRequest(BaseModel):
    """入驻审核请求"""

    review_comment: Optional[str] = Field(default=None, description="审核意见")
