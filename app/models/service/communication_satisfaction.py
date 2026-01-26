# -*- coding: utf-8 -*-
"""
服务模型 - 客户沟通和满意度
"""
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class CustomerCommunication(Base, TimestampMixin):
    """客户沟通记录表"""
    __tablename__ = 'customer_communications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    communication_no = Column(String(50), unique=True, nullable=False, comment='沟通记录号')

    # 沟通方式
    communication_type = Column(String(20), nullable=False, comment='沟通方式')

    # 客户信息
    customer_name = Column(String(100), nullable=False, comment='客户名称')
    customer_contact = Column(String(50), comment='客户联系人')
    customer_phone = Column(String(20), comment='客户电话')
    customer_email = Column(String(100), comment='客户邮箱')

    # 项目信息
    project_code = Column(String(50), comment='项目编号')
    project_name = Column(String(200), comment='项目名称')

    # 沟通时间和地点
    communication_date = Column(Date, nullable=False, comment='沟通日期')
    communication_time = Column(String(10), comment='沟通时间')
    duration = Column(Integer, comment='沟通时长（分钟）')
    location = Column(String(200), comment='服务地点')

    # 沟通内容
    topic = Column(String(50), nullable=False, comment='沟通主题')
    subject = Column(String(200), nullable=False, comment='沟通主题')
    content = Column(Text, nullable=False, comment='沟通内容')

    # 后续跟进
    follow_up_required = Column(Boolean, default=False, comment='是否需要后续跟进')
    follow_up_task = Column(Text, comment='跟进任务')
    follow_up_due_date = Column(Date, comment='跟进截止日期')
    follow_up_status = Column(String(20), comment='跟进状态')

    # 标签和重要性
    tags = Column(JSON, comment='标签列表')
    importance = Column(String(10), default='中', comment='重要性：低/中/高')

    # 创建人
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人ID')
    created_by_name = Column(String(50), comment='创建人姓名')

    # 关系
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_communication_customer', 'customer_name'),
        Index('idx_communication_date', 'communication_date'),
        {'comment': '客户沟通记录表'},
    )

    def __repr__(self):
        return f'<CustomerCommunication {self.communication_no}>'


class CustomerSatisfaction(Base, TimestampMixin):
    """客户满意度调查表"""
    __tablename__ = 'customer_satisfactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_no = Column(String(50), unique=True, nullable=False, comment='调查号')

    # 调查类型
    survey_type = Column(String(20), nullable=False, comment='调查类型')

    # 客户信息
    customer_name = Column(String(100), nullable=False, comment='客户名称')
    customer_contact = Column(String(50), comment='客户联系人')
    customer_email = Column(String(100), comment='客户邮箱')
    customer_phone = Column(String(20), comment='客户电话')

    # 项目信息
    project_code = Column(String(50), comment='项目编号')
    project_name = Column(String(200), comment='项目名称')

    # 调查信息
    survey_date = Column(Date, nullable=False, comment='调查日期')
    send_date = Column(Date, comment='发送日期')
    send_method = Column(String(20), comment='发送方式')
    deadline = Column(Date, comment='截止日期')

    # 状态
    status = Column(String(20), default='DRAFT', nullable=False, comment='状态')

    # 回复信息
    response_date = Column(Date, comment='回复日期')
    overall_score = Column(Numeric(3, 1), comment='总体满意度（1-5）')
    scores = Column(JSON, comment='详细评分（JSON格式）')
    feedback = Column(Text, comment='客户反馈')
    suggestions = Column(Text, comment='改进建议')

    # 创建人
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人ID')
    created_by_name = Column(String(50), comment='创建人姓名')

    # 关系
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_satisfaction_customer', 'customer_name'),
        Index('idx_satisfaction_date', 'survey_date'),
        {'comment': '客户满意度调查表'},
    )

    def __repr__(self):
        return f'<CustomerSatisfaction {self.survey_no}>'


class SatisfactionSurveyTemplate(Base, TimestampMixin):
    """满意度调查模板表"""
    __tablename__ = 'satisfaction_survey_templates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_name = Column(String(100), nullable=False, comment='模板名称')
    template_code = Column(String(50), unique=True, nullable=False, comment='模板编码')

    # 模板分类
    survey_type = Column(String(20), nullable=False, comment='调查类型')

    # 模板内容
    questions = Column(JSON, nullable=False, comment='问题列表（JSON格式）')
    # questions格式示例：
    # [
    #   {
    #     "id": 1,
    #     "type": "rating",  # rating/text/choice
    #     "question": "服务响应速度",
    #     "required": true,
    #     "options": null  # 如果是choice类型，这里是选项列表
    #   },
    #   ...
    # ]

    # 默认配置
    default_send_method = Column(String(20), comment='默认发送方式')
    default_deadline_days = Column(Integer, default=7, comment='默认截止天数（从发送日期起）')

    # 使用统计
    usage_count = Column(Integer, default=0, comment='使用次数')
    last_used_at = Column(DateTime, comment='最后使用时间')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')

    # 创建人
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人ID')
    created_by_name = Column(String(50), comment='创建人姓名')

    # 备注
    remark = Column(Text, comment='备注说明')

    # 关系
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_survey_template_code', 'template_code'),
        Index('idx_survey_template_type', 'survey_type'),
        {'comment': '满意度调查模板表'},
    )

    def __repr__(self):
        return f'<SatisfactionSurveyTemplate {self.template_code}: {self.template_name}>'
