"""
售前AI成本估算模型
"""
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class PresaleAICostEstimation(Base):
    """AI成本估算记录表"""
    __tablename__ = "presale_ai_cost_estimation"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    presale_ticket_id = Column(Integer, nullable=False, index=True, comment="售前工单ID")
    solution_id = Column(Integer, nullable=True, comment="解决方案ID")
    
    # 成本分解
    hardware_cost = Column(DECIMAL(12, 2), nullable=True, comment="硬件成本(BOM)")
    software_cost = Column(DECIMAL(12, 2), nullable=True, comment="软件成本(开发工时)")
    installation_cost = Column(DECIMAL(12, 2), nullable=True, comment="安装调试成本")
    service_cost = Column(DECIMAL(12, 2), nullable=True, comment="售后服务成本")
    risk_reserve = Column(DECIMAL(12, 2), nullable=True, comment="风险储备金")
    total_cost = Column(DECIMAL(12, 2), nullable=False, comment="总成本")
    
    # AI分析结果
    optimization_suggestions = Column(JSON, nullable=True, comment="成本优化建议")
    pricing_recommendations = Column(JSON, nullable=True, comment="定价推荐(low/medium/high)")
    confidence_score = Column(DECIMAL(3, 2), nullable=True, comment="置信度评分(0-1)")
    
    # AI模型信息
    model_version = Column(String(50), nullable=True, comment="AI模型版本")
    input_parameters = Column(JSON, nullable=True, comment="输入参数快照")
    
    # 元数据
    created_by = Column(Integer, nullable=False, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 索引
    __table_args__ = (
        Index('idx_presale_ticket_id', 'presale_ticket_id'),
        Index('idx_cost_est_created_at', 'created_at'),
    )


class PresaleCostHistory(Base):
    """历史成本数据(用于学习)"""
    __tablename__ = "presale_cost_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, nullable=True, comment="项目ID")
    project_name = Column(String(200), nullable=True, comment="项目名称")
    
    # 成本对比
    estimated_cost = Column(DECIMAL(12, 2), nullable=False, comment="估算成本")
    actual_cost = Column(DECIMAL(12, 2), nullable=False, comment="实际成本")
    variance_rate = Column(DECIMAL(5, 2), nullable=True, comment="偏差率(%)")
    
    # 详细分解
    cost_breakdown = Column(JSON, nullable=True, comment="成本分解详情")
    variance_analysis = Column(JSON, nullable=True, comment="偏差分析详情")
    
    # 项目特征(用于机器学习)
    project_features = Column(JSON, nullable=True, comment="项目特征向量")
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 索引
    __table_args__ = (
        Index('idx_cost_hist_project', 'project_id'),
        Index('idx_cost_hist_created_at', 'created_at'),
    )


class PresaleCostOptimizationRecord(Base):
    """成本优化建议记录"""
    __tablename__ = "presale_cost_optimization_record"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    estimation_id = Column(Integer, ForeignKey('presale_ai_cost_estimation.id'), nullable=False)
    
    # 优化建议
    optimization_type = Column(String(50), nullable=False, comment="优化类型(hardware/software/installation/service)")
    original_cost = Column(DECIMAL(12, 2), nullable=False, comment="原始成本")
    optimized_cost = Column(DECIMAL(12, 2), nullable=False, comment="优化后成本")
    saving_amount = Column(DECIMAL(12, 2), nullable=False, comment="节省金额")
    saving_rate = Column(DECIMAL(5, 2), nullable=False, comment="节省比例(%)")
    
    # 建议详情
    suggestion_detail = Column(JSON, nullable=True, comment="优化建议详情")
    alternative_solutions = Column(JSON, nullable=True, comment="替代方案")
    
    # 可行性评估
    feasibility_score = Column(DECIMAL(3, 2), nullable=True, comment="可行性评分(0-1)")
    risk_assessment = Column(Text, nullable=True, comment="风险评估")
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # 关系
    estimation = relationship("PresaleAICostEstimation", backref="optimization_records")
