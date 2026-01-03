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
    customer_short_name = Column(String(50), comment="客户简称")
    customer_type = Column(String(20), comment="客户类型")
    industry = Column(String(50), comment="所属行业")
    region = Column(String(100), comment="所在地区")
    address = Column(String(500), comment="详细地址")
    contact_person = Column(String(50), comment="联系人")
    contact_phone = Column(String(30), comment="联系电话")
    contact_email = Column(String(100), comment="联系邮箱")
    credit_level = Column(String(10), default="B", comment="信用等级")
    is_active = Column(Boolean, default=True, comment="是否启用")
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
    department = relationship("Department")
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
    """设备表"""

    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_code = Column(String(50), unique=True, nullable=False, comment="设备编号")
    machine_name = Column(String(200), nullable=False, comment="设备名称")
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )

    # 设备信息
    machine_type = Column(String(50), comment="设备类型")
    machine_model = Column(String(100), comment="设备型号")
    specification = Column(Text, comment="技术规格")
    serial_number = Column(String(100), comment="序列号")

    # 状态
    status = Column(String(20), default="PLANNING", comment="设备状态")
    current_stage = Column(String(10), default="S1", comment="当前阶段")
    progress_pct = Column(Integer, default=0, comment="进度(%)")

    # 时间
    planned_complete_date = Column(Date, comment="计划完成日期")
    actual_complete_date = Column(Date, comment="实际完成日期")
    ship_date = Column(Date, comment="发运日期")
    install_date = Column(Date, comment="安装日期")

    # 成本
    budget_cost = Column(Numeric(14, 2), default=0, comment="预算成本")
    actual_cost = Column(Numeric(14, 2), default=0, comment="实际成本")

    # 验收
    fat_date = Column(Date, comment="FAT日期")
    fat_result = Column(String(20), comment="FAT结果")
    sat_date = Column(Date, comment="SAT日期")
    sat_result = Column(String(20), comment="SAT结果")

    remark = Column(Text, comment="备注")

    # 关系
    project = relationship("Project", back_populates="machines")
    bom_headers = relationship("BomHeader", back_populates="machine", lazy="dynamic")

    __table_args__ = (
        Index("idx_machine_project", "project_id"),
        Index("idx_machine_status", "status"),
    )

    def __repr__(self):
        return f"<Machine {self.machine_code}>"


class ProjectStage(Base, TimestampMixin):
    """项目阶段表"""

    __tablename__ = "project_stages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    stage_code = Column(String(10), nullable=False, comment="阶段编码")
    stage_name = Column(String(50), nullable=False, comment="阶段名称")

    # 计划
    planned_start_date = Column(Date, comment="计划开始")
    planned_end_date = Column(Date, comment="计划结束")
    planned_days = Column(Integer, default=0, comment="计划工期")

    # 实际
    actual_start_date = Column(Date, comment="实际开始")
    actual_end_date = Column(Date, comment="实际结束")
    actual_days = Column(Integer, default=0, comment="实际工期")

    # 进度
    progress_pct = Column(Integer, default=0, comment="进度(%)")
    status = Column(String(20), default="PENDING", comment="状态")

    sort_order = Column(Integer, default=0, comment="排序")
    remark = Column(Text, comment="备注")

    # 关系
    project = relationship("Project", back_populates="stages")
    statuses = relationship("ProjectStatus", back_populates="stage", lazy="dynamic")

    __table_args__ = (Index("idx_stage_project", "project_id"),)

    def __repr__(self):
        return f"<ProjectStage {self.stage_code}>"


