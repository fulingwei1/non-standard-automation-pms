# -*- coding: utf-8 -*-
"""
售后服务模型

包括：客户反馈、维修保养、技术支持工单
"""

from datetime import date, datetime
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class AfterSalesFeedback(Base, TimestampMixin):
    """客户反馈表"""
    
    __tablename__ = "after_sales_feedback"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键 ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="关联项目 ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), comment="客户 ID")
    
    # 反馈信息
    feedback_type = Column(String(30), comment="反馈类型：COMPLAINT/SUGGESTION/PRAISE")
    feedback_content = Column(Text, comment="反馈内容")
    priority = Column(String(20), default="MEDIUM", comment="优先级：LOW/MEDIUM/HIGH/URGENT")
    
    # 处理状态
    status = Column(String(20), default="PENDING", comment="状态：PENDING/PROCESSING/RESOLVED/CLOSED")
    assigned_to = Column(Integer, ForeignKey("users.id"), comment="处理人 ID")
    resolved_at = Column(DateTime, comment="解决时间")
    resolution = Column(Text, comment="解决方案")
    
    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    
    __table_args__ = (
        Index("idx_asf_project", "project_id"),
        Index("idx_asf_customer", "customer_id"),
        Index("idx_asf_status", "status"),
    )


class AfterSalesMaintenance(Base, TimestampMixin):
    """维修保养记录表"""
    
    __tablename__ = "after_sales_maintenance"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键 ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="关联项目 ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), comment="客户 ID")
    
    # 保养信息
    maintenance_type = Column(String(30), comment="保养类型：REGULAR/REPAIR/UPGRADE")
    maintenance_content = Column(Text, comment="保养内容")
    scheduled_date = Column(Date, comment="计划日期")
    completed_date = Column(Date, comment="完成日期")
    
    # 状态
    status = Column(String(20), default="SCHEDULED", comment="状态：SCHEDULED/IN_PROGRESS/COMPLETED")
    technician_id = Column(Integer, ForeignKey("users.id"), comment="技术员 ID")
    notes = Column(Text, comment="备注")
    
    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    technician = relationship("User", foreign_keys=[technician_id])
    
    __table_args__ = (
        Index("idx_asm_project", "project_id"),
        Index("idx_asm_scheduled", "scheduled_date"),
        Index("idx_asm_status", "status"),
    )


class AfterSalesSupportTicket(Base, TimestampMixin):
    """技术支持工单表"""
    
    __tablename__ = "after_sales_support_tickets"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键 ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="关联项目 ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), comment="客户 ID")
    
    # 工单信息
    ticket_no = Column(String(50), unique=True, comment="工单编号")
    subject = Column(String(200), comment="主题")
    description = Column(Text, comment="问题描述")
    
    # 分类
    category = Column(String(30), comment="分类：TECHNICAL/TRAINING/DOCUMENTATION/OTHER")
    priority = Column(String(20), default="MEDIUM", comment="优先级：LOW/MEDIUM/HIGH/URGENT")
    
    # 处理状态
    status = Column(String(20), default="OPEN", comment="状态：OPEN/IN_PROGRESS/WAITING_CUSTOMER/RESOLVED/CLOSED")
    assigned_to = Column(Integer, ForeignKey("users.id"), comment="处理人 ID")
    resolved_at = Column(DateTime, comment="解决时间")
    resolution = Column(Text, comment="解决方案")
    
    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    
    __table_args__ = (
        Index("idx_asst_project", "project_id"),
        Index("idx_asst_ticket_no", "ticket_no"),
        Index("idx_asst_status", "status"),
    )


class AfterSalesWarranty(Base, TimestampMixin):
    """质保管理表"""
    
    __tablename__ = "after_sales_warranty"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目 ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), comment="客户 ID")
    
    # 质保信息
    warranty_no = Column(String(50), unique=True, comment="质保编号")
    warranty_type = Column(String(30), comment="质保类型：STANDARD/EXTENDED/VIP")
    warranty_start = Column(Date, comment="质保开始日期")
    warranty_end = Column(Date, comment="质保结束日期")
    warranty_months = Column(Integer, default=12, comment="质保月数")
    
    # 质保范围
    scope = Column(Text, comment="质保范围说明")
    exclusions = Column(Text, comment="质保排除项")
    
    # 状态
    status = Column(String(20), default="ACTIVE", comment="状态：ACTIVE/EXPIRED/CANCELLED")
    
    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    
    __table_args__ = (
        Index("idx_asw_project", "project_id"),
        Index("idx_asw_status", "status"),
        Index("idx_asw_end", "warranty_end"),
    )


class AfterSalesSparePart(Base, TimestampMixin):
    """备件管理表"""
    
    __tablename__ = "after_sales_spare_parts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目 ID")
    
    # 备件信息
    part_no = Column(String(50), comment="备件编号")
    part_name = Column(String(200), comment="备件名称")
    part_spec = Column(String(500), comment="规格型号")
    quantity = Column(Integer, default=0, comment="库存数量")
    min_stock = Column(Integer, default=1, comment="最低库存")
    unit_price = Column(String(20), comment="单价")
    
    # 供应商
    supplier = Column(String(200), comment="供应商")
    lead_time_days = Column(Integer, comment="采购周期(天)")
    
    # 状态
    status = Column(String(20), default="IN_STOCK", comment="状态：IN_STOCK/LOW_STOCK/OUT_OF_STOCK")
    
    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    
    __table_args__ = (
        Index("idx_assp_project", "project_id"),
        Index("idx_assp_status", "status"),
    )


