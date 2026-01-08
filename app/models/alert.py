# -*- coding: utf-8 -*-
"""
预警与异常管理模块模型
"""

from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, DateTime, Date, Text,
    ForeignKey, Numeric, Index, JSON
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class AlertRuleTemplate(Base, TimestampMixin):
    """预警规则模板表"""
    __tablename__ = 'alert_rule_templates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_code = Column(String(50), unique=True, nullable=False, comment='模板编码')
    template_name = Column(String(200), nullable=False, comment='模板名称')
    template_category = Column(String(30), nullable=False, comment='模板分类')
    rule_config = Column(JSON, nullable=False, comment='规则配置')
    description = Column(Text, comment='模板说明')
    usage_guide = Column(Text, comment='使用指南')
    is_active = Column(Boolean, default=True, comment='是否启用')

    def __repr__(self):
        return f'<AlertRuleTemplate {self.template_code}>'


class AlertRule(Base, TimestampMixin):
    """预警规则表"""
    __tablename__ = 'alert_rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_code = Column(String(50), unique=True, nullable=False, comment='规则编码')
    rule_name = Column(String(200), nullable=False, comment='规则名称')
    rule_type = Column(String(30), nullable=False, comment='规则类型')

    # 监控对象
    target_type = Column(String(30), nullable=False, comment='监控对象类型')
    target_field = Column(String(100), comment='监控字段')

    # 触发条件
    condition_type = Column(String(20), nullable=False, comment='条件类型')
    condition_operator = Column(String(10), comment='条件运算符')
    threshold_value = Column(String(100), comment='阈值')
    threshold_min = Column(String(50), comment='阈值下限')
    threshold_max = Column(String(50), comment='阈值上限')
    condition_expr = Column(Text, comment='自定义条件表达式')

    # 预警级别
    alert_level = Column(String(20), default='WARNING', comment='预警级别')

    # 提前预警
    advance_days = Column(Integer, default=0, comment='提前预警天数')

    # 通知配置
    notify_channels = Column(JSON, comment='通知渠道')
    notify_roles = Column(JSON, comment='通知角色')
    notify_users = Column(JSON, comment='指定通知用户')

    # 执行配置
    check_frequency = Column(String(20), default='DAILY', comment='检查频率')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    is_system = Column(Boolean, default=False, comment='是否系统预置')

    # 描述
    description = Column(Text, comment='规则说明')
    solution_guide = Column(Text, comment='处理指南')

    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    records = relationship('AlertRecord', back_populates='rule', lazy='dynamic')

    __table_args__ = (
        Index('idx_rule_type', 'rule_type'),
        Index('idx_rule_target', 'target_type'),
        Index('idx_rule_enabled', 'is_enabled'),
    )

    def __repr__(self):
        return f'<AlertRule {self.rule_code}>'


