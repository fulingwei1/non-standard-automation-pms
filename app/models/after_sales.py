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
