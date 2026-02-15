# -*- coding: utf-8 -*-
"""
进度预警模型
基于规则引擎生成的进度风险预警
"""
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ProgressAlert(Base, TimestampMixin):
    """进度预警"""
    __tablename__ = 'progress_alert'
    __table_args__ = (
        Index('idx_prog_alert_work_order', 'work_order_id'),
        Index('idx_prog_alert_workstation', 'workstation_id'),
        Index('idx_prog_alert_level', 'alert_level'),
        Index('idx_prog_alert_status', 'status'),
        Index('idx_prog_alert_type', 'alert_type'),
        Index('idx_prog_alert_triggered', 'triggered_at'),
        {'extend_existing': True, 'comment': '进度预警表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 预警关联
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=False, comment='工单ID')
    workstation_id = Column(Integer, ForeignKey('workstation.id'), comment='工位ID')
    
    # 预警信息
    alert_type = Column(String(50), nullable=False, 
                       comment='预警类型：DELAY/BOTTLENECK/QUALITY/EFFICIENCY/CAPACITY')
    alert_level = Column(String(20), nullable=False, default='WARNING', 
                        comment='预警级别：INFO/WARNING/CRITICAL/URGENT')
    alert_title = Column(String(200), nullable=False, comment='预警标题')
    alert_message = Column(Text, nullable=False, comment='预警内容')
    
    # 预警指标
    current_value = Column(Numeric(10, 2), comment='当前值')
    threshold_value = Column(Numeric(10, 2), comment='阈值')
    deviation_value = Column(Numeric(10, 2), comment='偏差值')
    
    # 预警状态
    status = Column(String(20), nullable=False, default='ACTIVE', 
                   comment='状态：ACTIVE/ACKNOWLEDGED/RESOLVED/DISMISSED')
    triggered_at = Column(DateTime, nullable=False, comment='触发时间')
    acknowledged_at = Column(DateTime, comment='确认时间')
    acknowledged_by = Column(Integer, ForeignKey('users.id'), comment='确认人ID')
    resolved_at = Column(DateTime, comment='解决时间')
    resolved_by = Column(Integer, ForeignKey('users.id'), comment='解决人ID')
    dismissed_at = Column(DateTime, comment='关闭时间')
    dismissed_by = Column(Integer, ForeignKey('users.id'), comment='关闭人ID')
    
    # 处理信息
    action_taken = Column(Text, comment='已采取措施')
    resolution_note = Column(Text, comment='解决说明')
    
    # 预警规则
    rule_code = Column(String(50), comment='触发规则编码')
    rule_name = Column(String(200), comment='触发规则名称')
    
    # 关系
    work_order = relationship('WorkOrder', backref='progress_alerts')
    workstation = relationship('Workstation', backref='progress_alerts')
    acknowledger = relationship('User', foreign_keys=[acknowledged_by])
    resolver = relationship('User', foreign_keys=[resolved_by])
    dismisser = relationship('User', foreign_keys=[dismissed_by])

    def __repr__(self):
        return f"<ProgressAlert {self.alert_type} level={self.alert_level} work_order_id={self.work_order_id}>"
