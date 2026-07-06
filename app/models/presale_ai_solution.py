"""
售前AI方案生成模块 - 数据模型
AI-Powered Solution Generation for Presales
"""

from datetime import datetime

from sqlalchemy import DECIMAL, JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.presale import PresaleSolutionTemplate as PresaleAISolutionTemplate


class PresaleAISolution(Base):
    """AI方案生成记录表"""

    __tablename__ = "presale_ai_solution"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    presale_ticket_id = Column(Integer, nullable=False, comment="售前工单ID")
    requirement_analysis_id = Column(
        Integer, ForeignKey("presale_ai_requirement_analysis.id"), comment="需求分析ID"
    )

    # 旧方案版本引擎已退役；保留空兼容列，避免历史库 schema 反复迁移。
    current_version_id = Column(Integer, comment="旧方案版本ID（已退役）")

    # 模板匹配结果
    matched_template_ids = Column(JSON, comment="匹配的模板ID列表 (TOP 3)")

    # 生成的方案内容
    generated_solution = Column(JSON, comment="生成的完整方案 JSON 格式")

    # 架构图 (Mermaid代码)
    architecture_diagram = Column(Text, comment="系统架构图 Mermaid 代码")
    topology_diagram = Column(Text, comment="设备拓扑图 Mermaid 代码")
    signal_flow_diagram = Column(Text, comment="信号流程图 Mermaid 代码")

    # BOM清单
    bom_list = Column(JSON, comment="BOM清单 JSON 格式")

    # 技术文档
    solution_description = Column(Text, comment="方案描述")
    technical_parameters = Column(JSON, comment="技术参数表")
    process_flow = Column(Text, comment="工艺流程说明")

    # 质量评分
    confidence_score = Column(DECIMAL(3, 2), comment="方案置信度评分 (0-1)")
    quality_score = Column(DECIMAL(3, 2), comment="方案质量评分 (0-5)")

    # 成本预估
    estimated_cost = Column(DECIMAL(12, 2), comment="预估成本")
    cost_breakdown = Column(JSON, comment="成本分解")

    # AI生成元数据
    ai_model_used = Column(String(100), comment="使用的AI模型")
    generation_time_seconds = Column(DECIMAL(6, 2), comment="生成耗时(秒)")
    prompt_tokens = Column(Integer, comment="Prompt tokens")
    completion_tokens = Column(Integer, comment="Completion tokens")

    # 审核状态
    status = Column(String(50), default="draft", comment="状态: draft/reviewing/approved/rejected")
    reviewed_by = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    reviewed_at = Column(DateTime, comment="审核时间")
    review_comments = Column(Text, comment="审核意见")

    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关联关系
    # TODO: 修复循环引用问题后再启用
    # requirement_analysis = relationship("PresaleAIRequirementAnalysis", back_populates="solutions")
    creator = relationship("User", foreign_keys=[created_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    # 索引
    __table_args__ = (
        Index("idx_presale_ticket", "presale_ticket_id"),
        Index("idx_ai_solution_status", "status"),
        Index("idx_ai_solution_created_at", "created_at"),
    )


class PresaleAIGenerationLog(Base):
    """AI生成日志表 (用于追踪和优化)"""

    __tablename__ = "presale_ai_generation_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    solution_id = Column(Integer, ForeignKey("presale_ai_solution.id"), comment="方案ID")

    # 请求信息
    request_type = Column(String(50), comment="请求类型: template_match/solution/architecture/bom")
    input_data = Column(JSON, comment="输入数据")

    # 响应信息
    output_data = Column(JSON, comment="输出数据")
    success = Column(Integer, comment="是否成功: 1成功/0失败")
    error_message = Column(Text, comment="错误信息")

    # 性能指标
    response_time_ms = Column(Integer, comment="响应时间(毫秒)")
    ai_model = Column(String(100), comment="AI模型")
    tokens_used = Column(Integer, comment="使用的token数")

    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    solution = relationship("PresaleAISolution")

    # 索引
    __table_args__ = (
        Index("idx_solution_id", "solution_id"),
        Index("idx_request_type", "request_type"),
        Index("idx_ai_sol_tmpl_created_at", "created_at"),
    )


# Backward-compatible alias
PresaleSolutionTemplate = PresaleAISolutionTemplate
