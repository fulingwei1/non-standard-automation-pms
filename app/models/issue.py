"""
问题管理中心模块 - 数据模型
支持项目问题、任务问题、验收问题等统一管理
"""
from sqlalchemy import JSON, Boolean, Column, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
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
    service_ticket_id = Column(Integer, ForeignKey('service_tickets.id'), comment='关联服务工单ID')

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

    # 问题原因和责任工程师
    root_cause = Column(String(20), comment='问题原因：DESIGN_ERROR/MATERIAL_DEFECT/PROCESS_ERROR/EXTERNAL_FACTOR/OTHER')
    responsible_engineer_id = Column(Integer, ForeignKey('users.id'), comment='责任工程师ID')
    responsible_engineer_name = Column(String(50), comment='责任工程师姓名')
    estimated_inventory_loss = Column(Numeric(14, 2), comment='预估库存损失金额')
    estimated_extra_hours = Column(Numeric(10, 2), comment='预估额外工时(小时)')

    # 关系
    project = relationship('Project', foreign_keys=[project_id])
    machine = relationship('Machine', foreign_keys=[machine_id])
    reporter = relationship('User', foreign_keys=[reporter_id])
    assignee = relationship('User', foreign_keys=[assignee_id])
    resolver = relationship('User', foreign_keys=[resolved_by])
    verifier = relationship('User', foreign_keys=[verified_by])
    responsible_engineer = relationship('User', foreign_keys=[responsible_engineer_id])
    acceptance_order = relationship('AcceptanceOrder', foreign_keys=[acceptance_order_id])
    related_issue = relationship('Issue', remote_side=[id], foreign_keys=[related_issue_id])
    service_ticket = relationship('ServiceTicket', foreign_keys=[service_ticket_id])
    follow_ups = relationship('IssueFollowUpRecord', back_populates='issue', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        {'comment': '问题表 - 统一的问题管理中心'},
    )

    def __repr__(self):
        return f'<Issue {self.issue_no}: {self.title}>'


class SolutionTemplate(Base, TimestampMixin):
    """解决方案模板表"""
    __tablename__ = 'solution_templates'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    template_name = Column(String(200), nullable=False, comment='模板名称')
    template_code = Column(String(50), unique=True, comment='模板编码')

    # 关联信息
    issue_type = Column(String(20), comment='问题类型')
    category = Column(String(20), comment='问题分类')
    severity = Column(String(20), comment='严重程度')

    # 解决方案内容
    solution = Column(Text, nullable=False, comment='解决方案模板')
    solution_steps = Column(JSON, comment='解决步骤（JSON数组）')
    # 示例结构: [
    #   {"step": 1, "description": "步骤1描述", "expected_result": "预期结果"},
    #   {"step": 2, "description": "步骤2描述", "expected_result": "预期结果"}
    # ]

    # 适用场景
    applicable_scenarios = Column(Text, comment='适用场景描述')
    prerequisites = Column(Text, comment='前置条件')
    precautions = Column(Text, comment='注意事项')

    # 标签和分类
    tags = Column(JSON, comment='标签（JSON数组）')
    keywords = Column(JSON, comment='关键词（JSON数组，用于搜索）')

    # 统计信息
    usage_count = Column(Integer, default=0, comment='使用次数')
    success_rate = Column(Numeric(5, 2), comment='成功率（%）')
    avg_resolution_time = Column(Numeric(10, 2), comment='平均解决时间（小时）')

    # 来源信息
    source_issue_id = Column(Integer, ForeignKey('issues.id'), comment='来源问题ID（从哪个问题提取的模板）')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    created_by_name = Column(String(50), comment='创建人姓名')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_public = Column(Boolean, default=True, comment='是否公开（所有项目可用）')

    # 关系
    source_issue = relationship('Issue', foreign_keys=[source_issue_id])
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_issue_solution_template_type', 'issue_type'),
        Index('idx_issue_solution_template_category', 'category'),
        Index('idx_solution_template_code', 'template_code'),
        {'comment': '解决方案模板表'}
    )

    def __repr__(self):
        return f'<SolutionTemplate {self.template_code}: {self.template_name}>'


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


