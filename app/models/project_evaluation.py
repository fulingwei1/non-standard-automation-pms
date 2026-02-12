# -*- coding: utf-8 -*-
"""
项目评价模块 ORM 模型
包含：项目评价记录、评价维度配置
"""


from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin

# ==================== 项目评价记录 ====================

class ProjectEvaluation(Base, TimestampMixin):
    """项目评价记录表"""
    __tablename__ = 'project_evaluations'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    evaluation_code = Column(String(50), unique=True, nullable=False, comment='评价编号')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')

    # 评价维度得分（1-10分）
    novelty_score = Column(Numeric(3, 1), comment='项目新旧得分（1-10分）')
    # 1-3分：全新项目（从未做过）
    # 4-6分：类似项目（做过类似）
    # 7-9分：标准项目（做过多次）
    # 10分：完全标准项目

    new_tech_score = Column(Numeric(3, 1), comment='新技术得分（1-10分）')
    # 1-3分：大量新技术（技术风险高）
    # 4-6分：部分新技术（有一定风险）
    # 7-9分：少量新技术（风险可控）
    # 10分：无新技术（成熟技术）

    difficulty_score = Column(Numeric(3, 1), comment='项目难度得分（1-10分）')
    # 1-3分：极高难度
    # 4-6分：高难度
    # 7-8分：中等难度
    # 9-10分：低难度

    workload_score = Column(Numeric(3, 1), comment='项目工作量得分（1-10分）')
    # 1-3分：工作量极大（>1000人天）
    # 4-6分：工作量大（500-1000人天）
    # 7-8分：工作量中等（200-500人天）
    # 9-10分：工作量小（<200人天）

    amount_score = Column(Numeric(3, 1), comment='项目金额得分（1-10分）')
    # 1-3分：超大项目（>500万）
    # 4-6分：大项目（200-500万）
    # 7-8分：中等项目（50-200万）
    # 9-10分：小项目（<50万）

    # 综合评价
    total_score = Column(Numeric(5, 2), comment='综合得分（加权平均）')
    evaluation_level = Column(String(20), comment='评价等级：S/A/B/C/D')
    # S级：90-100分（战略项目/超高难度）
    # A级：80-89分（重点项目/高难度）
    # B级：70-79分（一般项目/中等难度）
    # C级：60-69分（普通项目/低难度）
    # D级：<60分（简单项目）

    # 评价详情
    evaluation_detail = Column(JSON, comment='评价详情(JSON)')
    # 例如：
    # {
    #   "novelty": {"score": 3, "reason": "全新项目，从未做过类似设备"},
    #   "new_tech": {"score": 2, "reason": "使用新的视觉算法，技术风险高"},
    #   "difficulty": {"score": 4, "reason": "精度要求高，调试难度大"},
    #   "workload": {"score": 5, "reason": "预估800人天"},
    #   "amount": {"score": 6, "reason": "合同金额350万"}
    # }

    # 权重配置（可自定义）
    weights = Column(JSON, comment='权重配置(JSON)')
    # 默认权重：
    # {
    #   "novelty": 0.15,      # 项目新旧 15%
    #   "new_tech": 0.20,     # 新技术 20%
    #   "difficulty": 0.30,   # 难度 30%
    #   "workload": 0.20,     # 工作量 20%
    #   "amount": 0.15        # 金额 15%
    # }

    # 评价人
    evaluator_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='评价人ID')
    evaluator_name = Column(String(50), comment='评价人姓名')
    evaluation_date = Column(Date, nullable=False, comment='评价日期')

    # 评价说明
    evaluation_note = Column(Text, comment='评价说明')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态：DRAFT/CONFIRMED/ARCHIVED')

    # 关系
    project = relationship('Project')
    evaluator = relationship('User', foreign_keys=[evaluator_id])

    __table_args__ = (
        Index('idx_proj_eval_code', 'evaluation_code'),
        Index('idx_proj_eval_project', 'project_id'),
        Index('idx_proj_eval_date', 'evaluation_date'),
        Index('idx_proj_eval_level', 'evaluation_level'),
        {'comment': '项目评价记录表'}
    )

    def __repr__(self):
        return f"<ProjectEvaluation {self.evaluation_code}>"


# ==================== 项目评价维度配置 ====================

class ProjectEvaluationDimension(Base, TimestampMixin):
    """项目评价维度配置表"""
    __tablename__ = 'project_evaluation_dimensions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    dimension_code = Column(String(50), unique=True, nullable=False, comment='维度编码')
    dimension_name = Column(String(100), nullable=False, comment='维度名称')
    dimension_type = Column(String(20), nullable=False, comment='维度类型')
    # NOVELTY: 项目新旧
    # NEW_TECH: 新技术
    # DIFFICULTY: 难度
    # WORKLOAD: 工作量
    # AMOUNT: 金额

    # 评分标准
    scoring_rules = Column(JSON, comment='评分规则(JSON)')
    # 例如：
    # {
    #   "ranges": [
    #     {"min": 1, "max": 3, "label": "极高", "description": "..."},
    #     {"min": 4, "max": 6, "label": "高", "description": "..."},
    #     {"min": 7, "max": 8, "label": "中", "description": "..."},
    #     {"min": 9, "max": 10, "label": "低", "description": "..."}
    #   ]
    # }

    # 默认权重
    default_weight = Column(Numeric(5, 2), comment='默认权重(%)')

    # 计算方式
    calculation_method = Column(String(20), default='MANUAL', comment='计算方式')
    # MANUAL: 手动评价
    # AUTO: 自动计算（基于项目数据）
    # HYBRID: 混合（自动计算+人工调整）

    # 自动计算规则（如果calculation_method为AUTO或HYBRID）
    auto_calculation_rule = Column(JSON, comment='自动计算规则(JSON)')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    sort_order = Column(Integer, default=0, comment='排序')

    __table_args__ = (
        Index('idx_eval_dim_code', 'dimension_code'),
        Index('idx_eval_dim_type', 'dimension_type'),
        {'comment': '项目评价维度配置表'}
    )

    def __repr__(self):
        return f"<ProjectEvaluationDimension {self.dimension_code}>"

