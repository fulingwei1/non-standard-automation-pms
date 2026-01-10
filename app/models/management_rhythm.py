# -*- coding: utf-8 -*-
"""
管理节律数据模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime, ForeignKey, JSON, Index, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    MeetingRhythmLevel,
    MeetingCycleType,
    ActionItemStatus,
    RhythmHealthStatus,
)


# ==================== 管理节律配置 ====================

class ManagementRhythmConfig(Base, TimestampMixin):
    """管理节律配置表"""
    __tablename__ = 'management_rhythm_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 节律信息
    rhythm_level = Column(String(20), nullable=False, comment='节律层级:STRATEGIC/OPERATIONAL/OPERATION/TASK')
    cycle_type = Column(String(20), nullable=False, comment='周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY')
    config_name = Column(String(200), nullable=False, comment='配置名称')
    description = Column(Text, comment='配置描述')
    
    # 会议模板配置(JSON)
    meeting_template = Column(JSON, comment='会议模板配置')
    # 示例结构:
    # {
    #   "agenda_template": ["议题1", "议题2", "议题3"],
    #   "required_metrics": ["指标1", "指标2"],
    #   "output_artifacts": ["战略地图", "平衡计分卡"],
    #   "decision_framework": "四问四不做",
    #   "duration_minutes": 120
    # }
    
    # 关键指标清单(JSON)
    key_metrics = Column(JSON, comment='关键指标清单')
    # 示例结构:
    # [
    #   {"name": "收入", "type": "financial", "target": 1000},
    #   {"name": "利润率", "type": "financial", "target": 0.15}
    # ]
    
    # 输出成果清单(JSON)
    output_artifacts = Column(JSON, comment='输出成果清单')
    # 示例结构:
    # ["战略地图", "平衡计分卡", "OGSMT", "组织三图三表"]
    
    # 状态
    is_active = Column(String(10), default='ACTIVE', comment='是否启用:ACTIVE/INACTIVE')
    
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    __table_args__ = (
        Index('idx_rhythm_config_level_cycle', 'rhythm_level', 'cycle_type'),
        {'comment': '管理节律配置表'}
    )


# ==================== 战略会议 ====================

class StrategicMeeting(Base, TimestampMixin):
    """战略会议表（扩展自PmoMeeting概念）"""
    __tablename__ = 'strategic_meeting'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID(可为空表示跨项目会议)')
    related_project_ids = Column(JSON, comment='关联项目ID列表（JSON数组，支持多项目关联）')
    rhythm_config_id = Column(Integer, ForeignKey('management_rhythm_config.id'), comment='节律配置ID')
    
    # 会议信息
    rhythm_level = Column(String(20), nullable=False, comment='会议层级:STRATEGIC/OPERATIONAL/OPERATION/TASK')
    cycle_type = Column(String(20), nullable=False, comment='周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY')
    meeting_name = Column(String(200), nullable=False, comment='会议名称')
    meeting_type = Column(String(50), comment='会议类型(如:战略研讨会/经营分析会/运营例会/日清会)')
    
    # 时间地点
    meeting_date = Column(Date, nullable=False, comment='会议日期')
    start_time = Column(Time, comment='开始时间')
    end_time = Column(Time, comment='结束时间')
    location = Column(String(100), comment='会议地点')
    
    # 人员
    organizer_id = Column(Integer, ForeignKey('users.id'), comment='组织者ID')
    organizer_name = Column(String(50), comment='组织者')
    attendees = Column(JSON, comment='参会人员')
    # 示例结构: [{"user_id": 1, "name": "张三", "role": "主持人"}]
    
    # 内容
    agenda = Column(Text, comment='会议议程')
    minutes = Column(Text, comment='会议纪要')
    decisions = Column(Text, comment='会议决议')
    
    # 战略相关(JSON)
    strategic_context = Column(JSON, comment='战略背景')
    # 示例结构:
    # {
    #   "strategic_period": "中周期(3-5年)",
    #   "focus_areas": ["新业务孵化", "老业务收缩"],
    #   "key_questions": ["四问四不做"]
    # }
    
    # 五层战略结构(JSON) - 核心战略框架
    strategic_structure = Column(JSON, comment='五层战略结构:愿景/机会/定位/目标/路径')
    # 示例结构:
    # {
    #   "vision": {
    #     "mission": "我们希望通过____，让____变得更好",
    #     "vision": "最终成为一家怎样的公司",
    #     "why_exist": "存在的意义",
    #     "three_years_later": "三年后希望被怎么记住",
    #     "long_term_value": "为谁创造长期价值"
    #   },
    #   "opportunity": {
    #     "market_trend": "未来三年的行业关键趋势",
    #     "customer_demand": "客户需求本质",
    #     "competitive_gap": "竞争空位",
    #     "our_advantage": "我们的优势",
    #     "four_in_one": "四点合一分析(行业增长/竞争空隙/客户需求/自身优势)",
    #     "why_we_win": "凭什么能赢的逻辑"
    #   },
    #   "positioning": {
    #     "market_segment": "聚焦的赛道/细分市场",
    #     "differentiation": "差异化方式",
    #     "target_customers": "核心客户群体",
    #     "value_proposition": "独特价值主张",
    #     "competitive_barrier": "竞争壁垒"
    #   },
    #   "goals": {
    #     "strategic_hypothesis": "战略假设",
    #     "key_metrics": [
    #       {"name": "指标名", "target": "目标值", "purpose": "验证目的"}
    #     ],
    #     "annual_goals": "年度目标",
    #     "quarterly_goals": "季度目标",
    #     "monthly_goals": "月度目标"
    #   },
    #   "path": {
    #     "value_chain": "价值流路径(客户需求→产品方案→交付体验→复购机制)",
    #     "customer_need_essence": "客户需求本质",
    #     "product_solution": "产品方案",
    #     "service_experience": "服务体验",
    #     "repurchase_mechanism": "复购机制",
    #     "execution_order": "执行次序",
    #     "rhythm": "节奏(周执行/月验证/季校准/年复盘)",
    #     "resources": "兵力投入",
    #     "campaigns": "战役系统"
    #   }
    # }
    
    key_decisions = Column(JSON, comment='关键决策')
    # 示例结构:
    # [
    #   {"decision": "决策内容", "maker": "决策人", "date": "2025-01-15"}
    # ]
    
    resource_allocation = Column(JSON, comment='资源分配')
    # 示例结构:
    # {
    #   "budget_adjustment": 100000,
    #   "resource_reallocation": ["从A项目调拨到B项目"]
    # }
    
    # 指标快照(JSON)
    metrics_snapshot = Column(JSON, comment='指标快照')
    # 示例结构:
    # {
    #   "revenue": {"actual": 950, "target": 1000, "gap": -50},
    #   "profit_rate": {"actual": 0.14, "target": 0.15, "gap": -0.01}
    # }
    
    # 附件
    attachments = Column(JSON, comment='会议附件')
    
    # 状态
    status = Column(String(20), default='SCHEDULED', comment='状态:SCHEDULED/ONGOING/COMPLETED/CANCELLED')
    
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    # 关系
    action_items = relationship("MeetingActionItem", back_populates="meeting", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_strategic_meeting_level', 'rhythm_level'),
        Index('idx_strategic_meeting_cycle', 'cycle_type'),
        Index('idx_strategic_meeting_date', 'meeting_date'),
        Index('idx_strategic_meeting_project', 'project_id'),
        {'comment': '战略会议表'}
    )


# ==================== 会议行动项 ====================

class MeetingActionItem(Base, TimestampMixin):
    """会议行动项跟踪表"""
    __tablename__ = 'meeting_action_item'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    meeting_id = Column(Integer, ForeignKey('strategic_meeting.id', ondelete='CASCADE'), nullable=False, comment='会议ID')
    
    # 行动项信息
    action_description = Column(Text, nullable=False, comment='行动描述')
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='责任人ID')
    owner_name = Column(String(50), comment='责任人姓名')
    
    # 时间
    due_date = Column(Date, nullable=False, comment='截止日期')
    completed_date = Column(Date, comment='完成日期')
    
    # 状态
    status = Column(String(20), default='PENDING', comment='状态:PENDING/IN_PROGRESS/COMPLETED/OVERDUE')
    
    # 完成说明
    completion_notes = Column(Text, comment='完成说明')
    
    # 优先级
    priority = Column(String(20), default='NORMAL', comment='优先级:LOW/NORMAL/HIGH/URGENT')
    
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    # 关系
    meeting = relationship("StrategicMeeting", back_populates="action_items")
    
    __table_args__ = (
        Index('idx_action_item_meeting', 'meeting_id'),
        Index('idx_action_item_owner', 'owner_id'),
        Index('idx_action_item_status', 'status'),
        Index('idx_action_item_due_date', 'due_date'),
        {'comment': '会议行动项跟踪表'}
    )


# ==================== 节律仪表盘快照 ====================

class RhythmDashboardSnapshot(Base, TimestampMixin):
    """节律仪表盘快照表"""
    __tablename__ = 'rhythm_dashboard_snapshot'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 节律信息
    rhythm_level = Column(String(20), nullable=False, comment='节律层级:STRATEGIC/OPERATIONAL/OPERATION/TASK')
    cycle_type = Column(String(20), nullable=False, comment='周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY')
    current_cycle = Column(String(50), comment='当前周期(如:2025-Q1/2025-01/2025-W03/2025-01-15)')
    
    # 指标快照(JSON)
    key_metrics_snapshot = Column(JSON, comment='关键指标快照')
    # 示例结构:
    # {
    #   "revenue": {"actual": 950, "target": 1000, "gap": -50, "gap_percent": -5.0},
    #   "profit_rate": {"actual": 0.14, "target": 0.15, "gap": -0.01, "gap_percent": -6.67}
    # }
    
    # 健康状态
    health_status = Column(String(20), default='GREEN', comment='健康状态:GREEN/YELLOW/RED')
    
    # 会议信息
    last_meeting_date = Column(Date, comment='上次会议日期')
    next_meeting_date = Column(Date, comment='下次会议日期')
    meetings_count = Column(Integer, default=0, comment='本周期会议数量')
    completed_meetings_count = Column(Integer, default=0, comment='已完成会议数量')
    
    # 行动项统计
    total_action_items = Column(Integer, default=0, comment='总行动项数')
    completed_action_items = Column(Integer, default=0, comment='已完成行动项数')
    overdue_action_items = Column(Integer, default=0, comment='逾期行动项数')
    completion_rate = Column(String(10), comment='完成率(百分比)')
    
    # 快照时间
    snapshot_date = Column(Date, nullable=False, comment='快照日期')
    
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    __table_args__ = (
        Index('idx_dashboard_snapshot_level_cycle', 'rhythm_level', 'cycle_type'),
        Index('idx_dashboard_snapshot_date', 'snapshot_date'),
        {'comment': '节律仪表盘快照表'}
    )


# ==================== 会议报告 ====================

class MeetingReport(Base, TimestampMixin):
    """会议报告表"""
    __tablename__ = 'meeting_report'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 报告信息
    report_no = Column(String(50), unique=True, nullable=False, comment='报告编号')
    report_type = Column(String(20), nullable=False, comment='报告类型:ANNUAL/MONTHLY')
    report_title = Column(String(200), nullable=False, comment='报告标题')
    
    # 周期信息
    period_year = Column(Integer, nullable=False, comment='报告年份')
    period_month = Column(Integer, comment='报告月份（月度报告）')
    period_start = Column(Date, nullable=False, comment='周期开始日期')
    period_end = Column(Date, nullable=False, comment='周期结束日期')
    
    # 节律层级
    rhythm_level = Column(String(20), nullable=False, comment='节律层级:STRATEGIC/OPERATIONAL/OPERATION/TASK')
    
    # 报告数据(JSON)
    report_data = Column(JSON, comment='报告数据(JSON)')
    # 示例结构:
    # {
    #   "summary": {
    #     "total_meetings": 10,
    #     "completed_meetings": 8,
    #     "total_action_items": 50,
    #     "completed_action_items": 45,
    #     "completion_rate": "90%"
    #   },
    #   "meetings": [...],
    #   "action_items": [...],
    #   "key_decisions": [...],
    #   "strategic_structure": {...}
    # }
    
    # 对比数据(JSON) - 仅月度报告
    comparison_data = Column(JSON, comment='对比数据(JSON)，与上月对比')
    # 示例结构:
    # {
    #   "previous_period": "2025-01",
    #   "meetings_comparison": {
    #     "current": 8,
    #     "previous": 6,
    #     "change": "+2",
    #     "change_rate": "+33.3%"
    #   },
    #   "action_items_comparison": {...},
    #   "completion_rate_comparison": {...}
    # }
    
    # 文件路径
    file_path = Column(String(500), comment='报告文件路径（PDF/Excel）')
    file_size = Column(Integer, comment='文件大小（字节）')
    
    # 状态
    status = Column(String(20), default='GENERATED', comment='状态:GENERATED/PUBLISHED/ARCHIVED')
    
    # 生成信息
    generated_by = Column(Integer, ForeignKey('users.id'), comment='生成人ID')
    generated_at = Column(DateTime, default=datetime.now, comment='生成时间')
    published_at = Column(DateTime, comment='发布时间')
    
    __table_args__ = (
        Index('idx_meeting_report_type', 'report_type'),
        Index('idx_meeting_report_period', 'period_year', 'period_month'),
        Index('idx_meeting_report_level', 'rhythm_level'),
        Index('idx_meeting_report_date', 'period_start', 'period_end'),
        {'comment': '会议报告表'}
    )


# ==================== 报告配置 ====================

class MeetingReportConfig(Base, TimestampMixin):
    """会议报告配置表（管理部可配置）"""
    __tablename__ = 'meeting_report_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 配置信息
    config_name = Column(String(200), nullable=False, comment='配置名称')
    report_type = Column(String(20), nullable=False, comment='报告类型:ANNUAL/MONTHLY')
    description = Column(Text, comment='配置描述')
    
    # 指标配置(JSON) - 启用的指标列表
    enabled_metrics = Column(JSON, comment='启用的指标配置')
    # 示例结构:
    # [
    #   {
    #     "category": "项目管理",
    #     "metric_code": "project_total",
    #     "metric_name": "项目总数",
    #     "data_source": "Project",
    #     "calculation": "COUNT",
    #     "enabled": true,
    #     "show_in_summary": true,
    #     "show_in_detail": true,
    #     "show_comparison": true,
    #     "comparison_type": ["环比", "同比"],
    #     "display_order": 1
    #   }
    # ]
    
    # 对比配置(JSON)
    comparison_config = Column(JSON, comment='对比配置')
    # 示例结构:
    # {
    #   "enable_mom": true,  # 启用环比
    #   "enable_yoy": true,  # 启用同比
    #   "comparison_periods": ["previous_month", "same_month_last_year"],
    #   "highlight_threshold": {
    #     "increase_threshold": 10,  # 增长超过10%高亮
    #     "decrease_threshold": -10   # 下降超过10%高亮
    #   }
    # }
    
    # 显示配置(JSON)
    display_config = Column(JSON, comment='显示配置')
    # 示例结构:
    # {
    #   "sections": [
    #     {"name": "执行摘要", "enabled": true, "order": 1},
    #     {"name": "项目管理", "enabled": true, "order": 2},
    #     {"name": "销售管理", "enabled": true, "order": 3},
    #     ...
    #   ],
    #   "chart_types": {
    #     "trend_chart": true,
    #     "comparison_chart": true,
    #     "distribution_chart": true
    #   }
    # }
    
    # 状态
    is_default = Column(Boolean, default=False, comment='是否默认配置')
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    __table_args__ = (
        Index('idx_report_config_type', 'report_type'),
        Index('idx_report_config_default', 'is_default'),
        {'comment': '会议报告配置表'}
    )


# ==================== 报告指标定义 ====================

class ReportMetricDefinition(Base, TimestampMixin):
    """报告指标定义表"""
    __tablename__ = 'report_metric_definition'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 指标基本信息
    metric_code = Column(String(50), unique=True, nullable=False, comment='指标编码')
    metric_name = Column(String(200), nullable=False, comment='指标名称')
    category = Column(String(50), nullable=False, comment='指标分类')
    description = Column(Text, comment='指标说明')
    
    # 数据源配置
    data_source = Column(String(50), nullable=False, comment='数据源表名')
    data_field = Column(String(100), comment='数据字段')
    filter_conditions = Column(JSON, comment='筛选条件(JSON)')
    # 示例结构:
    # {
    #   "filters": [
    #     {"field": "status", "operator": "=", "value": "ACTIVE"},
    #     {"field": "created_at", "operator": ">=", "value": "period_start"}
    #   ]
    # }
    
    # 计算方式
    calculation_type = Column(String(20), nullable=False, comment='计算类型:COUNT/SUM/AVG/MAX/MIN/RATIO/CUSTOM')
    calculation_formula = Column(Text, comment='计算公式（CUSTOM类型使用）')
    
    # 对比支持
    support_mom = Column(Boolean, default=True, comment='支持环比')
    support_yoy = Column(Boolean, default=True, comment='支持同比')
    
    # 显示配置
    unit = Column(String(20), comment='单位')
    format_type = Column(String(20), default='NUMBER', comment='格式类型:NUMBER/PERCENTAGE/CURRENCY')
    decimal_places = Column(Integer, default=2, comment='小数位数')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_system = Column(Boolean, default=False, comment='是否系统预置')
    
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    __table_args__ = (
        Index('idx_metric_code', 'metric_code'),
        Index('idx_metric_category', 'category'),
        Index('idx_metric_source', 'data_source'),
        {'comment': '报告指标定义表'}
    )