class AlertRecord(Base, TimestampMixin):
    """预警记录表"""
    __tablename__ = 'alert_records'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    alert_no = Column(String(50), unique=True, nullable=False, comment='预警编号')
    rule_id = Column(Integer, ForeignKey('alert_rules.id'), nullable=False, comment='触发的规则ID')

    # 预警对象
    target_type = Column(String(30), nullable=False, comment='对象类型')
    target_id = Column(Integer, nullable=False, comment='对象ID')
    target_no = Column(String(100), comment='对象编号')
    target_name = Column(String(200), comment='对象名称')

    # 关联项目
    project_id = Column(Integer, ForeignKey('projects.id'), comment='关联项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='关联设备ID')

    # 预警信息
    alert_level = Column(String(20), nullable=False, comment='预警级别')
    alert_title = Column(String(200), nullable=False, comment='预警标题')
    alert_content = Column(Text, nullable=False, comment='预警内容')
    alert_data = Column(JSON, comment='预警数据')

    # 触发信息
    triggered_at = Column(DateTime, comment='触发时间')
    trigger_value = Column(String(100), comment='触发时的值')
    threshold_value = Column(String(100), comment='阈值')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')

    # 确认信息
    acknowledged_by = Column(Integer, ForeignKey('users.id'), comment='确认人')
    acknowledged_at = Column(DateTime, comment='确认时间')

    # 处理信息
    handler_id = Column(Integer, ForeignKey('users.id'), comment='处理人')
    handle_start_at = Column(DateTime, comment='开始处理时间')
    handle_end_at = Column(DateTime, comment='处理完成时间')
    handle_result = Column(Text, comment='处理结果')
    handle_note = Column(Text, comment='处理说明')

    # 是否升级
    is_escalated = Column(Boolean, default=False, comment='是否升级')
    escalated_at = Column(DateTime, comment='升级时间')
    escalated_to = Column(Integer, ForeignKey('users.id'), comment='升级给谁')

    # 关系
    rule = relationship('AlertRule', back_populates='records')
    project = relationship('Project')
    machine = relationship('Machine')
    notifications = relationship('AlertNotification', back_populates='alert', lazy='dynamic')

    __table_args__ = (
        Index('idx_alert_rule', 'rule_id'),
        Index('idx_alert_target', 'target_type', 'target_id'),
        Index('idx_alert_project', 'project_id'),
        Index('idx_alert_status', 'status'),
        Index('idx_alert_level', 'alert_level'),
        Index('idx_alert_time', 'triggered_at'),
    )

    def __repr__(self):
        return f'<AlertRecord {self.alert_no}>'


class AlertNotification(Base, TimestampMixin):
    """预警通知记录表"""
    __tablename__ = 'alert_notifications'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    alert_id = Column(BigInteger, ForeignKey('alert_records.id'), nullable=False, comment='预警记录ID')

    # 通知信息
    notify_channel = Column(String(20), nullable=False, comment='通知渠道')
    notify_target = Column(String(200), nullable=False, comment='通知目标')
    notify_user_id = Column(Integer, ForeignKey('users.id'), comment='通知用户ID')

    # 通知内容
    notify_title = Column(String(200), comment='通知标题')
    notify_content = Column(Text, comment='通知内容')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    sent_at = Column(DateTime, comment='发送时间')
    read_at = Column(DateTime, comment='阅读时间')
    error_message = Column(Text, comment='错误信息')

    # 重试
    retry_count = Column(Integer, default=0, comment='重试次数')
    next_retry_at = Column(DateTime, comment='下次重试时间')

    # 关系
    alert = relationship('AlertRecord', back_populates='notifications')

    __table_args__ = (
        Index('idx_notification_alert', 'alert_id'),
        Index('idx_notification_user', 'notify_user_id'),
        Index('idx_notification_status', 'status'),
    )


class ExceptionEvent(Base, TimestampMixin):
    """异常事件表"""
    __tablename__ = 'exception_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_no = Column(String(50), unique=True, nullable=False, comment='异常编号')

    # 异常来源
    source_type = Column(String(30), nullable=False, comment='来源类型')
    source_id = Column(Integer, comment='来源ID')
    alert_id = Column(BigInteger, ForeignKey('alert_records.id'), comment='关联预警ID')

    # 关联对象
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='设备ID')

    # 异常信息
    event_type = Column(String(30), nullable=False, comment='异常类型')
    severity = Column(String(20), nullable=False, comment='严重程度')
    event_title = Column(String(200), nullable=False, comment='异常标题')
    event_description = Column(Text, nullable=False, comment='异常描述')

    # 发现信息
    discovered_at = Column(DateTime, comment='发现时间')
    discovered_by = Column(Integer, ForeignKey('users.id'), comment='发现人')
    discovery_location = Column(String(200), comment='发现地点')

    # 影响评估
    impact_scope = Column(String(20), comment='影响范围')
    impact_description = Column(Text, comment='影响描述')
    schedule_impact = Column(Integer, default=0, comment='工期影响(天)')
    cost_impact = Column(Numeric(14, 2), default=0, comment='成本影响')

    # 状态
    status = Column(String(20), default='OPEN', comment='状态')

    # 责任人
    responsible_dept = Column(String(50), comment='责任部门')
    responsible_user_id = Column(Integer, ForeignKey('users.id'), comment='责任人')

    # 处理期限
    due_date = Column(Date, comment='要求完成日期')
    is_overdue = Column(Boolean, default=False, comment='是否超期')

    # 根本原因
    root_cause = Column(Text, comment='根本原因分析')
    cause_category = Column(String(50), comment='原因分类')

    # 解决方案
    solution = Column(Text, comment='解决方案')
    preventive_measures = Column(Text, comment='预防措施')

    # 处理结果
    resolved_at = Column(DateTime, comment='解决时间')
    resolved_by = Column(Integer, ForeignKey('users.id'), comment='解决人')
    resolution_note = Column(Text, comment='解决说明')

    # 验证
    verified_at = Column(DateTime, comment='验证时间')
    verified_by = Column(Integer, ForeignKey('users.id'), comment='验证人')
    verification_result = Column(String(20), comment='验证结果')

    # 附件
    attachments = Column(JSON, comment='附件')

    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    project = relationship('Project')
    machine = relationship('Machine')
    alert = relationship('AlertRecord')
    actions = relationship('ExceptionAction', back_populates='event', lazy='dynamic')
    escalations = relationship('ExceptionEscalation', back_populates='event', lazy='dynamic')

    __table_args__ = (
        Index('idx_event_project', 'project_id'),
        Index('idx_event_type', 'event_type'),
        Index('idx_event_severity', 'severity'),
        Index('idx_event_status', 'status'),
        Index('idx_event_responsible', 'responsible_user_id'),
    )

    def __repr__(self):
        return f'<ExceptionEvent {self.event_no}>'


