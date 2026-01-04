# -*- coding: utf-8 -*-
"""
报表中心模块 ORM 模型
包含：报表模板、报表定义、报表生成记录、报表订阅、数据导入导出
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime,
    Numeric, ForeignKey, Index, JSON, LargeBinary
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from enum import Enum


# ==================== 枚举定义 ====================

class ReportTypeEnum(str, Enum):
    """报表类型"""
    PROJECT_WEEKLY = 'PROJECT_WEEKLY'    # 项目周报
    PROJECT_MONTHLY = 'PROJECT_MONTHLY'  # 项目月报
    DEPT_WEEKLY = 'DEPT_WEEKLY'          # 部门周报
    DEPT_MONTHLY = 'DEPT_MONTHLY'        # 部门月报
    COMPANY_MONTHLY = 'COMPANY_MONTHLY'  # 公司月报
    COST_ANALYSIS = 'COST_ANALYSIS'      # 成本分析
    WORKLOAD_ANALYSIS = 'WORKLOAD_ANALYSIS'  # 负荷分析
    RISK_REPORT = 'RISK_REPORT'          # 风险报告
    CUSTOM = 'CUSTOM'                    # 自定义报表


class ReportPeriodEnum(str, Enum):
    """报表周期"""
    DAILY = 'DAILY'        # 日
    WEEKLY = 'WEEKLY'      # 周
    MONTHLY = 'MONTHLY'    # 月
    QUARTERLY = 'QUARTERLY'  # 季度
    YEARLY = 'YEARLY'      # 年度
    CUSTOM = 'CUSTOM'      # 自定义


class ExportFormatEnum(str, Enum):
    """导出格式"""
    XLSX = 'XLSX'  # Excel
    PDF = 'PDF'    # PDF
    HTML = 'HTML'  # HTML
    CSV = 'CSV'    # CSV
    JSON = 'JSON'  # JSON


class ImportStatusEnum(str, Enum):
    """导入状态"""
    PENDING = 'PENDING'        # 待处理
    VALIDATING = 'VALIDATING'  # 校验中
    VALIDATED = 'VALIDATED'    # 校验通过
    IMPORTING = 'IMPORTING'    # 导入中
    COMPLETED = 'COMPLETED'    # 已完成
    FAILED = 'FAILED'          # 失败
    PARTIAL = 'PARTIAL'        # 部分成功


# ==================== 报表模板 ====================

class ReportTemplate(Base, TimestampMixin):
    """报表模板"""
    __tablename__ = 'report_template'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    template_code = Column(String(50), unique=True, nullable=False, comment='模板编码')
    template_name = Column(String(100), nullable=False, comment='模板名称')
    report_type = Column(String(30), nullable=False, comment='报表类型')
    
    # 描述
    description = Column(Text, comment='模板描述')
    
    # 内容配置
    sections = Column(JSON, comment='模块配置(JSON)')
    metrics_config = Column(JSON, comment='指标配置(JSON)')
    charts_config = Column(JSON, comment='图表配置(JSON)')
    filters_config = Column(JSON, comment='筛选器配置(JSON)')
    
    # 样式配置
    style_config = Column(JSON, comment='样式配置(JSON)')
    
    # 适用角色
    default_for_roles = Column(JSON, comment='默认适用角色')
    
    # 使用统计
    use_count = Column(Integer, default=0, comment='使用次数')
    
    # 状态
    is_system = Column(Boolean, default=False, comment='是否系统内置')
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    created_by = Column(Integer, ForeignKey('user.id'), comment='创建人ID')
    
    __table_args__ = (
        Index('idx_rpt_tpl_code', 'template_code'),
        Index('idx_rpt_tpl_type', 'report_type'),
        {'comment': '报表模板表'}
    )


# ==================== 报表定义 ====================

class ReportDefinition(Base, TimestampMixin):
    """报表定义（用户自定义报表）"""
    __tablename__ = 'report_definition'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_code = Column(String(50), unique=True, nullable=False, comment='报表编码')
    report_name = Column(String(100), nullable=False, comment='报表名称')
    
    # 基于模板
    template_id = Column(Integer, ForeignKey('report_template.id'), comment='模板ID')
    
    # 报表配置
    report_type = Column(String(30), nullable=False, comment='报表类型')
    period_type = Column(String(20), default='MONTHLY', comment='周期类型')
    
    # 数据范围
    scope_type = Column(String(20), comment='范围类型:PROJECT/DEPARTMENT/COMPANY')
    scope_ids = Column(JSON, comment='范围ID列表')
    
    # 过滤条件
    filters = Column(JSON, comment='过滤条件(JSON)')
    
    # 内容配置
    sections = Column(JSON, comment='模块配置(JSON)')
    metrics = Column(JSON, comment='指标配置(JSON)')
    
    # 所有者
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False, comment='所有者ID')
    owner_name = Column(String(50), comment='所有者')
    
    # 共享设置
    is_shared = Column(Boolean, default=False, comment='是否共享')
    shared_to = Column(JSON, comment='共享给(用户/角色/部门)')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    __table_args__ = (
        Index('idx_rpt_def_code', 'report_code'),
        Index('idx_rpt_def_owner', 'owner_id'),
        Index('idx_rpt_def_type', 'report_type'),
        {'comment': '报表定义表'}
    )


# ==================== 报表生成记录 ====================

class ReportGeneration(Base, TimestampMixin):
    """报表生成记录"""
    __tablename__ = 'report_generation'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 报表信息
    report_definition_id = Column(Integer, ForeignKey('report_definition.id'), comment='报表定义ID')
    template_id = Column(Integer, ForeignKey('report_template.id'), comment='模板ID')
    report_type = Column(String(30), nullable=False, comment='报表类型')
    
    # 生成参数
    report_title = Column(String(200), comment='报表标题')
    period_type = Column(String(20), comment='周期类型')
    period_start = Column(Date, comment='周期开始')
    period_end = Column(Date, comment='周期结束')
    scope_type = Column(String(20), comment='范围类型')
    scope_id = Column(Integer, comment='范围ID')
    
    # 查看角色
    viewer_role = Column(String(50), comment='查看角色')
    
    # 生成结果
    report_data = Column(JSON, comment='报表数据(JSON)')
    
    # 状态
    status = Column(String(20), default='GENERATED', comment='状态')
    
    # 生成人
    generated_by = Column(Integer, ForeignKey('user.id'), comment='生成人ID')
    generated_at = Column(DateTime, default=datetime.now, comment='生成时间')
    
    # 导出记录
    export_format = Column(String(10), comment='导出格式')
    export_path = Column(String(500), comment='导出路径')
    exported_at = Column(DateTime, comment='导出时间')
    
    __table_args__ = (
        Index('idx_rpt_gen_definition', 'report_definition_id'),
        Index('idx_rpt_gen_type', 'report_type'),
        Index('idx_rpt_gen_time', 'generated_at'),
        {'comment': '报表生成记录表'}
    )


# ==================== 报表订阅 ====================

class ReportSubscription(Base, TimestampMixin):
    """报表订阅"""
    __tablename__ = 'report_subscription'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 订阅人
    subscriber_id = Column(Integer, ForeignKey('user.id'), nullable=False, comment='订阅人ID')
    subscriber_name = Column(String(50), comment='订阅人')
    
    # 报表
    report_definition_id = Column(Integer, ForeignKey('report_definition.id'), comment='报表定义ID')
    template_id = Column(Integer, ForeignKey('report_template.id'), comment='模板ID')
    report_type = Column(String(30), nullable=False, comment='报表类型')
    
    # 范围
    scope_type = Column(String(20), comment='范围类型')
    scope_id = Column(Integer, comment='范围ID')
    
    # 订阅频率
    frequency = Column(String(20), nullable=False, comment='频率:DAILY/WEEKLY/MONTHLY')
    send_day = Column(Integer, comment='发送日(周几或几号)')
    send_time = Column(String(10), default='09:00', comment='发送时间')
    
    # 发送渠道
    channels = Column(JSON, comment='发送渠道')
    email = Column(String(100), comment='邮箱')
    
    # 导出格式
    export_format = Column(String(10), default='PDF', comment='导出格式')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    last_sent_at = Column(DateTime, comment='上次发送时间')
    next_send_at = Column(DateTime, comment='下次发送时间')
    
    __table_args__ = (
        Index('idx_subscription_user', 'subscriber_id'),
        Index('idx_subscription_type', 'report_type'),
        {'comment': '报表订阅表'}
    )


# ==================== 数据导入任务 ====================

class DataImportTask(Base, TimestampMixin):
    """数据导入任务"""
    __tablename__ = 'data_import_task'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    task_no = Column(String(50), unique=True, nullable=False, comment='任务编号')
    
    # 导入类型
    import_type = Column(String(50), nullable=False, comment='导入类型')
    target_table = Column(String(100), comment='目标表')
    
    # 文件信息
    file_name = Column(String(200), nullable=False, comment='文件名')
    file_path = Column(String(500), comment='文件路径')
    file_size = Column(Integer, comment='文件大小')
    
    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    
    # 统计
    total_rows = Column(Integer, default=0, comment='总行数')
    success_rows = Column(Integer, default=0, comment='成功行数')
    failed_rows = Column(Integer, default=0, comment='失败行数')
    skipped_rows = Column(Integer, default=0, comment='跳过行数')
    
    # 校验结果
    validation_errors = Column(JSON, comment='校验错误(JSON)')
    
    # 导入人
    imported_by = Column(Integer, ForeignKey('user.id'), nullable=False, comment='导入人ID')
    
    # 时间
    started_at = Column(DateTime, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')
    
    # 错误信息
    error_message = Column(Text, comment='错误信息')
    error_log_path = Column(String(500), comment='错误日志路径')
    
    __table_args__ = (
        Index('idx_import_task_no', 'task_no'),
        Index('idx_import_type', 'import_type'),
        Index('idx_import_status', 'status'),
        Index('idx_import_user', 'imported_by'),
        {'comment': '数据导入任务表'}
    )


# ==================== 数据导出任务 ====================

class DataExportTask(Base, TimestampMixin):
    """数据导出任务"""
    __tablename__ = 'data_export_task'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    task_no = Column(String(50), unique=True, nullable=False, comment='任务编号')
    
    # 导出类型
    export_type = Column(String(50), nullable=False, comment='导出类型')
    export_format = Column(String(10), default='XLSX', comment='导出格式')
    
    # 查询条件
    query_params = Column(JSON, comment='查询参数(JSON)')
    
    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    
    # 结果
    file_name = Column(String(200), comment='文件名')
    file_path = Column(String(500), comment='文件路径')
    file_size = Column(Integer, comment='文件大小')
    total_rows = Column(Integer, default=0, comment='总行数')
    
    # 导出人
    exported_by = Column(Integer, ForeignKey('user.id'), nullable=False, comment='导出人ID')
    
    # 时间
    started_at = Column(DateTime, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')
    expires_at = Column(DateTime, comment='过期时间')
    
    # 下载统计
    download_count = Column(Integer, default=0, comment='下载次数')
    last_download_at = Column(DateTime, comment='最后下载时间')
    
    # 错误信息
    error_message = Column(Text, comment='错误信息')
    
    __table_args__ = (
        Index('idx_export_task_no', 'task_no'),
        Index('idx_export_type', 'export_type'),
        Index('idx_export_status', 'status'),
        Index('idx_export_user', 'exported_by'),
        {'comment': '数据导出任务表'}
    )


# ==================== 导入模板 ====================

class ImportTemplate(Base, TimestampMixin):
    """导入模板"""
    __tablename__ = 'import_template'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    template_code = Column(String(50), unique=True, nullable=False, comment='模板编码')
    template_name = Column(String(100), nullable=False, comment='模板名称')
    import_type = Column(String(50), nullable=False, comment='导入类型')
    
    # 模板文件
    template_file_path = Column(String(500), comment='模板文件路径')
    
    # 字段映射
    field_mappings = Column(JSON, nullable=False, comment='字段映射(JSON)')
    
    # 校验规则
    validation_rules = Column(JSON, comment='校验规则(JSON)')
    
    # 说明
    description = Column(Text, comment='说明')
    instructions = Column(Text, comment='填写说明')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    __table_args__ = (
        Index('idx_import_tpl_code', 'template_code'),
        Index('idx_import_tpl_type', 'import_type'),
        {'comment': '导入模板表'}
    )

