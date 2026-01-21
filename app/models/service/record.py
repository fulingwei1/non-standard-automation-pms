# -*- coding: utf-8 -*-
"""
服务模型 - 服务记录
"""
from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class ServiceRecord(Base, TimestampMixin):
    """现场服务记录表"""
    __tablename__ = 'service_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_no = Column(String(50), unique=True, nullable=False, comment='记录号')

    # 服务类型
    service_type = Column(String(20), nullable=False, comment='服务类型')

    # 关联信息
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    machine_no = Column(String(50), comment='机台号')
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, comment='客户ID')

    # 服务地点和时间
    location = Column(String(200), comment='服务地点')
    service_date = Column(Date, nullable=False, comment='服务日期')
    start_time = Column(String(10), comment='开始时间')
    end_time = Column(String(10), comment='结束时间')
    duration_hours = Column(Numeric(5, 2), comment='服务时长（小时）')

    # 服务人员
    service_engineer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='服务工程师ID')
    service_engineer_name = Column(String(50), comment='服务工程师姓名')

    # 客户联系人
    customer_contact = Column(String(50), comment='客户联系人')
    customer_phone = Column(String(20), comment='客户电话')

    # 服务内容
    service_content = Column(Text, nullable=False, comment='服务内容')
    service_result = Column(Text, comment='服务结果')
    issues_found = Column(Text, comment='发现的问题')
    solution_provided = Column(Text, comment='提供的解决方案')

    # 照片
    photos = Column(JSON, comment='照片列表')

    # 客户满意度
    customer_satisfaction = Column(Integer, comment='客户满意度1-5')
    customer_feedback = Column(Text, comment='客户反馈')
    customer_signed = Column(Boolean, default=False, comment='客户是否签字')

    # 状态
    status = Column(String(20), default='SCHEDULED', nullable=False, comment='状态')

    # 关系
    project = relationship('Project', foreign_keys=[project_id])
    customer = relationship('Customer', foreign_keys=[customer_id])
    service_engineer = relationship('User', foreign_keys=[service_engineer_id])

    __table_args__ = (
        Index('idx_service_record_project', 'project_id'),
        Index('idx_service_record_customer', 'customer_id'),
        Index('idx_service_record_date', 'service_date'),
        {'comment': '现场服务记录表'},
    )

    def __repr__(self):
        return f'<ServiceRecord {self.record_no}>'