class ExceptionAction(Base, TimestampMixin):
    """异常处理记录表"""
    __tablename__ = 'exception_actions'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('exception_events.id'), nullable=False, comment='异常事件ID')

    # 操作信息
    action_type = Column(String(30), nullable=False, comment='操作类型')
    action_content = Column(Text, nullable=False, comment='操作内容')

    # 状态变更
    old_status = Column(String(20), comment='原状态')
    new_status = Column(String(20), comment='新状态')

    # 附件
    attachments = Column(JSON, comment='附件')

    created_by = Column(Integer, ForeignKey('users.id'), comment='操作人')

    # 关系
    event = relationship('ExceptionEvent', back_populates='actions')

    __table_args__ = (
        Index('idx_action_event', 'event_id'),
        Index('idx_action_type', 'action_type'),
    )


class ExceptionEscalation(Base, TimestampMixin):
    """异常升级记录表"""
    __tablename__ = 'exception_escalations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('exception_events.id'), nullable=False, comment='异常事件ID')
    escalation_level = Column(Integer, nullable=False, comment='升级层级')

    # 升级信息
    escalated_from = Column(Integer, ForeignKey('users.id'), comment='升级发起人')
    escalated_to = Column(Integer, ForeignKey('users.id'), nullable=False, comment='升级接收人')
    escalated_at = Column(DateTime, comment='升级时间')
    escalation_reason = Column(Text, comment='升级原因')

    # 响应
    response_status = Column(String(20), default='PENDING', comment='响应状态')
    responded_at = Column(DateTime, comment='响应时间')
    response_note = Column(Text, comment='响应说明')

    # 关系
    event = relationship('ExceptionEvent', back_populates='escalations')

    __table_args__ = (
        Index('idx_escalation_event', 'event_id'),
    )


