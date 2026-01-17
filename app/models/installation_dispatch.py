# -*- coding: utf-8 -*-
"""
安装调试派工模块 ORM 模型
包含：安装调试派工单
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin

# ==================== 枚举定义 ====================

class InstallationDispatchTaskTypeEnum(str, Enum):
    """安装调试任务类型"""
    INSTALLATION = 'INSTALLATION'  # 安装
    DEBUGGING = 'DEBUGGING'        # 调试
    TRAINING = 'TRAINING'          # 培训
    MAINTENANCE = 'MAINTENANCE'    # 维护
    REPAIR = 'REPAIR'              # 维修
    OTHER = 'OTHER'                 # 其他


class InstallationDispatchStatusEnum(str, Enum):
    """安装调试派工单状态"""
    PENDING = 'PENDING'            # 待派工
    ASSIGNED = 'ASSIGNED'          # 已派工
    IN_PROGRESS = 'IN_PROGRESS'   # 进行中
    COMPLETED = 'COMPLETED'        # 已完成
    CANCELLED = 'CANCELLED'       # 已取消


class InstallationDispatchPriorityEnum(str, Enum):
    """安装调试派工单优先级"""
    LOW = 'LOW'          # 低
    NORMAL = 'NORMAL'    # 普通
    HIGH = 'HIGH'        # 高
    URGENT = 'URGENT'    # 紧急


# ==================== 安装调试派工单 ====================

class InstallationDispatchOrder(Base, TimestampMixin):
    """安装调试派工单表"""
    __tablename__ = 'installation_dispatch_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, comment='派工单号')

    # 关联信息
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), nullable=True, comment='机台ID')
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, comment='客户ID')

    # 任务信息
    task_type = Column(String(20), nullable=False, comment='任务类型')
    task_title = Column(String(200), nullable=False, comment='任务标题')
    task_description = Column(Text, comment='任务描述')
    location = Column(String(200), comment='现场地点')

    # 计划时间
    scheduled_date = Column(Date, nullable=False, comment='计划日期')
    estimated_hours = Column(Numeric(5, 2), comment='预计工时（小时）')

    # 派工信息
    assigned_to_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='派工人员ID')
    assigned_to_name = Column(String(50), comment='派工人员姓名')
    assigned_by_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='派工人ID')
    assigned_by_name = Column(String(50), comment='派工人姓名')
    assigned_time = Column(DateTime, comment='派工时间')

    # 状态和优先级
    status = Column(String(20), default='PENDING', nullable=False, comment='状态')
    priority = Column(String(20), default='NORMAL', nullable=False, comment='优先级')

    # 进度跟踪
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    actual_hours = Column(Numeric(5, 2), comment='实际工时（小时）')
    progress = Column(Integer, default=0, comment='进度百分比（0-100）')

    # 客户联系人信息
    customer_contact = Column(String(50), comment='客户联系人')
    customer_phone = Column(String(20), comment='客户电话')
    customer_address = Column(String(500), comment='客户地址')

    # 执行情况
    execution_notes = Column(Text, comment='执行说明')
    issues_found = Column(Text, comment='发现的问题')
    solution_provided = Column(Text, comment='提供的解决方案')
    photos = Column(JSON, comment='现场照片列表')

    # 关联
    service_record_id = Column(Integer, ForeignKey('service_records.id'), nullable=True, comment='关联服务记录ID')
    acceptance_order_id = Column(Integer, ForeignKey('acceptance_orders.id'), nullable=True, comment='关联验收单ID')

    # 备注
    remark = Column(Text, comment='备注')

    # 关系
    project = relationship('Project', foreign_keys=[project_id])
    machine = relationship('Machine', foreign_keys=[machine_id])
    customer = relationship('Customer', foreign_keys=[customer_id])
    assigned_to = relationship('User', foreign_keys=[assigned_to_id])
    assigned_by = relationship('User', foreign_keys=[assigned_by_id])
    service_record = relationship('ServiceRecord', foreign_keys=[service_record_id])
    acceptance_order = relationship('AcceptanceOrder', foreign_keys=[acceptance_order_id])

    __table_args__ = (
        Index('idx_install_dispatch_project', 'project_id'),
        Index('idx_install_dispatch_machine', 'machine_id'),
        Index('idx_install_dispatch_customer', 'customer_id'),
        Index('idx_install_dispatch_status', 'status'),
        Index('idx_install_dispatch_assigned', 'assigned_to_id'),
        Index('idx_install_dispatch_date', 'scheduled_date'),
        {'comment': '安装调试派工单表'},
    )

    def __repr__(self):
        return f'<InstallationDispatchOrder {self.order_no}>'
