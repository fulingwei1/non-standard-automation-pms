# -*- coding: utf-8 -*-
"""
验收管理模块模型
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text,
    ForeignKey, Numeric, Index, JSON
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class AcceptanceTemplate(Base, TimestampMixin):
    """验收模板表"""
    __tablename__ = 'acceptance_templates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_code = Column(String(50), unique=True, nullable=False, comment='模板编码')
    template_name = Column(String(200), nullable=False, comment='模板名称')
    acceptance_type = Column(String(20), nullable=False, comment='FAT/SAT/FINAL')
    equipment_type = Column(String(50), comment='设备类型')
    version = Column(String(20), default='1.0', comment='版本号')
    description = Column(Text, comment='模板说明')
    is_system = Column(Boolean, default=False, comment='是否系统预置')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    categories = relationship('TemplateCategory', back_populates='template', lazy='dynamic')

    __table_args__ = (
        Index('idx_template_type', 'acceptance_type'),
        Index('idx_template_equip', 'equipment_type'),
    )

    def __repr__(self):
        return f'<AcceptanceTemplate {self.template_code}>'


class TemplateCategory(Base, TimestampMixin):
    """模板检查分类表"""
    __tablename__ = 'template_categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey('acceptance_templates.id'), nullable=False, comment='所属模板')
    category_code = Column(String(20), nullable=False, comment='分类编码')
    category_name = Column(String(100), nullable=False, comment='分类名称')
    weight = Column(Numeric(5, 2), default=0, comment='权重百分比')
    sort_order = Column(Integer, default=0, comment='排序')
    is_required = Column(Boolean, default=True, comment='是否必检分类')
    description = Column(Text, comment='分类说明')

    # 关系
    template = relationship('AcceptanceTemplate', back_populates='categories')
    check_items = relationship('TemplateCheckItem', back_populates='category', lazy='dynamic')

    __table_args__ = (
        Index('idx_category_template', 'template_id'),
    )


class TemplateCheckItem(Base, TimestampMixin):
    """模板检查项表"""
    __tablename__ = 'template_check_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey('template_categories.id'), nullable=False, comment='所属分类')
    item_code = Column(String(50), nullable=False, comment='检查项编码')
    item_name = Column(String(200), nullable=False, comment='检查项名称')
    check_method = Column(Text, comment='检查方法')
    acceptance_criteria = Column(Text, comment='验收标准')
    standard_value = Column(String(100), comment='标准值')
    tolerance_min = Column(String(50), comment='下限')
    tolerance_max = Column(String(50), comment='上限')
    unit = Column(String(20), comment='单位')
    is_required = Column(Boolean, default=True, comment='是否必检项')
    is_key_item = Column(Boolean, default=False, comment='是否关键项')
    sort_order = Column(Integer, default=0, comment='排序')

    # 关系
    category = relationship('TemplateCategory', back_populates='check_items')

    __table_args__ = (
        Index('idx_check_item_category', 'category_id'),
    )


class AcceptanceOrder(Base, TimestampMixin):
    """验收单表"""
    __tablename__ = 'acceptance_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, comment='验收单号')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='设备ID')
    acceptance_type = Column(String(20), nullable=False, comment='FAT/SAT/FINAL')
    template_id = Column(Integer, ForeignKey('acceptance_templates.id'), comment='使用的模板')

    # 验收信息
    planned_date = Column(Date, comment='计划验收日期')
    actual_start_date = Column(DateTime, comment='实际开始时间')
    actual_end_date = Column(DateTime, comment='实际结束时间')
    location = Column(String(200), comment='验收地点')

    # 状态
    status = Column(String(20), default='DRAFT', comment='验收状态')

    # 统计
    total_items = Column(Integer, default=0, comment='检查项总数')
    passed_items = Column(Integer, default=0, comment='通过项数')
    failed_items = Column(Integer, default=0, comment='不通过项数')
    na_items = Column(Integer, default=0, comment='不适用项数')
    pass_rate = Column(Numeric(5, 2), default=0, comment='通过率')

    # 结论
    overall_result = Column(String(20), comment='PASSED/FAILED/CONDITIONAL')
    conclusion = Column(Text, comment='验收结论')
    conditions = Column(Text, comment='有条件通过的条件说明')

    # 签字确认
    qa_signer_id = Column(Integer, ForeignKey('users.id'), comment='QA签字人')
    qa_signed_at = Column(DateTime, comment='QA签字时间')
    customer_signer = Column(String(100), comment='客户签字人')
    customer_signed_at = Column(DateTime, comment='客户签字时间')
    customer_signature = Column(Text, comment='客户电子签名')

    # 附件
    report_file_path = Column(String(500), comment='验收报告文件路径')

    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    project = relationship('Project')
    machine = relationship('Machine')
    template = relationship('AcceptanceTemplate')
    items = relationship('AcceptanceOrderItem', back_populates='order', lazy='dynamic')
    issues = relationship('AcceptanceIssue', back_populates='order', lazy='dynamic')
    signatures = relationship('AcceptanceSignature', back_populates='order', lazy='dynamic')
    reports = relationship('AcceptanceReport', back_populates='order', lazy='dynamic')

    __table_args__ = (
        Index('idx_order_project', 'project_id'),
        Index('idx_order_machine', 'machine_id'),
        Index('idx_order_status', 'status'),
        Index('idx_order_type', 'acceptance_type'),
    )

    def __repr__(self):
        return f'<AcceptanceOrder {self.order_no}>'


class AcceptanceOrderItem(Base, TimestampMixin):
    """验收单检查项表"""
    __tablename__ = 'acceptance_order_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('acceptance_orders.id'), nullable=False, comment='验收单ID')
    template_item_id = Column(Integer, ForeignKey('template_check_items.id'), comment='模板检查项ID')

    # 检查项信息(从模板复制)
    category_code = Column(String(20), nullable=False, comment='分类编码')
    category_name = Column(String(100), nullable=False, comment='分类名称')
    item_code = Column(String(50), nullable=False, comment='检查项编码')
    item_name = Column(String(200), nullable=False, comment='检查项名称')
    check_method = Column(Text, comment='检查方法')
    acceptance_criteria = Column(Text, comment='验收标准')
    standard_value = Column(String(100), comment='标准值')
    tolerance_min = Column(String(50), comment='下限')
    tolerance_max = Column(String(50), comment='上限')
    unit = Column(String(20), comment='单位')
    is_required = Column(Boolean, default=True, comment='是否必检项')
    is_key_item = Column(Boolean, default=False, comment='是否关键项')
    sort_order = Column(Integer, default=0, comment='排序')

    # 检查结果
    result_status = Column(String(20), default='PENDING', comment='结果状态')
    actual_value = Column(String(100), comment='实际值')
    deviation = Column(String(100), comment='偏差')
    remark = Column(Text, comment='备注')

    # 检查记录
    checked_by = Column(Integer, ForeignKey('users.id'), comment='检查人')
    checked_at = Column(DateTime, comment='检查时间')

    # 复验信息
    retry_count = Column(Integer, default=0, comment='复验次数')
    last_retry_at = Column(DateTime, comment='最后复验时间')

    # 关系
    order = relationship('AcceptanceOrder', back_populates='items')

    __table_args__ = (
        Index('idx_order_item_order', 'order_id'),
        Index('idx_order_item_status', 'result_status'),
    )


class AcceptanceIssue(Base, TimestampMixin):
    """验收问题表"""
    __tablename__ = 'acceptance_issues'

    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_no = Column(String(50), unique=True, nullable=False, comment='问题编号')
    order_id = Column(Integer, ForeignKey('acceptance_orders.id'), nullable=False, comment='验收单ID')
    order_item_id = Column(Integer, ForeignKey('acceptance_order_items.id'), comment='关联检查项')

    # 问题信息
    issue_type = Column(String(20), nullable=False, comment='问题类型')
    severity = Column(String(20), nullable=False, comment='严重程度')
    title = Column(String(200), nullable=False, comment='问题标题')
    description = Column(Text, nullable=False, comment='问题描述')
    found_at = Column(DateTime, comment='发现时间')
    found_by = Column(Integer, ForeignKey('users.id'), comment='发现人')

    # 处理信息
    status = Column(String(20), default='OPEN', comment='状态')
    assigned_to = Column(Integer, ForeignKey('users.id'), comment='处理负责人')
    due_date = Column(Date, comment='要求完成日期')

    # 解决信息
    solution = Column(Text, comment='解决方案')
    resolved_at = Column(DateTime, comment='解决时间')
    resolved_by = Column(Integer, ForeignKey('users.id'), comment='解决人')

    # 验证信息
    verified_at = Column(DateTime, comment='验证时间')
    verified_by = Column(Integer, ForeignKey('users.id'), comment='验证人')
    verified_result = Column(String(20), comment='验证结果')

    # 是否阻塞验收
    is_blocking = Column(Boolean, default=False, comment='是否阻塞验收通过')

    # 附件
    attachments = Column(JSON, comment='附件列表')

    # 关系
    order = relationship('AcceptanceOrder', back_populates='issues')
    follow_ups = relationship('IssueFollowUp', back_populates='issue', lazy='dynamic')

    __table_args__ = (
        Index('idx_issue_order', 'order_id'),
        Index('idx_issue_status', 'status'),
        Index('idx_issue_severity', 'severity'),
        Index('idx_issue_assigned', 'assigned_to'),
    )

    def __repr__(self):
        return f'<AcceptanceIssue {self.issue_no}>'


class IssueFollowUp(Base, TimestampMixin):
    """问题跟进记录表"""
    __tablename__ = 'issue_follow_ups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(Integer, ForeignKey('acceptance_issues.id'), nullable=False, comment='问题ID')
    action_type = Column(String(20), nullable=False, comment='操作类型')
    action_content = Column(Text, nullable=False, comment='操作内容')
    old_value = Column(String(100), comment='原值')
    new_value = Column(String(100), comment='新值')
    attachments = Column(JSON, comment='附件')
    created_by = Column(Integer, ForeignKey('users.id'), comment='操作人')

    # 关系
    issue = relationship('AcceptanceIssue', back_populates='follow_ups')

    __table_args__ = (
        Index('idx_follow_up_issue', 'issue_id'),
    )


class AcceptanceSignature(Base, TimestampMixin):
    """验收签字记录表"""
    __tablename__ = 'acceptance_signatures'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('acceptance_orders.id'), nullable=False, comment='验收单ID')
    signer_type = Column(String(20), nullable=False, comment='签字人类型')
    signer_role = Column(String(50), comment='签字人角色')
    signer_name = Column(String(100), nullable=False, comment='签字人姓名')
    signer_user_id = Column(Integer, ForeignKey('users.id'), comment='系统用户ID')
    signer_company = Column(String(200), comment='签字人公司')
    signature_data = Column(Text, comment='电子签名数据')
    signed_at = Column(DateTime, comment='签字时间')
    ip_address = Column(String(50), comment='签字IP')
    device_info = Column(String(200), comment='设备信息')

    # 关系
    order = relationship('AcceptanceOrder', back_populates='signatures')

    __table_args__ = (
        Index('idx_signature_order', 'order_id'),
    )


class AcceptanceReport(Base, TimestampMixin):
    """验收报告表"""
    __tablename__ = 'acceptance_reports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('acceptance_orders.id'), nullable=False, comment='验收单ID')
    report_no = Column(String(50), unique=True, nullable=False, comment='报告编号')
    report_type = Column(String(20), nullable=False, comment='报告类型')
    version = Column(Integer, default=1, comment='版本号')

    # 报告内容
    report_content = Column(Text, comment='报告正文')

    # 文件信息
    file_path = Column(String(500), comment='PDF文件路径')
    file_size = Column(Integer, comment='文件大小')
    file_hash = Column(String(64), comment='文件哈希')

    generated_at = Column(DateTime, comment='生成时间')
    generated_by = Column(Integer, ForeignKey('users.id'), comment='生成人')

    # 关系
    order = relationship('AcceptanceOrder', back_populates='reports')

    __table_args__ = (
        Index('idx_report_order', 'order_id'),
    )

    def __repr__(self):
        return f'<AcceptanceReport {self.report_no}>'
