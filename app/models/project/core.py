# -*- coding: utf-8 -*-
"""
项目核心模型 - Project 和 Machine
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin
from ..organization import Department


class Project(Base, TimestampMixin):
    """项目表"""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_code = Column(String(50), unique=True, nullable=False, comment="项目编码")
    project_name = Column(String(200), nullable=False, comment="项目名称")
    short_name = Column(String(50), comment="项目简称")
    customer_id = Column(Integer, ForeignKey("customers.id"), comment="客户ID")
    customer_name = Column(String(200), comment="客户名称（冗余）")
    customer_contact = Column(String(100), comment="客户联系人")
    customer_phone = Column(String(50), comment="联系电话")
    contract_no = Column(String(100), comment="合同编号")

    # 项目信息
    project_type = Column(String(20), comment="项目类型")
    product_category = Column(String(50), comment="产品类别")
    industry = Column(String(50), comment="行业")
    project_category = Column(String(20), comment="项目分类：销售/研发/改造/维保")

    # 3D状态
    stage = Column(String(20), default="S1", comment="阶段")
    status = Column(String(20), default="ST01", comment="状态")
    health = Column(String(10), default="H1", comment="健康度")

    # 进度
    progress_pct = Column(Numeric(5, 2), default=0, comment="整体进度(%)")

    # 时间
    contract_date = Column(Date, comment="合同日期")
    planned_start_date = Column(Date, comment="计划开始")
    planned_end_date = Column(Date, comment="计划结束")
    actual_start_date = Column(Date, comment="实际开始")
    actual_end_date = Column(Date, comment="实际结束")

    # 金额
    contract_amount = Column(Numeric(14, 2), default=0, comment="合同金额")
    budget_amount = Column(Numeric(14, 2), default=0, comment="预算金额")
    actual_cost = Column(Numeric(14, 2), default=0, comment="实际成本")

    # 人员
    pm_id = Column(Integer, ForeignKey("users.id"), comment="项目经理ID")
    pm_name = Column(String(50), comment="项目经理姓名")
    dept_id = Column(Integer, ForeignKey("departments.id"), comment="所属部门")

    # 优先级与标签
    priority = Column(String(20), default="NORMAL", comment="优先级")
    tags = Column(Text, comment="标签")

    # 描述
    description = Column(Text, comment="项目描述")
    requirements = Column(Text, comment="项目需求摘要")

    # 附件
    attachments = Column(Text, comment="附件列表")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_archived = Column(Boolean, default=False, comment="是否归档")

    # 模板关联（Sprint 4.1: 项目模板使用统计）
    template_id = Column(Integer, ForeignKey("project_templates.id"), comment="创建时使用的模板ID")
    template_version_id = Column(Integer, ForeignKey("project_template_versions.id"), comment="创建时使用的模板版本ID")

    # 阶段模板关联（阶段模板化功能）
    stage_template_id = Column(Integer, ForeignKey("stage_templates.id"), comment="阶段模板ID")
    current_stage_instance_id = Column(Integer, comment="当前阶段实例ID")
    current_node_instance_id = Column(Integer, comment="当前节点实例ID")

    # 销售关联
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), comment="销售机会ID")
    contract_id = Column(Integer, ForeignKey("contracts.id"), comment="合同ID")

    # ERP集成
    erp_synced = Column(Boolean, default=False, comment="是否已录入ERP系统")
    erp_sync_time = Column(DateTime, comment="ERP同步时间")
    erp_order_no = Column(String(50), comment="ERP订单号")
    erp_sync_status = Column(String(20), default="PENDING", comment="ERP同步状态：PENDING/SYNCED/FAILED")

    # 财务状态
    invoice_issued = Column(Boolean, default=False, comment="是否已开票")
    final_payment_completed = Column(Boolean, default=False, comment="是否已结尾款")
    final_payment_date = Column(Date, comment="结尾款日期")

    # 质保信息
    warranty_period_months = Column(Integer, comment="质保期限（月）")
    warranty_start_date = Column(Date, comment="质保开始日期")
    warranty_end_date = Column(Date, comment="质保结束日期")

    # 实施信息
    implementation_address = Column(String(500), comment="实施地址")
    test_encryption = Column(String(100), comment="测试加密")

    # 预立项流程关联
    initiation_id = Column(Integer, ForeignKey("pmo_project_initiation.id"), comment="预立项申请ID")

    # 售前评估关联
    source_lead_id = Column(String(50), comment="来源线索号（如XS2501001）")
    evaluation_score = Column(Numeric(5, 2), comment="评估总分")
    predicted_win_rate = Column(Numeric(5, 4), comment="预测中标率（0-1）")
    outcome = Column(String(20), comment="最终结果：PENDING/WON/LOST/ABANDONED")
    loss_reason = Column(String(50), comment="丢标原因代码")
    loss_reason_detail = Column(Text, comment="丢标原因详情")
    salesperson_id = Column(Integer, ForeignKey("users.id"), comment="销售人员ID")

    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    customer = relationship("Customer", back_populates="projects")
    creator = relationship(
        "User", foreign_keys=[created_by], back_populates="created_projects"
    )
    manager = relationship(
        "User", foreign_keys=[pm_id], back_populates="managed_projects"
    )
    department = relationship(Department)
    opportunity = relationship("Opportunity", foreign_keys=[opportunity_id])
    contract = relationship("Contract", foreign_keys=[contract_id])
    salesperson = relationship("User", foreign_keys=[salesperson_id])
    initiation = relationship("PmoProjectInitiation", foreign_keys=[initiation_id])
    machines = relationship("Machine", back_populates="project", lazy="dynamic")
    stages = relationship("ProjectStage", back_populates="project", lazy="dynamic")
    milestones = relationship(
        "ProjectMilestone", back_populates="project", lazy="dynamic"
    )
    members = relationship("ProjectMember", back_populates="project", lazy="dynamic")
    costs = relationship("ProjectCost", back_populates="project", lazy="dynamic")
    financial_costs = relationship("FinancialProjectCost", back_populates="project", lazy="dynamic")
    documents = relationship(
        "ProjectDocument", back_populates="project", lazy="dynamic"
    )
    # 阶段模板化关系
    stage_template = relationship("StageTemplate", foreign_keys=[stage_template_id])
    stage_instances = relationship(
        "ProjectStageInstance", back_populates="project", lazy="dynamic"
    )
    node_instances = relationship(
        "ProjectNodeInstance", back_populates="project", lazy="dynamic"
    )

    __table_args__ = (
        Index("idx_projects_code", "project_code"),
        Index("idx_projects_customer", "customer_id"),
        Index("idx_projects_pm", "pm_id"),
        Index("idx_projects_stage", "stage"),
        Index("idx_projects_health", "health"),
        Index("idx_projects_active", "is_active"),
        # Sprint 5.1: 性能优化 - 添加复合索引
        Index("idx_projects_stage_status", "stage", "status"),
        Index("idx_projects_stage_health", "stage", "health"),
        Index("idx_projects_active_archived", "is_active", "is_archived"),
        Index("idx_projects_created_at", "created_at"),  # 用于排序
        Index("idx_projects_type_category", "project_type", "product_category"),  # 用于筛选
        Index("idx_projects_opportunity", "opportunity_id"),  # 销售机会关联
        Index("idx_projects_contract", "contract_id"),  # 合同关联
        Index("idx_projects_erp_sync", "erp_synced", "erp_sync_status"),  # ERP同步状态
        Index("idx_projects_initiation", "initiation_id"),  # 预立项关联
        Index("idx_projects_source_lead", "source_lead_id"),  # 来源线索关联
        Index("idx_projects_outcome", "outcome"),  # 线索结果
        Index("idx_projects_salesperson", "salesperson_id"),  # 销售人员
    )

    def __repr__(self):
        return f"<Project {self.project_code}>"


class Machine(Base, TimestampMixin):
    """设备/机台表"""

    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="所属项目"
    )
    machine_code = Column(String(50), nullable=False, comment="设备编码")
    machine_name = Column(String(200), nullable=False, comment="设备名称")
    machine_no = Column(Integer, default=1, comment="设备序号（项目内）")

    # 设备信息
    machine_type = Column(String(50), comment="设备类型")
    specification = Column(Text, comment="规格描述")

    # 状态
    stage = Column(String(20), default="S1", comment="设备阶段")
    status = Column(String(20), default="ST01", comment="设备状态")
    health = Column(String(10), default="H1", comment="健康度")

    # 进度
    progress_pct = Column(Numeric(5, 2), default=0, comment="设备进度")

    # 时间
    planned_start_date = Column(Date, comment="计划开始")
    planned_end_date = Column(Date, comment="计划结束")
    actual_start_date = Column(Date, comment="实际开始")
    actual_end_date = Column(Date, comment="实际结束")

    # FAT/SAT信息
    fat_date = Column(Date, comment="FAT日期")
    fat_result = Column(String(20), comment="FAT结果")
    sat_date = Column(Date, comment="SAT日期")
    sat_result = Column(String(20), comment="SAT结果")

    # 发货信息
    ship_date = Column(Date, comment="发货日期")
    ship_address = Column(String(500), comment="发货地址")
    tracking_no = Column(String(100), comment="物流单号")

    remark = Column(Text, comment="备注")

    # 关系
    project = relationship("Project", back_populates="machines")
    bom_headers = relationship("BomHeader", back_populates="machine", lazy="dynamic")

    __table_args__ = (
        Index("idx_machines_project", "project_id"),
        Index("idx_machines_stage", "stage"),
        Index("idx_machines_project_code", "project_id", "machine_code", unique=True),
    )

    def __repr__(self):
        return f"<Machine {self.machine_code}>"