class IssueStatisticsSnapshot(Base, TimestampMixin):
    """问题统计快照表"""
    __tablename__ = 'issue_statistics_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    snapshot_date = Column(Date, nullable=False, comment='快照日期')

    # 总体统计
    total_issues = Column(Integer, default=0, comment='问题总数')

    # 状态统计
    open_issues = Column(Integer, default=0, comment='待处理问题数')
    processing_issues = Column(Integer, default=0, comment='处理中问题数')
    resolved_issues = Column(Integer, default=0, comment='已解决问题数')
    closed_issues = Column(Integer, default=0, comment='已关闭问题数')
    cancelled_issues = Column(Integer, default=0, comment='已取消问题数')
    deferred_issues = Column(Integer, default=0, comment='已延期问题数')

    # 严重程度统计
    critical_issues = Column(Integer, default=0, comment='严重问题数')
    major_issues = Column(Integer, default=0, comment='重大问题数')
    minor_issues = Column(Integer, default=0, comment='轻微问题数')

    # 优先级统计
    urgent_issues = Column(Integer, default=0, comment='紧急问题数')
    high_priority_issues = Column(Integer, default=0, comment='高优先级问题数')
    medium_priority_issues = Column(Integer, default=0, comment='中优先级问题数')
    low_priority_issues = Column(Integer, default=0, comment='低优先级问题数')

    # 类型统计
    defect_issues = Column(Integer, default=0, comment='缺陷问题数')
    risk_issues = Column(Integer, default=0, comment='风险问题数')
    blocker_issues = Column(Integer, default=0, comment='阻塞问题数')

    # 特殊统计
    blocking_issues = Column(Integer, default=0, comment='阻塞问题数（is_blocking=True）')
    overdue_issues = Column(Integer, default=0, comment='逾期问题数')

    # 分类统计
    project_issues = Column(Integer, default=0, comment='项目问题数')
    task_issues = Column(Integer, default=0, comment='任务问题数')
    acceptance_issues = Column(Integer, default=0, comment='验收问题数')

    # 处理时间统计（小时）
    avg_response_time = Column(Numeric(10, 2), default=0, comment='平均响应时间')
    avg_resolve_time = Column(Numeric(10, 2), default=0, comment='平均解决时间')
    avg_verify_time = Column(Numeric(10, 2), default=0, comment='平均验证时间')

    # 分布数据（JSON格式）
    status_distribution = Column(JSON, comment='状态分布(JSON)')
    severity_distribution = Column(JSON, comment='严重程度分布(JSON)')
    priority_distribution = Column(JSON, comment='优先级分布(JSON)')
    category_distribution = Column(JSON, comment='分类分布(JSON)')
    project_distribution = Column(JSON, comment='项目分布(JSON)')

    # 趋势数据
    new_issues_today = Column(Integer, default=0, comment='今日新增问题数')
    resolved_today = Column(Integer, default=0, comment='今日解决问题数')
    closed_today = Column(Integer, default=0, comment='今日关闭问题数')

    __table_args__ = (
        Index('idx_snapshot_date', 'snapshot_date'),
        {'comment': '问题统计快照表'},
    )

    def __repr__(self):
        return f'<IssueStatisticsSnapshot {self.snapshot_date}: {self.total_issues} issues>'


class IssueTemplate(Base, TimestampMixin):
    """问题模板表"""
    __tablename__ = 'issue_templates'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    template_name = Column(String(100), nullable=False, comment='模板名称')
    template_code = Column(String(50), unique=True, nullable=False, comment='模板编码')

    # 模板分类
    category = Column(String(20), nullable=False, comment='问题分类')
    issue_type = Column(String(20), nullable=False, comment='问题类型')

    # 默认值
    default_severity = Column(String(20), comment='默认严重程度')
    default_priority = Column(String(20), default='MEDIUM', comment='默认优先级')
    default_impact_level = Column(String(20), comment='默认影响级别')

    # 模板内容
    title_template = Column(String(200), nullable=False, comment='标题模板（支持变量）')
    description_template = Column(Text, comment='描述模板（支持变量）')
    solution_template = Column(Text, comment='解决方案模板（支持变量）')

    # 默认字段
    default_tags = Column(Text, comment='默认标签JSON数组')
    default_impact_scope = Column(Text, comment='默认影响范围')
    default_is_blocking = Column(Boolean, default=False, comment='默认是否阻塞')

    # 使用统计
    usage_count = Column(Integer, default=0, comment='使用次数')
    last_used_at = Column(DateTime, comment='最后使用时间')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')

    # 备注
    remark = Column(Text, comment='备注说明')

    __table_args__ = (
        Index('idx_template_code', 'template_code'),
        Index('idx_template_category', 'category'),
        {'comment': '问题模板表'},
    )

    def __repr__(self):
        return f'<IssueTemplate {self.template_code}: {self.template_name}>'

