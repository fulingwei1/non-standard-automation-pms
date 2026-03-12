# -*- coding: utf-8 -*-
"""
线索需求详情 V2 - 拆分后的子表模型

将原 LeadRequirementDetail 表（60+字段）按业务场景拆分为3个子表：
1. LeadRequirementBasic - 基础需求信息
2. LeadRequirementTechnical - 技术规格（产能、测试、接口）
3. LeadRequirementFacility - 设施与物料

通过 one-to-one 关系连接，保持数据完整性。
"""

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


class LeadRequirementBasicV2(Base, TimestampMixin):
    """线索需求基础信息表

    包含项目基本信息、交付要求、需求成熟度等
    """

    __tablename__ = "lead_requirement_basic_v2"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, unique=True, comment="线索ID")

    # 基础信息
    customer_factory_location = Column(String(200), comment="客户工厂/地点")
    target_object_type = Column(String(100), comment="被测对象类型")
    application_scenario = Column(String(100), comment="应用场景")
    delivery_mode = Column(String(100), comment="计划交付模式")
    expected_delivery_date = Column(DateTime, comment="期望交付日期")
    requirement_source = Column(String(100), comment="需求来源")
    participant_ids = Column(Text, comment="参与人员(JSON Array)")

    # 需求成熟度
    requirement_maturity = Column(Integer, comment="需求成熟度(1-5级)")
    has_sow = Column(Boolean, comment="是否有客户SOW/URS")
    has_interface_doc = Column(Boolean, comment="是否有接口协议文档")
    has_drawing_doc = Column(Boolean, comment="是否有图纸/原理/IO清单")
    sample_availability = Column(Text, comment="样品可提供情况(JSON)")
    customer_support_resources = Column(Text, comment="客户配合资源(JSON)")

    # 风险与否决
    key_risk_factors = Column(Text, comment="关键风险初判(JSON Array)")
    veto_triggered = Column(Boolean, default=False, comment="一票否决触发")
    veto_reason = Column(Text, comment="一票否决原因")

    # 冻结状态
    requirement_version = Column(String(50), comment="需求包版本号")
    is_frozen = Column(Boolean, default=False, comment="是否冻结")
    frozen_at = Column(DateTime, comment="冻结时间")
    frozen_by = Column(Integer, ForeignKey("users.id"), comment="冻结人ID")

    # 关系
    lead = relationship("Lead", foreign_keys=[lead_id])
    frozen_by_user = relationship("User", foreign_keys=[frozen_by])
    technical = relationship(
        "LeadRequirementTechnicalV2",
        back_populates="basic",
        uselist=False,
        cascade="all, delete-orphan",
    )
    facility = relationship(
        "LeadRequirementFacilityV2",
        back_populates="basic",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_req_basic_v2_lead", "lead_id"),
        Index("idx_req_basic_v2_frozen", "is_frozen"),
        {"comment": "线索需求基础信息表(V2)"},
    )

    def __repr__(self):
        return f"<LeadRequirementBasicV2 lead={self.lead_id}>"


class LeadRequirementTechnicalV2(Base, TimestampMixin):
    """线索需求技术规格表

    包含产能节拍、测试规格、接口通讯等技术要求
    """

    __tablename__ = "lead_requirement_technical_v2"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    basic_id = Column(
        Integer,
        ForeignKey("lead_requirement_basic_v2.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="基础信息ID",
    )

    # 产能与节拍要求
    target_capacity_uph = Column(Numeric(10, 2), comment="目标产能(UPH)")
    target_capacity_daily = Column(Numeric(10, 2), comment="目标产能(日)")
    target_capacity_shift = Column(Numeric(10, 2), comment="目标产能(班)")
    cycle_time_seconds = Column(Numeric(10, 2), comment="节拍要求(CT秒)")
    workstation_count = Column(Integer, comment="工位数/并行数")
    changeover_method = Column(String(100), comment="换型方式")

    # 良率与复测
    yield_target = Column(Numeric(5, 2), comment="良率目标")
    retest_allowed = Column(Boolean, comment="是否允许复测")
    retest_max_count = Column(Integer, comment="复测次数")

    # 追溯与数据
    traceability_type = Column(String(50), comment="追溯要求")
    data_retention_period = Column(Integer, comment="数据保留期限(天)")
    data_format = Column(String(100), comment="数据格式")

    # 测试规格
    test_scope = Column(Text, comment="测试范围(JSON Array)")
    key_metrics_spec = Column(Text, comment="关键指标口径(JSON)")
    coverage_boundary = Column(Text, comment="覆盖边界(JSON)")
    exception_handling = Column(Text, comment="允许的异常处理(JSON)")

    # 验收要求
    acceptance_method = Column(String(100), comment="验收方式")
    acceptance_basis = Column(Text, comment="验收依据")
    delivery_checklist = Column(Text, comment="验收交付物清单(JSON Array)")

    # 接口与通讯
    interface_types = Column(Text, comment="被测对象接口类型(JSON Array)")
    io_point_estimate = Column(Text, comment="IO点数估算(JSON)")
    communication_protocols = Column(Text, comment="通讯协议(JSON Array)")
    upper_system_integration = Column(Text, comment="与上位系统对接(JSON)")
    data_field_list = Column(Text, comment="数据字段清单(JSON Array)")
    it_security_restrictions = Column(Text, comment="IT安全/网络限制(JSON)")

    # 关系
    basic = relationship("LeadRequirementBasicV2", back_populates="technical")

    __table_args__ = (
        Index("idx_req_tech_v2_basic", "basic_id"),
        {"comment": "线索需求技术规格表(V2)"},
    )

    def __repr__(self):
        return f"<LeadRequirementTechnicalV2 basic={self.basic_id}>"


class LeadRequirementFacilityV2(Base, TimestampMixin):
    """线索需求设施物料表

    包含供电气源、环境安全、物料要求等
    """

    __tablename__ = "lead_requirement_facility_v2"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    basic_id = Column(
        Integer,
        ForeignKey("lead_requirement_basic_v2.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="基础信息ID",
    )

    # 环境与设施
    power_supply = Column(Text, comment="供电(JSON)")
    air_supply = Column(Text, comment="气源(JSON)")
    environment = Column(Text, comment="环境(JSON)")
    safety_requirements = Column(Text, comment="安全要求(JSON)")
    space_and_logistics = Column(Text, comment="占地与物流(JSON)")
    customer_site_standards = Column(Text, comment="客户现场规范(JSON)")

    # 物料要求
    customer_supplied_materials = Column(Text, comment="客供物料清单(JSON Array)")
    restricted_brands = Column(Text, comment="禁用品牌(JSON Array)")
    specified_brands = Column(Text, comment="指定品牌(JSON Array)")
    long_lead_items = Column(Text, comment="长周期件提示(JSON Array)")

    # 售后支持
    spare_parts_requirement = Column(Text, comment="备品备件要求(JSON)")
    after_sales_support = Column(Text, comment="售后支持要求(JSON)")

    # 关系
    basic = relationship("LeadRequirementBasicV2", back_populates="facility")

    __table_args__ = (
        Index("idx_req_facility_v2_basic", "basic_id"),
        {"comment": "线索需求设施物料表(V2)"},
    )

    def __repr__(self):
        return f"<LeadRequirementFacilityV2 basic={self.basic_id}>"