class ProjectStatus(Base, TimestampMixin):
    """项目状态表"""

    __tablename__ = "project_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_id = Column(
        Integer, ForeignKey("project_stages.id"), nullable=False, comment="阶段ID"
    )
    status_code = Column(String(20), nullable=False, comment="状态编码")
    status_name = Column(String(100), nullable=False, comment="状态名称")

    # 时间
    planned_date = Column(Date, comment="计划日期")
    actual_date = Column(Date, comment="实际日期")

    # 状态
    is_completed = Column(Boolean, default=False, comment="是否完成")
    completed_at = Column(DateTime, comment="完成时间")
    completed_by = Column(Integer, ForeignKey("users.id"), comment="完成人")

    sort_order = Column(Integer, default=0, comment="排序")
    remark = Column(Text, comment="备注")

    # 关系
    stage = relationship("ProjectStage", back_populates="statuses")

    __table_args__ = (Index("idx_status_stage", "stage_id"),)

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
    role_in_project = Column(String(50), nullable=False, comment="项目角色")
    responsibility = Column(String(200), comment="职责说明")
    join_date = Column(Date, comment="加入日期")
    leave_date = Column(Date, comment="退出日期")
    is_active = Column(Boolean, default=True, comment="是否在岗")
    workload_pct = Column(Integer, default=100, comment="投入比例(%)")

    # 关系
    project = relationship("Project", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        Index("idx_member_project", "project_id"),
        Index("idx_member_user", "user_id"),
    )


class ProjectMilestone(Base, TimestampMixin):
    """项目里程碑表"""

    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    milestone_type = Column(String(30), nullable=False, comment="里程碑类型")
    milestone_name = Column(String(200), nullable=False, comment="里程碑名称")

    # 时间
    planned_date = Column(Date, comment="计划日期")
    actual_date = Column(Date, comment="实际日期")
    reminder_days = Column(Integer, default=7, comment="提前提醒天数")

    # 状态
    status = Column(String(20), default="PENDING", comment="状态")
    is_key = Column(Boolean, default=False, comment="是否关键里程碑")

    # 关联
    related_stage = Column(String(10), comment="关联阶段")
    deliverable = Column(String(500), comment="交付物")

    completed_by = Column(Integer, ForeignKey("users.id"), comment="完成确认人")
    remark = Column(Text, comment="备注")

    # 关系
    project = relationship("Project", back_populates="milestones")

    __table_args__ = (
        Index("idx_milestone_project", "project_id"),
        Index("idx_milestone_status", "status"),
    )


class ProjectCost(Base, TimestampMixin):
    """项目成本表"""

    __tablename__ = "project_costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    cost_type = Column(String(30), nullable=False, comment="成本类型")
    cost_name = Column(String(200), nullable=False, comment="成本名称")
    cost_category = Column(String(50), comment="成本分类")

    # 金额
    budget_amount = Column(Numeric(14, 2), default=0, comment="预算金额")
    actual_amount = Column(Numeric(14, 2), default=0, comment="实际金额")
    variance_amount = Column(Numeric(14, 2), default=0, comment="差异金额")

    # 时间
    cost_date = Column(Date, comment="发生日期")
    cost_month = Column(String(7), comment="所属月份")

    # 关联
    related_order_type = Column(String(20), comment="关联单据类型")
    related_order_id = Column(Integer, comment="关联单据ID")
    related_order_no = Column(String(100), comment="关联单据号")

    remark = Column(Text, comment="备注")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    project = relationship("Project", back_populates="costs")

    __table_args__ = (
        Index("idx_cost_project", "project_id"),
        Index("idx_cost_type", "cost_type"),
    )


class ProjectDocument(Base, TimestampMixin):
    """项目文档表"""

    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    doc_type = Column(String(30), nullable=False, comment="文档类型")
    doc_name = Column(String(200), nullable=False, comment="文档名称")
    doc_no = Column(String(100), comment="文档编号")
    version = Column(String(20), default="1.0", comment="版本号")

    # 文件信息
    file_path = Column(String(500), comment="文件路径")
    file_size = Column(Integer, comment="文件大小")
    file_type = Column(String(50), comment="文件类型")

    # 状态
    status = Column(String(20), default="DRAFT", comment="状态")
    is_latest = Column(Boolean, default=True, comment="是否最新版本")

    # 阶段关联
    related_stage = Column(String(10), comment="关联阶段")

    remark = Column(Text, comment="备注")
    uploaded_by = Column(Integer, ForeignKey("users.id"), comment="上传人")

    # 关系
    project = relationship("Project", back_populates="documents")

    __table_args__ = (
        Index("idx_document_project", "project_id"),
        Index("idx_document_type", "doc_type"),
    )
