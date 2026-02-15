"""
售前AI方案生成模块 - 数据模型
AI-Powered Solution Generation for Presales
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DECIMAL, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class PresaleAISolution(Base):
    """AI方案生成记录表"""
    __tablename__ = "presale_ai_solution"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    presale_ticket_id = Column(Integer, nullable=False, comment="售前工单ID")
    requirement_analysis_id = Column(Integer, ForeignKey("presale_ai_requirement_analysis.id"), comment="需求分析ID")
    
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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    requirement_analysis = relationship("PresaleAIRequirementAnalysis", back_populates="solutions")
    creator = relationship("User", foreign_keys=[created_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    # 索引
    __table_args__ = (
        Index('idx_presale_ticket', 'presale_ticket_id'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
    )


class PresaleSolutionTemplate(Base):
    """方案模板库 (用于相似度匹配)"""
    __tablename__ = "presale_solution_templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(200), nullable=False, comment="模板名称")
    code = Column(String(100), unique=True, comment="模板编码")
    
    # 分类信息
    industry = Column(String(100), comment="行业分类: 汽车/电子/医疗/食品等")
    equipment_type = Column(String(100), comment="设备类型: 装配/焊接/检测/包装等")
    complexity_level = Column(String(50), comment="复杂度: simple/medium/complex")
    
    # 模板内容
    solution_content = Column(JSON, comment="方案内容模板")
    architecture_diagram = Column(Text, comment="架构图模板 (Mermaid)")
    bom_template = Column(JSON, comment="BOM模板")
    
    # 技术参数
    technical_specs = Column(JSON, comment="技术规格参数")
    equipment_list = Column(JSON, comment="设备清单")
    
    # 向量嵌入 (用于语义搜索)
    embedding = Column(Text, comment="文本嵌入向量 (JSON字符串)")
    embedding_model = Column(String(100), comment="嵌入模型名称")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    success_rate = Column(DECIMAL(3, 2), comment="成功率")
    avg_quality_score = Column(DECIMAL(3, 2), comment="平均质量评分")
    
    # 成本信息
    typical_cost_range_min = Column(DECIMAL(12, 2), comment="典型成本范围-最小值")
    typical_cost_range_max = Column(DECIMAL(12, 2), comment="典型成本范围-最大值")
    
    # 标签和关键词
    tags = Column(JSON, comment="标签列表")
    keywords = Column(Text, comment="关键词 (用于全文搜索)")
    
    # 状态
    is_active = Column(Integer, default=1, comment="是否启用: 1启用/0禁用")
    
    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    creator = relationship("User", foreign_keys=[created_by])
    
    # 索引
    __table_args__ = (
        Index('idx_industry_equipment', 'industry', 'equipment_type'),
        Index('idx_complexity', 'complexity_level'),
        Index('idx_active', 'is_active'),
        Index('idx_usage', 'usage_count'),
    )


class PresaleAIGenerationLog(Base):
    """AI生成日志表 (用于追踪和优化)"""
    __tablename__ = "presale_ai_generation_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
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
        Index('idx_solution_id', 'solution_id'),
        Index('idx_request_type', 'request_type'),
        Index('idx_created_at', 'created_at'),
    )
