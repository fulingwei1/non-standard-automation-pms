# -*- coding: utf-8 -*-
"""
技术评估和需求管理模型
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
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
from app.models.enums import (
    AssessmentStatusEnum,
    OpenItemStatusEnum,
)


class TechnicalAssessment(Base, TimestampMixin):
    """技术评估结果表"""
    __tablename__ = "technical_assessments"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    source_type = Column(String(20), nullable=False, comment="来源类型：LEAD/OPPORTUNITY")
    source_id = Column(Integer, nullable=False, comment="来源ID（Lead.id 或 Opportunity.id）")
    evaluator_id = Column(Integer, ForeignKey("users.id"), comment="评估人ID（技术工程师）")
    status = Column(String(20), default=AssessmentStatusEnum.PENDING, comment="评估状态")
    total_score = Column(Integer, comment="总分")
    dimension_scores = Column(Text, comment="五维分数详情(JSON)")
    veto_triggered = Column(Boolean, default=False, comment="是否触发一票否决")
    veto_rules = Column(Text, comment="触发的否决规则(JSON)")
    decision = Column(String(30), comment="决策建议：推荐立项/有条件立项/暂缓/不建议立项")
    risks = Column(Text, comment="风险列表(JSON)")
    similar_cases = Column(Text, comment="相似失败案例(JSON)")
    ai_analysis = Column(Text, comment="AI分析报告")
    conditions = Column(Text, comment="立项条件(JSON)")
    evaluated_at = Column(DateTime, comment="评估完成时间")

    evaluator = relationship("User", foreign_keys=[evaluator_id])

    __table_args__ = (
        Index('idx_assessment_source', 'source_type', 'source_id'),
        Index('idx_assessment_status', 'status'),
        Index('idx_assessment_evaluator', 'evaluator_id'),
        Index('idx_assessment_decision', 'decision'),
    )

    def __repr__(self):
        return f"<TechnicalAssessment {self.id}>"


class ScoringRule(Base, TimestampMixin):
    """评分规则配置表"""
    __tablename__ = "scoring_rules"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    version = Column(String(20), unique=True, nullable=False, comment="版本号")
    rules_json = Column(Text, nullable=False, comment="完整规则配置(JSON)")
    is_active = Column(Boolean, default=False, comment="是否启用")
    description = Column(Text, comment="描述")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_scoring_rule_active', 'is_active'),
        Index('idx_scoring_rule_version', 'version'),
    )

    def __repr__(self):
        return f"<ScoringRule {self.version}>"


class FailureCase(Base, TimestampMixin):
    """失败案例库表"""
    __tablename__ = "failure_cases"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    case_code = Column(String(50), unique=True, nullable=False, comment="案例编号")
    project_name = Column(String(200), nullable=False, comment="项目名称")
    industry = Column(String(50), nullable=False, comment="行业")
    product_types = Column(Text, comment="产品类型(JSON Array)")
    processes = Column(Text, comment="工序/测试类型(JSON Array)")
    takt_time_s = Column(Integer, comment="节拍时间(秒)")
    annual_volume = Column(Integer, comment="年产量")
    budget_status = Column(String(50), comment="预算状态")
    customer_project_status = Column(String(50), comment="客户项目状态")
    spec_status = Column(String(50), comment="规范状态")
    price_sensitivity = Column(String(50), comment="价格敏感度")
    delivery_months = Column(Integer, comment="交付周期(月)")
    failure_tags = Column(Text, nullable=False, comment="失败标签(JSON Array)")
    core_failure_reason = Column(Text, nullable=False, comment="核心失败原因")
    early_warning_signals = Column(Text, nullable=False, comment="预警信号(JSON Array)")
    final_result = Column(String(100), comment="最终结果")
    lesson_learned = Column(Text, nullable=False, comment="教训总结")
    keywords = Column(Text, nullable=False, comment="关键词(JSON Array)")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_failure_case_industry', 'industry'),
        Index('idx_failure_case_code', 'case_code'),
    )

    def __repr__(self):
        return f"<FailureCase {self.case_code}>"


class LeadRequirementDetail(Base, TimestampMixin):
    """线索需求详情表"""
    __tablename__ = "lead_requirement_details"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, comment="线索ID")
    customer_factory_location = Column(String(200), comment="客户工厂/地点")
    target_object_type = Column(String(100), comment="被测对象类型")
    application_scenario = Column(String(100), comment="应用场景")
    delivery_mode = Column(String(100), comment="计划交付模式")
    expected_delivery_date = Column(DateTime, comment="期望交付日期")
    requirement_source = Column(String(100), comment="需求来源")
    participant_ids = Column(Text, comment="参与人员(JSON Array)")
    requirement_maturity = Column(Integer, comment="需求成熟度(1-5级)")
    has_sow = Column(Boolean, comment="是否有客户SOW/URS")
    has_interface_doc = Column(Boolean, comment="是否有接口协议文档")
    has_drawing_doc = Column(Boolean, comment="是否有图纸/原理/IO清单")
    sample_availability = Column(Text, comment="样品可提供情况(JSON)")
    customer_support_resources = Column(Text, comment="客户配合资源(JSON)")
    key_risk_factors = Column(Text, comment="关键风险初判(JSON Array)")
    veto_triggered = Column(Boolean, default=False, comment="一票否决触发")
    veto_reason = Column(Text, comment="一票否决原因")
    target_capacity_uph = Column(Numeric(10, 2), comment="目标产能(UPH)")
    target_capacity_daily = Column(Numeric(10, 2), comment="目标产能(日)")
    target_capacity_shift = Column(Numeric(10, 2), comment="目标产能(班)")
    cycle_time_seconds = Column(Numeric(10, 2), comment="节拍要求(CT秒)")
    workstation_count = Column(Integer, comment="工位数/并行数")
    changeover_method = Column(String(100), comment="换型方式")
    yield_target = Column(Numeric(5, 2), comment="良率目标")
    retest_allowed = Column(Boolean, comment="是否允许复测")
    retest_max_count = Column(Integer, comment="复测次数")
    traceability_type = Column(String(50), comment="追溯要求")
    data_retention_period = Column(Integer, comment="数据保留期限(天)")
    data_format = Column(String(100), comment="数据格式")
    test_scope = Column(Text, comment="测试范围(JSON Array)")
    key_metrics_spec = Column(Text, comment="关键指标口径(JSON)")
    coverage_boundary = Column(Text, comment="覆盖边界(JSON)")
    exception_handling = Column(Text, comment="允许的异常处理(JSON)")
    acceptance_method = Column(String(100), comment="验收方式")
    acceptance_basis = Column(Text, comment="验收依据")
    delivery_checklist = Column(Text, comment="验收交付物清单(JSON Array)")
    interface_types = Column(Text, comment="被测对象接口类型(JSON Array)")
    io_point_estimate = Column(Text, comment="IO点数估算(JSON)")
    communication_protocols = Column(Text, comment="通讯协议(JSON Array)")
    upper_system_integration = Column(Text, comment="与上位系统对接(JSON)")
    data_field_list = Column(Text, comment="数据字段清单(JSON Array)")
    it_security_restrictions = Column(Text, comment="IT安全/网络限制(JSON)")
    power_supply = Column(Text, comment="供电(JSON)")
    air_supply = Column(Text, comment="气源(JSON)")
    environment = Column(Text, comment="环境(JSON)")
    safety_requirements = Column(Text, comment="安全要求(JSON)")
    space_and_logistics = Column(Text, comment="占地与物流(JSON)")
    customer_site_standards = Column(Text, comment="客户现场规范(JSON)")
    customer_supplied_materials = Column(Text, comment="客供物料清单(JSON Array)")
    restricted_brands = Column(Text, comment="禁用品牌(JSON Array)")
    specified_brands = Column(Text, comment="指定品牌(JSON Array)")
    long_lead_items = Column(Text, comment="长周期件提示(JSON Array)")
    spare_parts_requirement = Column(Text, comment="备品备件要求(JSON)")
    after_sales_support = Column(Text, comment="售后支持要求(JSON)")
    requirement_version = Column(String(50), comment="需求包版本号")
    is_frozen = Column(Boolean, default=False, comment="是否冻结")
    frozen_at = Column(DateTime, comment="冻结时间")
    frozen_by = Column(Integer, ForeignKey("users.id"), comment="冻结人ID")

    lead = relationship("Lead", foreign_keys=[lead_id])
    frozen_by_user = relationship("User", foreign_keys=[frozen_by])

    __table_args__ = (
        Index('idx_requirement_detail_lead', 'lead_id'),
        Index('idx_requirement_detail_frozen', 'is_frozen'),
    )

    def __repr__(self):
        return f"<LeadRequirementDetail {self.id}>"


class RequirementFreeze(Base, TimestampMixin):
    """需求冻结记录表"""
    __tablename__ = "requirement_freezes"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    source_type = Column(String(20), nullable=False, comment="来源类型：LEAD/OPPORTUNITY")
    source_id = Column(Integer, nullable=False, comment="来源ID")
    freeze_type = Column(String(50), nullable=False, comment="冻结点类型")
    freeze_time = Column(DateTime, default=datetime.now, comment="冻结时间")
    frozen_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="冻结人ID")
    version_number = Column(String(50), nullable=False, comment="冻结版本号")
    requires_ecr = Column(Boolean, default=True, comment="冻结后变更是否必须走ECR/ECN")
    description = Column(Text, comment="冻结说明")

    frozen_by_user = relationship("User", foreign_keys=[frozen_by])

    __table_args__ = (
        Index('idx_requirement_freeze_source', 'source_type', 'source_id'),
        Index('idx_requirement_freeze_type', 'freeze_type'),
        Index('idx_requirement_freeze_time', 'freeze_time'),
    )

    def __repr__(self):
        return f"<RequirementFreeze {self.id}>"


class OpenItem(Base, TimestampMixin):
    """未决事项表"""
    __tablename__ = "open_items"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    source_type = Column(String(20), nullable=False, comment="来源类型：LEAD/OPPORTUNITY")
    source_id = Column(Integer, nullable=False, comment="来源ID")
    item_code = Column(String(50), unique=True, nullable=False, comment="未决事项编号")
    item_type = Column(String(50), nullable=False, comment="问题类型")
    description = Column(Text, nullable=False, comment="问题描述")
    responsible_party = Column(String(50), nullable=False, comment="责任方")
    responsible_person_id = Column(Integer, ForeignKey("users.id"), comment="责任人ID")
    due_date = Column(DateTime, comment="截止日期")
    status = Column(String(20), default=OpenItemStatusEnum.PENDING, comment="当前状态")
    close_evidence = Column(Text, comment="关闭证据(附件/链接/记录)")
    blocks_quotation = Column(Boolean, default=False, comment="是否阻塞报价")
    closed_at = Column(DateTime, comment="关闭时间")

    responsible_person = relationship("User", foreign_keys=[responsible_person_id])

    __table_args__ = (
        Index('idx_open_item_source', 'source_type', 'source_id'),
        Index('idx_open_item_status', 'status'),
        Index('idx_open_item_type', 'item_type'),
        Index('idx_open_item_blocks', 'blocks_quotation'),
        Index('idx_open_item_due_date', 'due_date'),
    )

    def __repr__(self):
        return f"<OpenItem {self.item_code}>"


class AIClarification(Base, TimestampMixin):
    """AI澄清记录表"""
    __tablename__ = "ai_clarifications"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    source_type = Column(String(20), nullable=False, comment="来源类型：LEAD/OPPORTUNITY")
    source_id = Column(Integer, nullable=False, comment="来源ID")
    round = Column(Integer, nullable=False, comment="澄清轮次")
    questions = Column(Text, nullable=False, comment="AI生成的问题(JSON Array)")
    answers = Column(Text, comment="用户回答(JSON Array)")

    __table_args__ = (
        Index('idx_ai_clarification_source', 'source_type', 'source_id'),
        Index('idx_ai_clarification_round', 'round'),
    )

    def __repr__(self):
        return f"<AIClarification {self.id}>"


class QuoteApproval(Base, TimestampMixin):
    """报价审批表"""
    __tablename__ = "quote_approvals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, comment="报价ID")
    approval_level = Column(Integer, nullable=False, comment="审批层级")
    approval_role = Column(String(50), nullable=False, comment="审批角色")
    approver_id = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approver_name = Column(String(50), comment="审批人姓名")
    approval_result = Column(String(20), comment="审批结果")
    approval_opinion = Column(Text, comment="审批意见")
    status = Column(String(20), default="PENDING", comment="状态")
    approved_at = Column(DateTime, comment="审批时间")
    due_date = Column(DateTime, comment="审批期限")
    is_overdue = Column(Boolean, default=False, comment="是否超期")

    quote = relationship("Quote", foreign_keys=[quote_id])
    approver = relationship("User", foreign_keys=[approver_id])

    __table_args__ = (
        Index("idx_quote_approval_quote", "quote_id"),
        Index("idx_quote_approval_approver", "approver_id"),
        Index("idx_quote_approval_status", "status"),
    )

    def __repr__(self):
        return f"<QuoteApproval {self.quote_id}-L{self.approval_level}>"
