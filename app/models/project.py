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
    machines = relationship("Machine", back_populates="project", lazy="dynamic")
    stages = relationship("ProjectStage", back_populates="project", lazy="dynamic")
    milestones = relationship(
        "ProjectMilestone", back_populates="project", lazy="dynamic"
    )
    members = relationship("ProjectMember", back_populates="project", lazy="dynamic")
    costs = relationship("ProjectCost", back_populates="project", lazy="dynamic")
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


class ProjectMember(Base, TimestampMixin):
    """项目成员表"""

    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    role_code = Column(String(50), nullable=False, comment="角色编码")

    # 分配信息
    allocation_pct = Column(Numeric(5, 2), default=100, comment="分配比例")
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")

    # 状态
    is_active = Column(Boolean, default=True)

    # 备注
    remark = Column(Text, comment="备注")

    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_project_members_project", "project_id"),
        Index("idx_project_members_user", "user_id"),
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


class ProjectDocument(Base, TimestampMixin):
    """项目文档表"""

    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="设备ID")
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
    machine = relationship("Machine")

    __table_args__ = (
        Index("idx_project_documents_project", "project_id"),
        Index("idx_project_documents_type", "doc_type"),
    )