class AlertStatistics(Base, TimestampMixin):
    """预警统计表"""
    __tablename__ = 'alert_statistics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(Date, nullable=False, comment='统计日期')
    stat_type = Column(String(20), nullable=False, comment='统计类型')

    # 预警统计
    total_alerts = Column(Integer, default=0, comment='预警总数')
    info_alerts = Column(Integer, default=0, comment='提示级别')
    warning_alerts = Column(Integer, default=0, comment='警告级别')
    critical_alerts = Column(Integer, default=0, comment='严重级别')
    urgent_alerts = Column(Integer, default=0, comment='紧急级别')

    # 处理统计
    pending_alerts = Column(Integer, default=0, comment='待处理')
    processing_alerts = Column(Integer, default=0, comment='处理中')
    resolved_alerts = Column(Integer, default=0, comment='已解决')
    ignored_alerts = Column(Integer, default=0, comment='已忽略')

    # 异常统计
    total_exceptions = Column(Integer, default=0, comment='异常总数')
    open_exceptions = Column(Integer, default=0, comment='未关闭异常')
    overdue_exceptions = Column(Integer, default=0, comment='超期异常')

    # 响应时间(小时)
    avg_response_time = Column(Numeric(10, 2), default=0, comment='平均响应时间')
    avg_resolve_time = Column(Numeric(10, 2), default=0, comment='平均解决时间')

    __table_args__ = (
        Index('idx_stat_date', 'stat_date'),
        Index('idx_stat_type', 'stat_type'),
    )


class ProjectHealthSnapshot(Base, TimestampMixin):
    """项目健康度快照表"""
    __tablename__ = 'project_health_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    snapshot_date = Column(Date, nullable=False, comment='快照日期')

    # 健康指标
    overall_health = Column(String(10), nullable=False, comment='综合健康度')
    schedule_health = Column(String(10), comment='进度健康度')
    cost_health = Column(String(10), comment='成本健康度')
    quality_health = Column(String(10), comment='质量健康度')
    resource_health = Column(String(10), comment='资源健康度')

    # 健康评分(0-100)
    health_score = Column(Integer, default=0, comment='综合评分')

    # 风险指标
    open_alerts = Column(Integer, default=0, comment='未处理预警数')
    open_exceptions = Column(Integer, default=0, comment='未关闭异常数')
    blocking_issues = Column(Integer, default=0, comment='阻塞问题数')

    # 进度指标
    schedule_variance = Column(Numeric(5, 2), default=0, comment='进度偏差(%)')
    milestone_on_track = Column(Integer, default=0, comment='按期里程碑数')
    milestone_delayed = Column(Integer, default=0, comment='延期里程碑数')

    # 成本指标
    cost_variance = Column(Numeric(5, 2), default=0, comment='成本偏差(%)')
    budget_used_pct = Column(Numeric(5, 2), default=0, comment='预算使用率(%)')

    # 主要风险
    top_risks = Column(JSON, comment='主要风险')

    # 关系
    project = relationship('Project')

    __table_args__ = (
        Index('idx_health_project', 'project_id'),
        Index('idx_health_date', 'snapshot_date'),
    )


class AlertSubscription(Base, TimestampMixin):
    """预警订阅配置表"""
    __tablename__ = 'alert_subscriptions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    
    # 订阅范围
    alert_type = Column(String(50), comment='预警类型（空表示全部）')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID（空表示全部）')
    
    # 订阅配置
    min_level = Column(String(20), default='WARNING', comment='最低接收级别')
    notify_channels = Column(JSON, comment='通知渠道（JSON数组）')
    
    # 免打扰时段
    quiet_start = Column(String(10), comment='免打扰开始时间（HH:mm格式）')
    quiet_end = Column(String(10), comment='免打扰结束时间（HH:mm格式）')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    # 关系
    user = relationship('User')
    project = relationship('Project')
    
    __table_args__ = (
        Index('idx_alert_subscriptions_user', 'user_id'),
        Index('idx_alert_subscriptions_type', 'alert_type'),
        Index('idx_alert_subscriptions_project', 'project_id'),
        Index('idx_alert_subscriptions_active', 'is_active'),
    )
    
    def __repr__(self):
        return f'<AlertSubscription user_id={self.user_id} alert_type={self.alert_type}>'
