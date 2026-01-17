# -*- coding: utf-8 -*-
"""
客服服务模块 ORM 模型
包含：服务工单、现场服务记录、客户沟通、满意度调查、知识库
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

class ServiceTicketStatusEnum(str, Enum):
    """服务工单状态"""
    PENDING = 'PENDING'          # 待分配
    IN_PROGRESS = 'IN_PROGRESS'  # 处理中
    RESOLVED = 'RESOLVED'        # 待验证
    CLOSED = 'CLOSED'            # 已关闭


class ServiceTicketUrgencyEnum(str, Enum):
    """服务工单紧急程度"""
    LOW = 'LOW'                  # 低
    MEDIUM = 'MEDIUM'            # 中
    HIGH = 'HIGH'                # 高
    URGENT = 'URGENT'            # 紧急


class ServiceTicketProblemTypeEnum(str, Enum):
    """问题类型"""
    SOFTWARE = 'SOFTWARE'        # 软件问题
    MECHANICAL = 'MECHANICAL'    # 机械问题
    ELECTRICAL = 'ELECTRICAL'    # 电气问题
    OPERATION = 'OPERATION'      # 操作问题
    OTHER = 'OTHER'              # 其他


class ServiceRecordTypeEnum(str, Enum):
    """服务记录类型"""
    INSTALLATION = 'INSTALLATION'  # 安装调试
    TRAINING = 'TRAINING'          # 操作培训
    MAINTENANCE = 'MAINTENANCE'     # 定期维护
    REPAIR = 'REPAIR'               # 故障维修
    OTHER = 'OTHER'                 # 其他


class ServiceRecordStatusEnum(str, Enum):
    """服务记录状态"""
    SCHEDULED = 'SCHEDULED'      # 已排期
    IN_PROGRESS = 'IN_PROGRESS'  # 进行中
    COMPLETED = 'COMPLETED'      # 已完成
    CANCELLED = 'CANCELLED'      # 已取消


class CommunicationTypeEnum(str, Enum):
    """沟通方式"""
    PHONE = 'PHONE'              # 电话
    EMAIL = 'EMAIL'              # 邮件
    ON_SITE = 'ON_SITE'          # 现场
    WECHAT = 'WECHAT'            # 微信
    MEETING = 'MEETING'          # 会议
    OTHER = 'OTHER'              # 其他


class SurveyStatusEnum(str, Enum):
    """满意度调查状态"""
    DRAFT = 'DRAFT'              # 待发送
    SENT = 'SENT'                # 已发送
    PENDING = 'PENDING'          # 待回复
    COMPLETED = 'COMPLETED'      # 已完成
    EXPIRED = 'EXPIRED'          # 已过期


class SurveyTypeEnum(str, Enum):
    """调查类型"""
    PROJECT = 'PROJECT'          # 项目满意度
    SERVICE = 'SERVICE'          # 服务满意度
    PRODUCT = 'PRODUCT'          # 产品满意度


# ==================== 服务工单 ====================

class ServiceTicket(Base, TimestampMixin):
    """服务工单表"""
    __tablename__ = 'service_tickets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_no = Column(String(50), unique=True, nullable=False, comment='工单号')

    # 关联信息
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, comment='客户ID')

    # 问题信息
    problem_type = Column(String(20), nullable=False, comment='问题类型')
    problem_desc = Column(Text, nullable=False, comment='问题描述')
    urgency = Column(String(20), nullable=False, comment='紧急程度')

    # 报告人信息
    reported_by = Column(String(50), nullable=False, comment='报告人')
    reported_time = Column(DateTime, nullable=False, comment='报告时间')

    # 处理人信息
    assigned_to_id = Column(Integer, ForeignKey('users.id'), comment='处理人ID')
    assigned_to_name = Column(String(50), comment='处理人姓名')
    assigned_time = Column(DateTime, comment='分配时间')

    # 状态和时间
    status = Column(String(20), default='PENDING', nullable=False, comment='状态')
    response_time = Column(DateTime, comment='响应时间')
    resolved_time = Column(DateTime, comment='解决时间')

    # 解决方案
    solution = Column(Text, comment='解决方案')
    root_cause = Column(Text, comment='根本原因')
    preventive_action = Column(Text, comment='预防措施')

    # 满意度
    satisfaction = Column(Integer, comment='满意度1-5')
    feedback = Column(Text, comment='客户反馈')

    # 时间线（JSON格式存储）
    timeline = Column(JSON, comment='时间线记录')

    # 关系
    project = relationship('Project', foreign_keys=[project_id])
    customer = relationship('Customer', foreign_keys=[customer_id])
    assignee = relationship('User', foreign_keys=[assigned_to_id])

    __table_args__ = (
        Index('idx_service_ticket_project', 'project_id'),
        Index('idx_service_ticket_customer', 'customer_id'),
        Index('idx_service_ticket_status', 'status'),
        {'comment': '服务工单表'},
    )

    # 多项目关联关系
    related_projects = relationship(
        'ServiceTicketProject',
        back_populates='ticket',
        cascade='all, delete-orphan'
    )

    # 抄送人员关系
    cc_users = relationship(
        'ServiceTicketCcUser',
        back_populates='ticket',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<ServiceTicket {self.ticket_no}>'


# ==================== 工单项目关联表 ====================

class ServiceTicketProject(Base, TimestampMixin):
    """工单项目关联表（支持多对多）"""
    __tablename__ = 'service_ticket_projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('service_tickets.id', ondelete='CASCADE'), nullable=False, comment='工单ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    is_primary = Column(Boolean, default=False, comment='是否主项目')

    # 关系
    ticket = relationship('ServiceTicket', back_populates='related_projects')
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_ticket_projects_ticket', 'ticket_id'),
        Index('idx_ticket_projects_project', 'project_id'),
        {'comment': '工单项目关联表'},
    )

    def __repr__(self):
        return f'<ServiceTicketProject ticket_id={self.ticket_id} project_id={self.project_id}>'


# ==================== 工单抄送人员表 ====================

class ServiceTicketCcUser(Base, TimestampMixin):
    """工单抄送人员表"""
    __tablename__ = 'service_ticket_cc_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('service_tickets.id', ondelete='CASCADE'), nullable=False, comment='工单ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    notified_at = Column(DateTime, comment='通知时间')
    read_at = Column(DateTime, comment='阅读时间')

    # 关系
    ticket = relationship('ServiceTicket', back_populates='cc_users')
    user = relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        Index('idx_ticket_cc_ticket', 'ticket_id'),
        Index('idx_ticket_cc_user', 'user_id'),
        {'comment': '工单抄送人员表'},
    )

    def __repr__(self):
        return f'<ServiceTicketCcUser ticket_id={self.ticket_id} user_id={self.user_id}>'


# ==================== 现场服务记录 ====================

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


# ==================== 客户沟通 ====================

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


# ==================== 满意度调查 ====================

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


# ==================== 满意度调查模板 ====================

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


# ==================== 知识库 ====================

class KnowledgeBase(Base, TimestampMixin):
    """知识库文章表"""
    __tablename__ = 'knowledge_base'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_no = Column(String(50), unique=True, nullable=False, comment='文章编号')

    # 基本信息
    title = Column(String(200), nullable=False, comment='文章标题')
    category = Column(String(50), nullable=False, comment='分类')
    content = Column(Text, nullable=True, comment='文章内容')

    # 文件信息
    file_path = Column(String(500), nullable=True, comment='文件路径')
    file_name = Column(String(200), nullable=True, comment='原始文件名')
    file_size = Column(Integer, nullable=True, comment='文件大小（字节）')
    file_type = Column(String(100), nullable=True, comment='文件MIME类型')

    # 标签和标记
    tags = Column(JSON, comment='标签列表')
    is_faq = Column(Boolean, default=False, comment='是否FAQ')
    is_featured = Column(Boolean, default=False, comment='是否精选')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态：草稿/已发布/已归档')

    # 统计信息
    view_count = Column(Integer, default=0, comment='浏览量')
    like_count = Column(Integer, default=0, comment='点赞数')
    helpful_count = Column(Integer, default=0, comment='有用数')
    download_count = Column(Integer, default=0, comment='下载次数')
    adopt_count = Column(Integer, default=0, comment='采用次数')

    # 权限设置
    allow_download = Column(Boolean, default=True, comment='是否允许他人下载')

    # 作者
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='作者ID')
    author_name = Column(String(50), comment='作者姓名')

    # 关系
    author = relationship('User', foreign_keys=[author_id])

    __table_args__ = (
        Index('idx_kb_category', 'category'),
        Index('idx_kb_status', 'status'),
        Index('idx_kb_faq', 'is_faq'),
        {'comment': '知识库文章表'},
    )

    def __repr__(self):
        return f'<KnowledgeBase {self.article_no}>'



