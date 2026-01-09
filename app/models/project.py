# -*- coding: utf-8 -*-
"""
项目管理模块模型
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Text,
    ForeignKey,
    Numeric,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin
from .organization import Department


class Customer(Base, TimestampMixin):
    """客户表"""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_code = Column(String(50), unique=True, nullable=False, comment="客户编码")
    customer_name = Column(String(200), nullable=False, comment="客户名称")
    short_name = Column(String(50), comment="客户简称")
    customer_type = Column(String(20), comment="客户类型")
    industry = Column(String(50), comment="所属行业")
    scale = Column(String(20), comment="规模")
    address = Column(String(500), comment="详细地址")
    contact_person = Column(String(50), comment="联系人")
    contact_phone = Column(String(50), comment="联系电话")
    contact_email = Column(String(100), comment="联系邮箱")

    # NEW fields from DB
    legal_person = Column(String(50), comment="法人代表")
    tax_no = Column(String(50), comment="税号")
    bank_name = Column(String(100), comment="开户行")
    bank_account = Column(String(50), comment="账号")

    credit_level = Column(String(20), default="B", comment="信用等级")
    credit_limit = Column(Numeric(14, 2), comment="信用额度")
    payment_terms = Column(String(50), comment="付款条款")

    portal_enabled = Column(Boolean, default=False, comment="门户启用")
    portal_username = Column(String(100), comment="门户账号")

    status = Column(String(20), default="ACTIVE", comment="状态")
    remark = Column(Text, comment="备注")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    projects = relationship("Project", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.customer_code}>"


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
        UniqueConstraint("project_id", "machine_code"),
    )

    def __repr__(self):
        return f"<Machine {self.machine_code}>"


class ProjectStage(Base, TimestampMixin):
    """项目阶段表（项目相关）"""

    __tablename__ = "project_stages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="所属项目"
    )
    stage_code = Column(String(20), nullable=False, comment="阶段编码：S1-S9")
    stage_name = Column(String(50), nullable=False, comment="阶段名称")
    stage_order = Column(Integer, nullable=False, comment="阶段顺序")
    description = Column(Text, comment="阶段描述")

    # 计划与实际
    planned_start_date = Column(Date, comment="计划开始")
    planned_end_date = Column(Date, comment="计划结束")
    actual_start_date = Column(Date, comment="实际开始")
    actual_end_date = Column(Date, comment="实际结束")

    # 进度
    progress_pct = Column(Integer, default=0, comment="进度(%)")
    status = Column(String(20), default="PENDING", comment="状态")

    # 门控条件
    gate_conditions = Column(Text, comment="进入条件JSON")
    required_deliverables = Column(Text, comment="必需交付物JSON")

    # 默认时长
    default_duration_days = Column(Integer, comment="默认工期（天）")

    # 颜色配置
    color = Column(String(20), comment="显示颜色")
    icon = Column(String(50), comment="图标")

    is_active = Column(Boolean, default=True)

    # 关系
    project = relationship("Project", back_populates="stages")
    statuses = relationship("ProjectStatus", back_populates="stage", lazy="dynamic")

    __table_args__ = (
        Index("idx_stage_project", "project_id"),
        UniqueConstraint("project_id", "stage_code"),
    )

    def __repr__(self):
        return f"<ProjectStage {self.stage_code}>"


class ProjectStatus(Base, TimestampMixin):
    """项目状态定义表"""

    __tablename__ = "project_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_id = Column(
        Integer, ForeignKey("project_stages.id"), nullable=False, comment="所属阶段ID"
    )
    status_code = Column(String(20), nullable=False, comment="状态编码")
    status_name = Column(String(50), nullable=False, comment="状态名称")
    status_order = Column(Integer, nullable=False, comment="状态顺序")
    description = Column(Text, comment="状态描述")

    # 状态类型
    status_type = Column(String(20), default="NORMAL", comment="NORMAL/MILESTONE/GATE")

    # 自动流转
    auto_next_status = Column(String(20), comment="自动下一状态")

    is_active = Column(Boolean, default=True)

    # 关系
    stage = relationship("ProjectStage", back_populates="statuses")

    __table_args__ = (
        Index("idx_project_statuses_stage", "stage_id"),
        UniqueConstraint("stage_id", "status_code"),
    )

    def __repr__(self):
        return f"<ProjectStatus {self.status_code}>"


class ProjectStatusLog(Base):
    """项目状态变更日志表"""

    __tablename__ = "project_status_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    machine_id = Column(
        Integer, ForeignKey("machines.id"), nullable=True, comment="设备ID（可选）"
    )

    # 变更前状态
    old_stage = Column(String(20), comment="变更前阶段")
    old_status = Column(String(20), comment="变更前状态")
    old_health = Column(String(10), comment="变更前健康度")

    # 变更后状态
    new_stage = Column(String(20), comment="变更后阶段")
    new_status = Column(String(20), comment="变更后状态")
    new_health = Column(String(10), comment="变更后健康度")

    # 变更信息
    change_type = Column(
        String(20), nullable=False, comment="变更类型：STAGE_CHANGE/STATUS_CHANGE/HEALTH_CHANGE"
    )
    change_reason = Column(Text, comment="变更原因")
    change_note = Column(Text, comment="变更备注")

    # 操作信息
    changed_by = Column(Integer, ForeignKey("users.id"), comment="变更人ID")
    changed_at = Column(DateTime, nullable=False, comment="变更时间")

    # 关系
    project = relationship("Project", backref="status_logs")
    machine = relationship("Machine", backref="status_logs")
    changer = relationship("User", foreign_keys=[changed_by])

    __table_args__ = (
        Index("idx_project_status_logs_project", "project_id"),
        Index("idx_project_status_logs_machine", "machine_id"),
        Index("idx_project_status_logs_time", "changed_at"),
    )

    def __repr__(self):
        return f"<ProjectStatusLog {self.change_type} for Project {self.project_id}>"


class ProjectMember(Base, TimestampMixin):
    """项目成员表"""

    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    role_code = Column(String(50), nullable=False, comment="角色编码（兼容旧版）")

    # 新增：角色类型关联（支持灵活配置）
    role_type_id = Column(
        Integer,
        ForeignKey("project_role_types.id"),
        nullable=True,
        comment="角色类型ID（关联角色字典）"
    )
    is_lead = Column(Boolean, default=False, comment="是否为该角色的负责人")

    # 新增：设备级成员分配
    machine_id = Column(
        Integer,
        ForeignKey("machines.id"),
        nullable=True,
        comment="设备ID（设备级成员分配）"
    )

    # 新增：团队层级关系
    lead_member_id = Column(
        Integer,
        ForeignKey("project_members.id"),
        nullable=True,
        comment="所属负责人ID（团队成员指向其负责人）"
    )

    # 分配信息
    allocation_pct = Column(Numeric(5, 2), default=100, comment="分配比例")
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")
    
    # 矩阵式管理字段
    commitment_level = Column(String(20), comment="投入级别：FULL/PARTIAL/ADVISORY")
    reporting_to_pm = Column(Boolean, default=True, comment="是否向项目经理汇报")
    dept_manager_notified = Column(Boolean, default=False, comment="部门经理是否已通知")

    # 状态
    is_active = Column(Boolean, default=True)

    # 备注
    remark = Column(Text, comment="备注")

    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    role_type = relationship("ProjectRoleType", foreign_keys=[role_type_id])
    machine = relationship("Machine", foreign_keys=[machine_id])
    lead = relationship("ProjectMember", remote_side=[id], foreign_keys=[lead_member_id])
    team_members = relationship(
        "ProjectMember",
        back_populates="lead",
        foreign_keys=[lead_member_id]
    )

    __table_args__ = (
        Index("idx_project_members_project", "project_id"),
        Index("idx_project_members_user", "user_id"),
        Index("idx_project_members_role_type", "role_type_id"),
        Index("idx_project_members_is_lead", "is_lead"),
        Index("idx_project_members_machine", "machine_id"),
        Index("idx_project_members_lead", "lead_member_id"),
        UniqueConstraint("project_id", "user_id", "role_code"),
    )


class ProjectMilestone(Base, TimestampMixin):
    """项目里程碑表"""

    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="设备ID（可选）")
    milestone_code = Column(String(50), nullable=False, comment="里程碑编码")
    milestone_name = Column(String(200), nullable=False, comment="里程碑名称")
    milestone_type = Column(
        String(20), default="CUSTOM", comment="GATE/DELIVERY/PAYMENT/CUSTOM"
    )

    # 时间
    planned_date = Column(Date, nullable=False, comment="计划日期")
    actual_date = Column(Date, comment="实际完成日期")
    reminder_days = Column(Integer, default=7, comment="提前提醒天数")

    # 状态
    status = Column(String(20), default="PENDING", comment="状态")
    is_key = Column(Boolean, default=False, comment="是否关键里程碑")

    # 关联
    stage_code = Column(String(20), comment="关联阶段")
    deliverables = Column(Text, comment="交付物JSON")

    owner_id = Column(Integer, ForeignKey("users.id"), comment="责任人")
    remark = Column(Text, comment="备注")

    # 关系
    project = relationship("Project", back_populates="milestones")

    __table_args__ = (
        Index("idx_project_milestones_project", "project_id"),
        Index("idx_project_milestones_status", "status"),
        Index("idx_project_milestones_date", "planned_date"),
    )

    def __repr__(self):
        return f"<ProjectMilestone {self.milestone_code}>"


class ProjectPaymentPlan(Base, TimestampMixin):
    """项目收款计划表"""

    __tablename__ = "project_payment_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    contract_id = Column(Integer, ForeignKey("contracts.id"), comment="合同ID")
    
    payment_no = Column(Integer, nullable=False, comment="期次")
    payment_name = Column(String(100), nullable=False, comment="款项名称")
    payment_type = Column(String(20), nullable=False, comment="款项类型：ADVANCE/DELIVERY/ACCEPTANCE/WARRANTY")
    
    # 金额
    payment_ratio = Column(Numeric(5, 2), comment="比例(%)")
    planned_amount = Column(Numeric(14, 2), nullable=False, comment="计划金额")
    actual_amount = Column(Numeric(14, 2), default=0, comment="实际收款")
    
    # 时间
    planned_date = Column(Date, comment="计划收款日期")
    actual_date = Column(Date, comment="实际收款日期")
    
    # 触发条件
    milestone_id = Column(Integer, ForeignKey("project_milestones.id"), comment="关联里程碑ID")
    trigger_milestone = Column(String(50), comment="触发里程碑名称")
    trigger_condition = Column(Text, comment="触发条件描述")
    
    # 状态
    status = Column(String(20), default="PENDING", comment="状态：PENDING/INVOICED/PARTIAL/COMPLETED")
    
    # 发票信息
    invoice_id = Column(Integer, ForeignKey("invoices.id"), comment="关联发票ID")
    invoice_no = Column(String(100), comment="发票号")
    invoice_date = Column(Date, comment="开票日期")
    invoice_amount = Column(Numeric(14, 2), comment="开票金额")
    
    remark = Column(Text, comment="备注")
    
    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    contract = relationship("Contract", foreign_keys=[contract_id])
    milestone = relationship("ProjectMilestone", foreign_keys=[milestone_id])
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    invoice_requests = relationship("InvoiceRequest", back_populates="payment_plan")
    
    __table_args__ = (
        Index("idx_payment_plans_project", "project_id"),
        Index("idx_payment_plans_contract", "contract_id"),
        Index("idx_payment_plans_milestone", "milestone_id"),
        Index("idx_payment_plans_status", "status"),
    )
    
    def __repr__(self):
        return f"<ProjectPaymentPlan {self.project_id}-{self.payment_no}>"


class ProjectCost(Base, TimestampMixin):
    """项目成本表"""

    __tablename__ = "project_costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="设备ID")
    cost_type = Column(String(50), nullable=False, comment="成本类型")
    cost_category = Column(String(50), nullable=False, comment="成本分类")

    # 来源
    source_module = Column(String(50), comment="来源模块")
    source_type = Column(String(50), comment="来源类型")
    source_id = Column(Integer, comment="来源ID")
    source_no = Column(String(100), comment="来源单号")

    # 金额
    amount = Column(Numeric(14, 2), nullable=False, default=0, comment="金额")
    tax_amount = Column(Numeric(12, 2), default=0, comment="税额")

    # 时间
    cost_date = Column(Date, nullable=False, comment="发生日期")

    description = Column(Text, comment="描述")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    project = relationship("Project", back_populates="costs")
    machine = relationship("Machine")

    __table_args__ = (
        Index("idx_project_costs_project", "project_id"),
        Index("idx_project_costs_type", "cost_type"),
        Index("idx_project_costs_date", "cost_date"),
    )


class FinancialProjectCost(Base, TimestampMixin):
    """财务历史项目成本表（财务部维护的非物料成本）"""
    
    __tablename__ = "financial_project_costs"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    # 项目关联
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    project_code = Column(String(50), comment="项目编号（冗余字段，便于查询）")
    project_name = Column(String(200), comment="项目名称（冗余字段，便于查询）")
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="设备ID")
    
    # 成本类型和分类
    cost_type = Column(String(50), nullable=False, comment="成本类型：LABOR/TRAVEL/ENTERTAINMENT/OTHER")
    cost_category = Column(String(50), nullable=False, comment="成本分类：出差费/人工费/招待费/其他")
    cost_item = Column(String(200), comment="成本项名称")
    
    # 金额信息
    amount = Column(Numeric(14, 2), nullable=False, comment="金额")
    tax_amount = Column(Numeric(12, 2), default=0, comment="税额")
    currency = Column(String(10), default="CNY", comment="币种")
    
    # 时间信息
    cost_date = Column(Date, nullable=False, comment="发生日期")
    cost_month = Column(String(7), comment="成本月份(YYYY-MM)")
    
    # 详细信息
    description = Column(Text, comment="费用说明")
    location = Column(String(200), comment="地点（出差费用）")
    participants = Column(String(500), comment="参与人员（逗号分隔）")
    purpose = Column(String(500), comment="用途/目的")
    
    # 人工费用相关
    user_id = Column(Integer, ForeignKey("users.id"), comment="人员ID（人工费用）")
    user_name = Column(String(50), comment="人员姓名（冗余）")
    hours = Column(Numeric(10, 2), comment="工时（人工费用）")
    hourly_rate = Column(Numeric(10, 2), comment="时薪（人工费用）")
    
    # 来源信息
    source_type = Column(String(50), default="FINANCIAL_UPLOAD", comment="来源类型：FINANCIAL_UPLOAD（财务上传）")
    source_no = Column(String(100), comment="来源单号（如报销单号、发票号等）")
    invoice_no = Column(String(100), comment="发票号")
    
    # 上传信息
    upload_batch_no = Column(String(50), comment="上传批次号")
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="上传人ID（财务部）")
    
    # 状态
    is_verified = Column(Boolean, default=False, comment="是否已核实")
    verified_by = Column(Integer, ForeignKey("users.id"), comment="核实人ID")
    verified_at = Column(DateTime, comment="核实时间")
    
    # 关系
    project = relationship("Project", back_populates="financial_costs")
    machine = relationship("Machine")
    user = relationship("User", foreign_keys=[user_id])
    uploader = relationship("User", foreign_keys=[uploaded_by])
    verifier = relationship("User", foreign_keys=[verified_by])
    
    __table_args__ = (
        Index("idx_financial_cost_project", "project_id"),
        Index("idx_financial_cost_type", "cost_type"),
        Index("idx_financial_cost_category", "cost_category"),
        Index("idx_financial_cost_date", "cost_date"),
        Index("idx_financial_cost_month", "cost_month"),
        Index("idx_financial_cost_upload_batch", "upload_batch_no"),
        {"comment": "财务历史项目成本表"}
    )
    
    def __repr__(self):
        return f"<FinancialProjectCost {self.project_code}-{self.cost_type}>"


class ProjectDocument(Base, TimestampMixin):
    """项目文档表"""

    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="设备ID")
    rd_project_id = Column(Integer, ForeignKey("rd_project.id"), comment="研发项目ID")
    doc_type = Column(String(50), nullable=False, comment="文档类型")
    doc_category = Column(String(50), comment="文档分类")
    doc_name = Column(String(200), nullable=False, comment="文档名称")
    doc_no = Column(String(100), comment="文档编号")
    version = Column(String(20), default="1.0", comment="版本号")

    # 文件信息
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_name = Column(String(200), nullable=False, comment="文件名")
    file_size = Column(Integer, comment="文件大小")
    file_type = Column(String(50), comment="文件类型")

    # 状态
    status = Column(String(20), default="DRAFT", comment="状态")

    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人")
    approved_at = Column(DateTime, comment="审批时间")

    description = Column(Text, comment="描述")
    uploaded_by = Column(Integer, ForeignKey("users.id"), comment="上传人")

    # 关系
    project = relationship("Project", back_populates="documents")
    rd_project = relationship(
        "RdProject",
        foreign_keys=[rd_project_id],
        primaryjoin="ProjectDocument.rd_project_id == RdProject.id"
    )
    machine = relationship("Machine")

    __table_args__ = (
        Index("idx_project_documents_project", "project_id"),
        Index("idx_project_documents_rd_project", "rd_project_id"),
        Index("idx_project_documents_type", "doc_type"),
    )


class ProjectTemplate(Base, TimestampMixin):
    """项目模板表"""

    __tablename__ = "project_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_code = Column(String(50), unique=True, nullable=False, comment="模板编码")
    template_name = Column(String(200), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    
    # 模板配置（JSON格式存储项目默认配置）
    project_type = Column(String(20), comment="项目类型")
    product_category = Column(String(50), comment="产品类别")
    industry = Column(String(50), comment="行业")
    
    # 默认配置
    default_stage = Column(String(20), default="S1", comment="默认阶段")
    default_status = Column(String(20), default="ST01", comment="默认状态")
    default_health = Column(String(10), default="H1", comment="默认健康度")
    
    # 模板内容（JSON格式，存储项目字段的默认值）
    template_config = Column(Text, comment="模板配置JSON")
    
    # 是否启用
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    # 版本管理
    current_version_id = Column(Integer, ForeignKey("project_template_versions.id"), comment="当前版本ID")
    
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")
    
    # 关系
    versions = relationship("ProjectTemplateVersion", back_populates="template", foreign_keys="ProjectTemplateVersion.template_id", cascade="all, delete-orphan")
    current_version = relationship("ProjectTemplateVersion", foreign_keys=[current_version_id], post_update=True)
    
    __table_args__ = (
        Index("idx_project_template_code", "template_code"),
        Index("idx_project_template_active", "is_active"),
        Index("idx_project_template_current_version", "current_version_id"),
    )

    def __repr__(self):
        return f"<ProjectTemplate {self.template_code}>"


class ProjectTemplateVersion(Base, TimestampMixin):
    """项目模板版本表"""
    
    __tablename__ = "project_template_versions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("project_templates.id"), nullable=False, comment="模板ID")
    version_no = Column(String(20), nullable=False, comment="版本号")
    status = Column(String(20), default="DRAFT", comment="状态：DRAFT/ACTIVE/ARCHIVED")
    template_config = Column(Text, comment="模板配置JSON")
    release_notes = Column(Text, comment="版本说明")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    published_by = Column(Integer, ForeignKey("users.id"), comment="发布人ID")
    published_at = Column(DateTime, comment="发布时间")
    
    # 关系
    template = relationship("ProjectTemplate", back_populates="versions", foreign_keys=[template_id])
    creator = relationship("User", foreign_keys=[created_by], backref="project_template_versions_created")
    publisher = relationship("User", foreign_keys=[published_by], backref="project_template_versions_published")
    
    __table_args__ = (
        Index("idx_project_template_version_template", "template_id"),
        Index("idx_project_template_version_status", "status"),
        Index("idx_project_template_version_unique", "template_id", "version_no", unique=True),
    )
    
    def __repr__(self):
        return f"<ProjectTemplateVersion {self.template_id}-{self.version_no}>"


class ProjectMemberContribution(Base, TimestampMixin):
    """项目成员贡献度表"""
    __tablename__ = "project_member_contributions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    period = Column(String(7), nullable=False, comment="统计周期 YYYY-MM")
    
    # 工作量指标
    task_count = Column(Integer, default=0, comment="完成任务数")
    task_hours = Column(Numeric(10, 2), default=0, comment="任务工时")
    actual_hours = Column(Numeric(10, 2), default=0, comment="实际投入工时")
    
    # 质量指标
    deliverable_count = Column(Integer, default=0, comment="交付物数量")
    issue_count = Column(Integer, default=0, comment="问题数")
    issue_resolved = Column(Integer, default=0, comment="解决问题数")
    
    # 贡献度评分
    contribution_score = Column(Numeric(5, 2), comment="贡献度评分")
    pm_rating = Column(Integer, comment="项目经理评分 1-5")
    
    # 奖金关联
    bonus_amount = Column(Numeric(14, 2), default=0, comment="项目奖金金额")
    
    # 关系
    project = relationship("Project")
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index("idx_project_member_contrib_project", "project_id"),
        Index("idx_project_member_contrib_user", "user_id"),
        Index("idx_project_member_contrib_period", "period"),
        UniqueConstraint("project_id", "user_id", "period"),
    )
    
    def __repr__(self):
        return f"<ProjectMemberContribution {self.project_id}-{self.user_id}-{self.period}>"
