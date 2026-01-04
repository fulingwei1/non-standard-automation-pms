"""
问题管理中心模块 - 数据模型
支持项目问题、任务问题、验收问题等统一管理
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import IssueStatusEnum, SeverityEnum


class IssueCategoryEnum(str):
    """问题分类"""
    PROJECT = 'PROJECT'          # 项目问题
    TASK = 'TASK'                # 任务问题
    ACCEPTANCE = 'ACCEPTANCE'    # 验收问题
    QUALITY = 'QUALITY'          # 质量问题
    TECHNICAL = 'TECHNICAL'      # 技术问题
    RESOURCE = 'RESOURCE'        # 资源问题
    SCHEDULE = 'SCHEDULE'        # 进度问题
    CUSTOMER = 'CUSTOMER'        # 客户问题
    OTHER = 'OTHER'              # 其他


class IssueTypeEnum(str):
    """问题类型"""
    DEFECT = 'DEFECT'            # 缺陷
    DEVIATION = 'DEVIATION'      # 偏差
    RISK = 'RISK'                # 风险
    BLOCKER = 'BLOCKER'          # 阻塞
    SUGGESTION = 'SUGGESTION'    # 建议
    QUESTION = 'QUESTION'        # 疑问
    OTHER = 'OTHER'              # 其他


class Issue(Base, TimestampMixin):
    """问题表 - 统一的问题管理中心"""
    __tablename__ = 'issues'

    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_no = Column(String(50), unique=True, nullable=False, comment='问题编号')
    
    # 关联信息
    category = Column(String(20), nullable=False, comment='问题分类')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='关联项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='关联机台ID')
    task_id = Column(Integer, comment='关联任务ID')
    acceptance_order_id = Column(Integer, ForeignKey('acceptance_orders.id'), comment='关联验收单ID')
    related_issue_id = Column(Integer, ForeignKey('issues.id'), comment='关联问题ID（父子问题）')
    
    # 问题基本信息
    issue_type = Column(String(20), nullable=False, comment='问题类型')
    severity = Column(String(20), nullable=False, comment='严重程度')
    priority = Column(String(20), default='MEDIUM', comment='优先级：LOW/MEDIUM/HIGH/URGENT')
    title = Column(String(200), nullable=False, comment='问题标题')
    description = Column(Text, nullable=False, comment='问题描述')
    
    # 提出人信息
    reporter_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='提出人ID')
    reporter_name = Column(String(50), comment='提出人姓名')
    report_date = Column(DateTime, nullable=False, comment='提出时间')
    
    # 处理人信息
    assignee_id = Column(Integer, ForeignKey('users.id'), comment='处理负责人ID')
    assignee_name = Column(String(50), comment='处理负责人姓名')
    due_date = Column(Date, comment='要求完成日期')
    
    # 状态信息
    status = Column(String(20), default='OPEN', nullable=False, comment='问题状态')
    
    # 解决信息
    solution = Column(Text, comment='解决方案')
    resolved_at = Column(DateTime, comment='解决时间')
    resolved_by = Column(Integer, ForeignKey('users.id'), comment='解决人ID')
    resolved_by_name = Column(String(50), comment='解决人姓名')
    
    # 验证信息
    verified_at = Column(DateTime, comment='验证时间')
    verified_by = Column(Integer, ForeignKey('users.id'), comment='验证人ID')
    verified_by_name = Column(String(50), comment='验证人姓名')
    verified_result = Column(String(20), comment='验证结果：VERIFIED/REJECTED')
    
    # 影响评估
    impact_scope = Column(Text, comment='影响范围')
    impact_level = Column(String(20), comment='影响级别：LOW/MEDIUM/HIGH/CRITICAL')
    is_blocking = Column(Boolean, default=False, comment='是否阻塞项目/任务')
    
    # 附件和标签
    attachments = Column(Text, comment='附件列表JSON')
    tags = Column(Text, comment='标签JSON数组')
    
    # 统计信息
    follow_up_count = Column(Integer, default=0, comment='跟进次数')
    last_follow_up_at = Column(DateTime, comment='最后跟进时间')
    
    # 关系
    project = relationship('Project', foreign_keys=[project_id])
    machine = relationship('Machine', foreign_keys=[machine_id])
    reporter = relationship('User', foreign_keys=[reporter_id])
    assignee = relationship('User', foreign_keys=[assignee_id])
    resolver = relationship('User', foreign_keys=[resolved_by])
    verifier = relationship('User', foreign_keys=[verified_by])
    acceptance_order = relationship('AcceptanceOrder', foreign_keys=[acceptance_order_id])
    related_issue = relationship('Issue', remote_side=[id], foreign_keys=[related_issue_id])
    follow_ups = relationship('IssueFollowUpRecord', back_populates='issue', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        {'comment': '问题表 - 统一的问题管理中心'},
    )
    
    def __repr__(self):
        return f'<Issue {self.issue_no}: {self.title}>'


class IssueFollowUpRecord(Base, TimestampMixin):
    """问题跟进记录表（通用问题管理）"""
    __tablename__ = 'issue_follow_up_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(Integer, ForeignKey('issues.id'), nullable=False, comment='问题ID')
    
    # 跟进信息
    follow_up_type = Column(String(20), nullable=False, comment='跟进类型：COMMENT/STATUS_CHANGE/ASSIGNMENT/SOLUTION/VERIFICATION')
    content = Column(Text, nullable=False, comment='跟进内容')
    
    # 操作人
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='操作人ID')
    operator_name = Column(String(50), comment='操作人姓名')
    
    # 状态变更（如果是状态变更类型）
    old_status = Column(String(20), comment='原状态')
    new_status = Column(String(20), comment='新状态')
    
    # 附件
    attachments = Column(Text, comment='附件列表JSON')
    
    # 关系
    issue = relationship('Issue', back_populates='follow_ups')
    operator = relationship('User', foreign_keys=[operator_id])
    
    __table_args__ = (
        {'comment': '问题跟进记录表'},
    )
    
    def __repr__(self):
        return f'<IssueFollowUpRecord {self.id}: {self.follow_up_type}>'

