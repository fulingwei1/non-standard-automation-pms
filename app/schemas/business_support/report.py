# -*- coding: utf-8 -*-
"""
销售报表 Schema
"""

from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


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
