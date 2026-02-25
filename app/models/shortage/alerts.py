# -*- coding: utf-8 -*-
"""
缺料管理 - 预警与统计模型

注意: ShortageAlert 类已废弃，缺料预警现使用统一的 AlertRecord 模型
通过 AlertRecord.target_type='SHORTAGE' 筛选缺料预警
详见: docs/plans/2026-01-21-alert-system-consolidation-design.md
"""
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class AlertHandleLog(Base, TimestampMixin):
    """预警处理日志表
    
    【状态】未启用 - 告警处理日志"""
    __tablename__ = 'mat_alert_log'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    alert_id = Column(Integer, nullable=False, comment='预警ID')

    # 操作信息
    action_type = Column(String(20), nullable=False, comment='操作类型：create/handle/update/escalate/resolve/close')
    action_description = Column(Text, comment='操作描述')

    # 操作人
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='操作人ID')
    operator_name = Column(String(50), comment='操作人姓名')
    action_time = Column(DateTime, nullable=False, default=datetime.now, comment='操作时间')

    # 操作前后状态
    before_status = Column(String(20), comment='操作前状态')
    after_status = Column(String(20), comment='操作后状态')
    before_level = Column(String(20), comment='操作前级别')
    after_level = Column(String(20), comment='操作后级别')

    # 扩展数据
    extra_data = Column(JSON, comment='扩展数据JSON')

    # 关系
    operator = relationship('User')

    __table_args__ = (
        Index('idx_alert_log_alert', 'alert_id'),
        Index('idx_alert_log_time', 'action_time'),
        Index('idx_alert_log_operator', 'operator_id'),
        {'comment': '预警处理日志表'}
    )


class ShortageDailyReport(Base, TimestampMixin):
    """缺料统计日报表"""
    __tablename__ = 'mat_shortage_daily_report'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_date = Column(Date, unique=True, nullable=False, comment='报告日期')

    # 预警统计
    new_alerts = Column(Integer, default=0, comment='新增预警数')
    resolved_alerts = Column(Integer, default=0, comment='已解决预警数')
    pending_alerts = Column(Integer, default=0, comment='待处理预警数')
    overdue_alerts = Column(Integer, default=0, comment='逾期预警数')
    level1_count = Column(Integer, default=0, comment='一级预警数')
    level2_count = Column(Integer, default=0, comment='二级预警数')
    level3_count = Column(Integer, default=0, comment='三级预警数')
    level4_count = Column(Integer, default=0, comment='四级预警数')

    # 上报统计
    new_reports = Column(Integer, default=0, comment='新增上报数')
    resolved_reports = Column(Integer, default=0, comment='已解决上报数')

    # 工单统计
    total_work_orders = Column(Integer, default=0, comment='总工单数')
    kit_complete_count = Column(Integer, default=0, comment='齐套完成工单数')
    kit_rate = Column(Numeric(5, 2), default=0, comment='平均齐套率')

    # 到货统计
    expected_arrivals = Column(Integer, default=0, comment='预期到货数')
    actual_arrivals = Column(Integer, default=0, comment='实际到货数')
    delayed_arrivals = Column(Integer, default=0, comment='延迟到货数')
    on_time_rate = Column(Numeric(5, 2), default=0, comment='准时到货率')

    # 响应时效
    avg_response_minutes = Column(Integer, default=0, comment='平均响应时间(分钟)')
    avg_resolve_hours = Column(Numeric(5, 2), default=0, comment='平均解决时间(小时)')

    # 停工统计
    stoppage_count = Column(Integer, default=0, comment='停工次数')
    stoppage_hours = Column(Numeric(8, 2), default=0, comment='停工时长(小时)')

    __table_args__ = (
        Index('idx_daily_report_date', 'report_date'),
        {'comment': '缺料统计日报表'}
    )


# ============================================================
# ShortageAlert 类已废弃 (2026-01-21)
# ============================================================
# 原因: 缺料预警已合并到统一的 AlertRecord 表
# 迁移方式: AlertRecord.target_type='SHORTAGE'
# 字段映射:
#   - material_id → AlertRecord.target_id
#   - material_code → AlertRecord.target_no
#   - material_name → AlertRecord.target_name
#   - handle_start_time → AlertRecord.handle_start_at
#   - resolve_time → AlertRecord.handle_end_at
#   - 其他业务字段 → AlertRecord.alert_data (JSON)
#
# 如需使用缺料预警功能，请使用:
#   from app.models.alert import AlertRecord
#   db.query(AlertRecord).filter(AlertRecord.target_type == 'SHORTAGE')
# ============================================================

# 向后兼容别名
from app.models.shortage.smart_alert import ShortageAlert  # noqa: F401
