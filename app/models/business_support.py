# -*- coding: utf-8 -*-
"""
商务支持模块 ORM 模型
包含：投标管理、合同审核、回款跟踪、文件归档
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime,
    Numeric, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class BiddingProject(Base, TimestampMixin):
    """投标项目表"""

    __tablename__ = "bidding_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bidding_no = Column(String(50), unique=True, nullable=False, comment="投标编号")
    project_name = Column(String(500), nullable=False, comment="项目名称")
    customer_id = Column(Integer, ForeignKey("customers.id"), comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")

    # 招标信息
    tender_no = Column(String(100), comment="招标编号")
    tender_type = Column(String(20), comment="招标类型：public/invited/competitive/single_source/online")
    tender_platform = Column(String(200), comment="招标平台")
    tender_url = Column(String(500), comment="招标链接")

    # 时间节点
    publish_date = Column(Date, comment="发布日期")
    deadline_date = Column(DateTime, comment="投标截止时间")
    bid_opening_date = Column(DateTime, comment="开标时间")

    # 标书信息
    bid_bond = Column(Numeric(15, 2), comment="投标保证金")
    bid_bond_status = Column(String(20), default="not_required", comment="保证金状态：not_required/pending/paid/returned")
    estimated_amount = Column(Numeric(15, 2), comment="预估金额")

    # 投标准备
    bid_document_status = Column(String(20), default="not_started", comment="标书状态：not_started/in_progress/completed/submitted")
    technical_doc_ready = Column(Boolean, default=False, comment="技术文件就绪")
    commercial_doc_ready = Column(Boolean, default=False, comment="商务文件就绪")
    qualification_doc_ready = Column(Boolean, default=False, comment="资质文件就绪")

    # 投标方式
    submission_method = Column(String(20), comment="投递方式：offline/online/both")
    submission_address = Column(String(500), comment="投递地址")

    # 负责人
    sales_person_id = Column(Integer, ForeignKey("users.id"), comment="业务员ID")
    sales_person_name = Column(String(50), comment="业务员")
    support_person_id = Column(Integer, ForeignKey("users.id"), comment="商务支持ID")
    support_person_name = Column(String(50), comment="商务支持")

    # 投标结果
    bid_result = Column(String(20), default="pending", comment="投标结果：pending/won/lost/cancelled/invalid")
    bid_price = Column(Numeric(15, 2), comment="投标价格")
    win_price = Column(Numeric(15, 2), comment="中标价格")
    result_date = Column(Date, comment="结果公布日期")
    result_remark = Column(Text, comment="结果说明")

    status = Column(String(20), default="draft", comment="状态：draft/preparing/submitted/closed")
    remark = Column(Text, comment="备注")

    # 关系
    customer = relationship("Customer", foreign_keys=[customer_id])
    sales_person = relationship("User", foreign_keys=[sales_person_id])
    support_person = relationship("User", foreign_keys=[support_person_id])
    documents = relationship("BiddingDocument", back_populates="bidding_project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_bidding_no", "bidding_no"),
        Index("idx_customer", "customer_id"),
        Index("idx_deadline", "deadline_date"),
        Index("idx_result", "bid_result"),
    )

    def __repr__(self):
        return f"<BiddingProject {self.bidding_no}>"


class BiddingDocument(Base, TimestampMixin):
    """投标文件表"""

    __tablename__ = "bidding_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bidding_project_id = Column(Integer, ForeignKey("bidding_projects.id"), nullable=False, comment="投标项目ID")
    document_type = Column(String(50), comment="文件类型：technical/commercial/qualification/other")
    document_name = Column(String(200), comment="文件名称")
    file_path = Column(String(500), comment="文件路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    version = Column(String(20), comment="版本号")
    status = Column(String(20), default="draft", comment="状态：draft/reviewed/approved")
    reviewed_by = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    reviewed_at = Column(DateTime, comment="审核时间")
    remark = Column(Text, comment="备注")

    # 关系
    bidding_project = relationship("BiddingProject", back_populates="documents")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        Index("idx_bidding_project", "bidding_project_id"),
        Index("idx_document_type", "document_type"),
    )

    def __repr__(self):
        return f"<BiddingDocument {self.document_name}>"


class ContractReview(Base, TimestampMixin):
    """合同审核记录表"""

    __tablename__ = "contract_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    review_type = Column(String(20), comment="审核类型：business/legal/finance")
    review_status = Column(String(20), default="pending", comment="审核状态：pending/passed/rejected")
    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    review_comment = Column(Text, comment="审核意见")
    reviewed_at = Column(DateTime, comment="审核时间")
    risk_items = Column(JSON, comment="风险项列表")

    # 关系
    contract = relationship("Contract", foreign_keys=[contract_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    __table_args__ = (
        Index("idx_contract", "contract_id"),
        Index("idx_review_status", "review_status"),
    )

    def __repr__(self):
        return f"<ContractReview {self.id}>"


class ContractSealRecord(Base, TimestampMixin):
    """合同盖章邮寄记录表"""

    __tablename__ = "contract_seal_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    seal_status = Column(String(20), default="pending", comment="盖章状态：pending/sealed/sent/received/archived")
    seal_date = Column(Date, comment="盖章日期")
    seal_operator_id = Column(Integer, ForeignKey("users.id"), comment="盖章操作人ID")
    send_date = Column(Date, comment="邮寄日期")
    tracking_no = Column(String(50), comment="快递单号")
    courier_company = Column(String(50), comment="快递公司")
    receive_date = Column(Date, comment="回收日期")
    archive_date = Column(Date, comment="归档日期")
    archive_location = Column(String(200), comment="归档位置")
    remark = Column(Text, comment="备注")

    # 关系
    contract = relationship("Contract", foreign_keys=[contract_id])
    seal_operator = relationship("User", foreign_keys=[seal_operator_id])

    __table_args__ = (
        Index("idx_contract", "contract_id"),
        Index("idx_seal_status", "seal_status"),
    )

    def __repr__(self):
        return f"<ContractSealRecord {self.id}>"


class PaymentReminder(Base, TimestampMixin):
    """回款催收记录表"""

    __tablename__ = "payment_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    payment_node = Column(String(50), comment="付款节点：prepayment/delivery/acceptance/warranty")
    payment_amount = Column(Numeric(15, 2), comment="应回款金额")
    plan_date = Column(Date, comment="计划回款日期")
    reminder_type = Column(String(20), comment="催收类型：call/email/visit/other")
    reminder_content = Column(Text, comment="催收内容")
    reminder_date = Column(Date, comment="催收日期")
    reminder_person_id = Column(Integer, ForeignKey("users.id"), comment="催收人ID")
    customer_response = Column(Text, comment="客户反馈")
    next_reminder_date = Column(Date, comment="下次催收日期")
    status = Column(String(20), default="pending", comment="状态：pending/completed/cancelled")
    remark = Column(Text, comment="备注")

    # 关系
    contract = relationship("Contract", foreign_keys=[contract_id])
    project = relationship("Project", foreign_keys=[project_id])
    reminder_person = relationship("User", foreign_keys=[reminder_person_id])

    __table_args__ = (
        Index("idx_contract", "contract_id"),
        Index("idx_project", "project_id"),
        Index("idx_reminder_date", "reminder_date"),
    )

    def __repr__(self):
        return f"<PaymentReminder {self.id}>"


class DocumentArchive(Base, TimestampMixin):
    """文件归档表"""

    __tablename__ = "document_archives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    archive_no = Column(String(50), unique=True, nullable=False, comment="归档编号")
    document_type = Column(String(50), comment="文件类型：contract/acceptance/invoice/other")
    related_type = Column(String(50), comment="关联类型：contract/project/acceptance")
    related_id = Column(Integer, comment="关联ID")
    document_name = Column(String(200), comment="文件名称")
    file_path = Column(String(500), comment="文件路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    archive_location = Column(String(200), comment="归档位置")
    archive_date = Column(Date, comment="归档日期")
    archiver_id = Column(Integer, ForeignKey("users.id"), comment="归档人ID")
    status = Column(String(20), default="archived", comment="状态：archived/borrowed/returned")
    remark = Column(Text, comment="备注")

    # 关系
    archiver = relationship("User", foreign_keys=[archiver_id])

    __table_args__ = (
        Index("idx_archive_no", "archive_no"),
        Index("idx_document_type", "document_type"),
        Index("idx_related", "related_type", "related_id"),
    )

    def __repr__(self):
        return f"<DocumentArchive {self.archive_no}>"


class SalesOrder(Base, TimestampMixin):
    """销售订单表"""

    __tablename__ = "sales_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, comment="订单编号")
    
    # 关联
    contract_id = Column(Integer, ForeignKey("contracts.id"), comment="合同ID")
    contract_no = Column(String(50), comment="合同编号")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    project_no = Column(String(50), comment="项目号")
    
    # 订单信息
    order_type = Column(String(20), default="standard", comment="订单类型：standard/sample/repair/other")
    order_amount = Column(Numeric(15, 2), comment="订单金额")
    currency = Column(String(10), default="CNY", comment="币种")
    
    # 交期
    required_date = Column(Date, comment="客户要求日期")
    promised_date = Column(Date, comment="承诺交期")
    
    # 状态
    order_status = Column(String(20), default="draft", comment="订单状态：draft/confirmed/in_production/ready/partial_shipped/shipped/completed/cancelled")
    
    # 项目号分配
    project_no_assigned = Column(Boolean, default=False, comment="是否已分配项目号")
    project_no_assigned_date = Column(DateTime, comment="项目号分配时间")
    project_notice_sent = Column(Boolean, default=False, comment="是否已发项目通知单")
    project_notice_date = Column(DateTime, comment="通知单发布时间")
    
    # ERP信息
    erp_order_no = Column(String(50), comment="ERP订单号")
    erp_sync_status = Column(String(20), default="pending", comment="ERP同步状态：pending/synced/failed")
    erp_sync_time = Column(DateTime, comment="ERP同步时间")
    
    # 负责人
    sales_person_id = Column(Integer, ForeignKey("users.id"), comment="业务员ID")
    sales_person_name = Column(String(50), comment="业务员")
    support_person_id = Column(Integer, ForeignKey("users.id"), comment="商务支持ID")
    
    remark = Column(Text, comment="备注")
    
    # 关系
    contract = relationship("Contract", foreign_keys=[contract_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    project = relationship("Project", foreign_keys=[project_id])
    sales_person = relationship("User", foreign_keys=[sales_person_id])
    support_person = relationship("User", foreign_keys=[support_person_id])
    delivery_orders = relationship("DeliveryOrder", back_populates="sales_order", cascade="all, delete-orphan")
    order_items = relationship("SalesOrderItem", back_populates="sales_order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_order_no", "order_no"),
        Index("idx_contract", "contract_id"),
        Index("idx_customer", "customer_id"),
        Index("idx_project", "project_id"),
        Index("idx_status", "order_status"),
    )

    def __repr__(self):
        return f"<SalesOrder {self.order_no}>"


class SalesOrderItem(Base, TimestampMixin):
    """销售订单明细表"""

    __tablename__ = "sales_order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False, comment="销售订单ID")
    item_name = Column(String(200), comment="明细名称")
    item_spec = Column(String(200), comment="规格型号")
    qty = Column(Numeric(10, 2), comment="数量")
    unit = Column(String(20), comment="单位")
    unit_price = Column(Numeric(12, 2), comment="单价")
    amount = Column(Numeric(12, 2), comment="金额")
    remark = Column(Text, comment="备注")

    # 关系
    sales_order = relationship("SalesOrder", back_populates="order_items")

    __table_args__ = (
        Index("idx_sales_order", "sales_order_id"),
    )

    def __repr__(self):
        return f"<SalesOrderItem {self.id}>"


class DeliveryOrder(Base, TimestampMixin):
    """发货单表"""

    __tablename__ = "delivery_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_no = Column(String(50), unique=True, nullable=False, comment="送货单号")
    
    # 关联
    order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False, comment="销售订单ID")
    order_no = Column(String(50), comment="销售订单号")
    contract_id = Column(Integer, ForeignKey("contracts.id"), comment="合同ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    
    # 发货信息
    delivery_date = Column(Date, comment="发货日期")
    delivery_type = Column(String(20), comment="发货方式：express/logistics/self_pickup/install")
    logistics_company = Column(String(100), comment="物流公司")
    tracking_no = Column(String(100), comment="物流单号")
    
    # 收货信息
    receiver_name = Column(String(50), comment="收货人")
    receiver_phone = Column(String(20), comment="收货电话")
    receiver_address = Column(String(500), comment="收货地址")
    
    # 金额
    delivery_amount = Column(Numeric(15, 2), comment="本次发货金额")
    
    # 审批
    approval_status = Column(String(20), default="pending", comment="审批状态：pending/approved/rejected")
    approval_comment = Column(Text, comment="审批意见")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approved_at = Column(DateTime, comment="审批时间")
    
    # 特殊审批（应收未收情况）
    special_approval = Column(Boolean, default=False, comment="是否特殊审批")
    special_approver_id = Column(Integer, ForeignKey("users.id"), comment="特殊审批人ID")
    special_approval_reason = Column(Text, comment="特殊审批原因")
    
    # 送货单状态
    delivery_status = Column(String(20), default="draft", comment="送货单状态：draft/approved/printed/shipped/received/returned")
    print_date = Column(DateTime, comment="打印时间")
    ship_date = Column(DateTime, comment="实际发货时间")
    receive_date = Column(Date, comment="客户签收日期")
    
    # 送货单回收
    return_status = Column(String(20), default="pending", comment="送货单回收状态：pending/received/lost")
    return_date = Column(Date, comment="回收日期")
    signed_delivery_file_id = Column(Integer, comment="签收送货单文件ID")
    
    remark = Column(Text, comment="备注")
    
    # 关系
    sales_order = relationship("SalesOrder", back_populates="delivery_orders")
    contract = relationship("Contract", foreign_keys=[contract_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    project = relationship("Project", foreign_keys=[project_id])
    approver = relationship("User", foreign_keys=[approved_by])
    special_approver = relationship("User", foreign_keys=[special_approver_id])

    __table_args__ = (
        Index("idx_delivery_no", "delivery_no"),
        Index("idx_order", "order_id"),
        Index("idx_customer", "customer_id"),
        Index("idx_status", "delivery_status"),
        Index("idx_return_status", "return_status"),
    )

    def __repr__(self):
        return f"<DeliveryOrder {self.delivery_no}>"


class AcceptanceTracking(Base, TimestampMixin):
    """验收单跟踪记录表（商务支持角度）"""

    __tablename__ = "acceptance_tracking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    acceptance_order_id = Column(Integer, ForeignKey("acceptance_orders.id"), nullable=False, comment="验收单ID")
    acceptance_order_no = Column(String(50), comment="验收单号")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    project_code = Column(String(50), comment="项目编号")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")
    
    # 验收条件检查
    condition_check_status = Column(String(20), default="pending", comment="验收条件检查状态：pending/checking/met/not_met")
    condition_check_result = Column(Text, comment="验收条件检查结果")
    condition_check_date = Column(DateTime, comment="验收条件检查日期")
    condition_checker_id = Column(Integer, ForeignKey("users.id"), comment="检查人ID")
    
    # 验收单跟踪
    tracking_status = Column(String(20), default="pending", comment="跟踪状态：pending/reminded/received")
    reminder_count = Column(Integer, default=0, comment="催签次数")
    last_reminder_date = Column(DateTime, comment="最后催签日期")
    last_reminder_by = Column(Integer, ForeignKey("users.id"), comment="最后催签人ID")
    received_date = Column(Date, comment="收到原件日期")
    signed_file_id = Column(Integer, comment="签收验收单文件ID")
    
    # 验收报告跟踪
    report_status = Column(String(20), default="pending", comment="报告状态：pending/generated/signed/archived")
    report_generated_date = Column(DateTime, comment="报告生成日期")
    report_signed_date = Column(DateTime, comment="报告签署日期")
    report_archived_date = Column(DateTime, comment="报告归档日期")
    
    # 质保期跟踪
    warranty_start_date = Column(Date, comment="质保开始日期")
    warranty_end_date = Column(Date, comment="质保结束日期")
    warranty_status = Column(String(20), default="not_started", comment="质保状态：not_started/active/expiring/expired")
    warranty_expiry_reminded = Column(Boolean, default=False, comment="是否已提醒质保到期")
    
    # 关联合同
    contract_id = Column(Integer, ForeignKey("contracts.id"), comment="合同ID")
    contract_no = Column(String(50), comment="合同编号")
    
    # 负责人
    sales_person_id = Column(Integer, ForeignKey("users.id"), comment="业务员ID")
    sales_person_name = Column(String(50), comment="业务员")
    support_person_id = Column(Integer, ForeignKey("users.id"), comment="商务支持ID")
    
    remark = Column(Text, comment="备注")
    
    # 关系
    acceptance_order = relationship("AcceptanceOrder", foreign_keys=[acceptance_order_id])
    project = relationship("Project", foreign_keys=[project_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    contract = relationship("Contract", foreign_keys=[contract_id])
    condition_checker = relationship("User", foreign_keys=[condition_checker_id])
    last_reminder_by_user = relationship("User", foreign_keys=[last_reminder_by])
    sales_person = relationship("User", foreign_keys=[sales_person_id])
    support_person = relationship("User", foreign_keys=[support_person_id])
    tracking_records = relationship("AcceptanceTrackingRecord", back_populates="tracking", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_acceptance_order", "acceptance_order_id"),
        Index("idx_project_tracking", "project_id"),
        Index("idx_customer_tracking", "customer_id"),
        Index("idx_tracking_status", "tracking_status"),
        Index("idx_condition_status", "condition_check_status"),
    )

    def __repr__(self):
        return f"<AcceptanceTracking {self.acceptance_order_no}>"


class AcceptanceTrackingRecord(Base, TimestampMixin):
    """验收单跟踪记录明细表（记录每次催签等操作）"""

    __tablename__ = "acceptance_tracking_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tracking_id = Column(Integer, ForeignKey("acceptance_tracking.id"), nullable=False, comment="跟踪记录ID")
    record_type = Column(String(20), nullable=False, comment="记录类型：reminder/condition_check/report_track/warranty_reminder")
    record_content = Column(Text, comment="记录内容")
    record_date = Column(DateTime, nullable=False, comment="记录日期")
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="操作人ID")
    operator_name = Column(String(50), comment="操作人")
    result = Column(String(20), comment="操作结果：success/failed/pending")
    remark = Column(Text, comment="备注")
    
    # 关系
    tracking = relationship("AcceptanceTracking", back_populates="tracking_records")
    operator = relationship("User", foreign_keys=[operator_id])

    __table_args__ = (
        Index("idx_tracking_record", "tracking_id"),
        Index("idx_record_type", "record_type"),
        Index("idx_record_date", "record_date"),
    )

    def __repr__(self):
        return f"<AcceptanceTrackingRecord {self.id}>"


class Reconciliation(Base, TimestampMixin):
    """客户对账单表"""

    __tablename__ = "reconciliations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reconciliation_no = Column(String(50), unique=True, nullable=False, comment="对账单号")
    
    # 客户
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")
    
    # 对账期间
    period_start = Column(Date, comment="对账开始日期")
    period_end = Column(Date, comment="对账结束日期")
    
    # 金额汇总
    opening_balance = Column(Numeric(15, 2), default=0, comment="期初余额")
    period_sales = Column(Numeric(15, 2), default=0, comment="本期销售")
    period_receipt = Column(Numeric(15, 2), default=0, comment="本期回款")
    closing_balance = Column(Numeric(15, 2), default=0, comment="期末余额")
    
    # 状态
    status = Column(String(20), default="draft", comment="状态：draft/sent/confirmed/disputed")
    sent_date = Column(Date, comment="发送日期")
    confirm_date = Column(Date, comment="确认日期")
    
    # 客户确认
    customer_confirmed = Column(Boolean, default=False, comment="客户是否确认")
    customer_confirm_date = Column(Date, comment="客户确认日期")
    customer_difference = Column(Numeric(15, 2), comment="客户差异金额")
    difference_reason = Column(Text, comment="差异原因")
    
    # 文件
    reconciliation_file_id = Column(Integer, comment="对账单文件ID")
    confirmed_file_id = Column(Integer, comment="确认回执文件ID")
    
    remark = Column(Text, comment="备注")
    
    # 关系
    customer = relationship("Customer", foreign_keys=[customer_id])

    __table_args__ = (
        Index("idx_reconciliation_no", "reconciliation_no"),
        Index("idx_customer_reconciliation", "customer_id"),
        Index("idx_period", "period_start", "period_end"),
        Index("idx_status", "status"),
    )

    def __repr__(self):
        return f"<Reconciliation {self.reconciliation_no}>"


class InvoiceRequest(Base, TimestampMixin):
    """开票申请表"""

    __tablename__ = "invoice_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_no = Column(String(50), unique=True, nullable=False, comment="申请编号")

    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    project_name = Column(String(200), comment="项目名称")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")

    payment_plan_id = Column(Integer, ForeignKey("project_payment_plans.id"), comment="关联回款计划ID")

    invoice_type = Column(String(20), comment="发票类型")
    invoice_title = Column(String(200), comment="发票抬头")
    tax_rate = Column(Numeric(5, 2), comment="税率(%)")
    amount = Column(Numeric(14, 2), nullable=False, comment="不含税金额")
    tax_amount = Column(Numeric(14, 2), comment="税额")
    total_amount = Column(Numeric(14, 2), comment="含税金额")
    currency = Column(String(10), default="CNY", comment="币种")
    expected_issue_date = Column(Date, comment="预计开票日期")
    expected_payment_date = Column(Date, comment="预计回款日期")

    reason = Column(Text, comment="开票事由")
    attachments = Column(Text, comment="附件列表JSON")
    remark = Column(Text, comment="备注")

    status = Column(String(20), default="PENDING", comment="状态：DRAFT/PENDING/APPROVED/REJECTED/CANCELLED")
    approval_comment = Column(Text, comment="审批意见")
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="申请人ID")
    requested_by_name = Column(String(50), comment="申请人姓名")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approved_at = Column(DateTime, comment="审批时间")

    invoice_id = Column(Integer, ForeignKey("invoices.id"), comment="生成的发票ID")
    receipt_status = Column(String(20), default="UNPAID", comment="回款状态：UNPAID/PARTIAL/PAID")
    receipt_updated_at = Column(DateTime, comment="回款状态更新时间")

    # 关系
    contract = relationship("Contract", foreign_keys=[contract_id])
    project = relationship("Project", foreign_keys=[project_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    payment_plan = relationship("ProjectPaymentPlan", back_populates="invoice_requests")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    invoice = relationship("Invoice", foreign_keys=[invoice_id])

    __table_args__ = (
        Index("idx_invoice_request_no", "request_no"),
        Index("idx_invoice_request_contract", "contract_id"),
        Index("idx_invoice_request_project", "project_id"),
        Index("idx_invoice_request_customer", "customer_id"),
        Index("idx_invoice_request_status", "status"),
        Index("idx_invoice_request_plan", "payment_plan_id"),
    )

    def __repr__(self):
        return f"<InvoiceRequest {self.request_no}>"


class CustomerSupplierRegistration(Base, TimestampMixin):
    """客户供应商入驻管理表"""

    __tablename__ = "customer_supplier_registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    registration_no = Column(String(100), unique=True, nullable=False, comment="入驻编号")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")
    platform_name = Column(String(100), nullable=False, comment="平台名称")
    platform_url = Column(String(500), comment="平台链接")

    registration_status = Column(String(20), default="PENDING", comment="状态：PENDING/SUBMITTED/APPROVED/REJECTED/ACTIVE")
    application_date = Column(Date, comment="申请日期")
    approved_date = Column(Date, comment="批准日期")
    expire_date = Column(Date, comment="有效期")

    contact_person = Column(String(50), comment="联系人")
    contact_phone = Column(String(30), comment="联系电话")
    contact_email = Column(String(100), comment="联系邮箱")

    required_docs = Column(Text, comment="提交资料JSON")
    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    review_comment = Column(Text, comment="审核意见")

    external_sync_status = Column(String(20), default="pending", comment="外部平台同步状态")
    last_sync_at = Column(DateTime, comment="最后同步时间")
    sync_message = Column(Text, comment="同步结果消息")

    remark = Column(Text, comment="备注")

    customer = relationship("Customer", foreign_keys=[customer_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    __table_args__ = (
        Index("idx_supplier_reg_customer", "customer_id"),
        Index("idx_supplier_reg_platform", "platform_name"),
        Index("idx_supplier_reg_status", "registration_status"),
    )

    def __repr__(self):
        return f"<CustomerSupplierRegistration {self.registration_no}>"