class AfterSalesFieldService(Base, TimestampMixin):
    """现场服务记录表"""
    
    __tablename__ = "after_sales_field_services"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目 ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), comment="客户 ID")
    ticket_id = Column(Integer, ForeignKey("after_sales_support_tickets.id"), comment="关联工单 ID")
    
    # 服务信息
    service_no = Column(String(50), unique=True, comment="服务编号")
    service_type = Column(String(30), comment="服务类型：INSTALLATION/REPAIR/UPGRADE/TRAINING")
    service_content = Column(Text, comment="服务内容")
    
    # 时间
    planned_date = Column(Date, comment="计划日期")
    actual_date = Column(Date, comment="实际日期")
    service_hours = Column(Integer, comment="服务工时(小时)")
    travel_hours = Column(Integer, comment="差旅工时(小时)")
    
    # 人员
    engineer_id = Column(Integer, ForeignKey("users.id"), comment="服务工程师 ID")
    engineer_name = Column(String(100), comment="工程师姓名")
    
    # 费用
    travel_cost = Column(String(20), comment="差旅费用")
    parts_cost = Column(String(20), comment="备件费用")
    total_cost = Column(String(20), comment="总费用")
    is_warranty = Column(Boolean, default=True, comment="是否质保内")
    
    # 服务报告
    report_content = Column(Text, comment="服务报告")
    customer_sign = Column(Boolean, default=False, comment="客户是否签字确认")
    
    # 状态
    status = Column(String(20), default="PLANNED", comment="状态：PLANNED/IN_PROGRESS/COMPLETED/CANCELLED")
    
    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    engineer = relationship("User", foreign_keys=[engineer_id])
    
    __table_args__ = (
        Index("idx_asfs_project", "project_id"),
        Index("idx_asfs_status", "status"),
        Index("idx_asfs_engineer", "engineer_id"),
    )


class AfterSalesSLA(Base, TimestampMixin):
    """SLA 管理表"""
    
    __tablename__ = "after_sales_sla"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目 ID")
    ticket_id = Column(Integer, ForeignKey("after_sales_support_tickets.id"), comment="工单 ID")
    
    # SLA 指标
    response_target_hours = Column(Integer, default=4, comment="响应目标(小时)")
    resolve_target_hours = Column(Integer, default=24, comment="解决目标(小时)")
    actual_response_hours = Column(Integer, comment="实际响应(小时)")
    actual_resolve_hours = Column(Integer, comment="实际解决(小时)")
    
    # 达标
    response_met = Column(Boolean, comment="响应是否达标")
    resolve_met = Column(Boolean, comment="解决是否达标")
    
    project = relationship("Project", foreign_keys=[project_id])
    
    __table_args__ = (Index("idx_sla_project", "project_id"), Index("idx_sla_ticket", "ticket_id"),)


class AfterSalesSatisfaction(Base, TimestampMixin):
    """客户满意度表"""
    
    __tablename__ = "after_sales_satisfaction"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目 ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), comment="客户 ID")
    ticket_id = Column(Integer, ForeignKey("after_sales_support_tickets.id"), nullable=True, comment="工单 ID")
    field_service_id = Column(Integer, ForeignKey("after_sales_field_services.id"), nullable=True, comment="现场服务 ID")
    
    # 满意度评分
    overall_score = Column(Integer, comment="总体满意度 1-10")
    response_score = Column(Integer, comment="响应速度 1-10")
    quality_score = Column(Integer, comment="服务质量 1-10")
    attitude_score = Column(Integer, comment="服务态度 1-10")
    nps_score = Column(Integer, comment="NPS 评分 0-10")
    
    # 反馈
    comments = Column(Text, comment="客户评价")
    
    project = relationship("Project", foreign_keys=[project_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    
    __table_args__ = (Index("idx_sat_project", "project_id"),)


class AfterSalesKnowledge(Base, TimestampMixin):
    """售后知识库表"""
    
    __tablename__ = "after_sales_knowledge"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 知识信息
    title = Column(String(200), comment="标题")
    category = Column(String(30), comment="分类：FAQ/SOLUTION/GUIDE/TROUBLESHOOT")
    content = Column(Text, comment="内容")
    keywords = Column(String(500), comment="关键词(逗号分隔)")
    
    # 关联
    project_type = Column(String(50), comment="项目类型：ICT/FCT/EOL")
    product_category = Column(String(100), comment="产品类别")
    
    # 统计
    view_count = Column(Integer, default=0, comment="浏览次数")
    helpful_count = Column(Integer, default=0, comment="有用次数")
    
    # 状态
    status = Column(String(20), default="PUBLISHED", comment="状态：DRAFT/PUBLISHED/ARCHIVED")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")
    
    __table_args__ = (Index("idx_ask_category", "category"), Index("idx_ask_status", "status"),)
