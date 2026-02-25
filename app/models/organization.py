# -*- coding: utf-8 -*-
"""
组织架构模型 (员工、部门、人事档案、人事事务)
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin
from enum import Enum
from typing import List, TYPE_CHECKING
from sqlalchemy import JSON, Index, UniqueConstraint

if TYPE_CHECKING:
    pass


def __getattr__(name):
    """兼容导出：部分调用方从 organization 模块导入 Customer"""
    if name == "Customer":
        from app.models.project.customer import Customer
        return Customer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class Department(Base, TimestampMixin):
    """部门表"""

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dept_code = Column(String(20), unique=True, nullable=False, comment="部门编码")
    dept_name = Column(String(50), nullable=False, comment="部门名称")
    parent_id = Column(Integer, ForeignKey("departments.id"), comment="父部门ID")
    manager_id = Column(Integer, ForeignKey("employees.id"), comment="部门负责人ID")
    level = Column(Integer, default=1, comment="层级")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    parent = relationship("Department", remote_side=[id], backref="children")
    manager = relationship("Employee", foreign_keys=[manager_id])
    # projects relationship is defined in Project model with backref or manual

    def __repr__(self):
        return f"<Department {self.dept_name}>"


class Employee(Base, TimestampMixin):
    """员工表"""

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_code = Column(String(10), unique=True, nullable=False, comment="工号")
    name = Column(String(50), nullable=False, comment="姓名")
    department = Column(String(50), comment="部门")  # Legacy string field
    role = Column(String(50), comment="角色")
    phone = Column(String(20), comment="电话")
    wechat_userid = Column(String(50), comment="企业微信UserID")
    is_active = Column(Boolean, default=True, comment="是否在职")
    employment_status = Column(
        String(20), default="active", comment="在职状态: active(在职), resigned(离职)"
    )
    employment_type = Column(
        String(20),
        default="regular",
        comment="员工类型: regular(正式), probation(试用期), intern(实习期)",
    )
    id_card = Column(String(18), comment="身份证号")
    pinyin_name = Column(String(100), comment="姓名拼音")

    # 关系
    # user = relationship('User', back_populates='employee')
    hr_profile = relationship(
        "EmployeeHrProfile", back_populates="employee", uselist=False
    )

    def __repr__(self):
        return f"<Employee {self.name}>"


class EmployeeHrProfile(Base, TimestampMixin):
    """员工人事档案详情表"""

    __tablename__ = "employee_hr_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        unique=True,
        nullable=False,
        comment="员工ID",
    )

    # 组织信息
    dept_level1 = Column(String(50), comment="一级部门")
    dept_level2 = Column(String(50), comment="二级部门")
    dept_level3 = Column(String(50), comment="三级部门")
    direct_supervisor = Column(String(50), comment="直接上级")
    position = Column(String(100), comment="职务")
    job_level = Column(String(50), comment="级别")

    # 入职相关
    hire_date = Column(Date, comment="入职时间")
    probation_end_date = Column(Date, comment="转正日期")
    is_confirmed = Column(Boolean, default=False, comment="是否转正")
    contract_sign_date = Column(Date, comment="合同签订日期")
    contract_end_date = Column(Date, comment="合同到期日")

    # 个人基本信息
    gender = Column(String(10), comment="性别")
    birth_date = Column(Date, comment="出生年月")
    age = Column(Integer, comment="年龄")
    ethnicity = Column(String(20), comment="民族")
    political_status = Column(String(20), comment="政治面貌")
    marital_status = Column(String(20), comment="婚姻状况")
    height_cm = Column(Numeric(5, 1), comment="身高(cm)")
    weight_kg = Column(Numeric(5, 1), comment="体重(kg)")
    native_place = Column(String(50), comment="籍贯")

    # 联系地址
    home_address = Column(String(200), comment="家庭住址")
    current_address = Column(String(200), comment="目前住址")
    emergency_contact = Column(String(50), comment="紧急联系人")
    emergency_phone = Column(String(20), comment="紧急联系电话")

    # 教育背景
    graduate_school = Column(String(100), comment="毕业院校")
    graduate_date = Column(String(20), comment="毕业时间")
    major = Column(String(100), comment="所学专业")
    education_level = Column(String(20), comment="文化程度")
    foreign_language = Column(String(50), comment="外语程度")
    hobbies = Column(String(200), comment="特长爱好")

    # 财务与社保
    bank_account = Column(String(50), comment="银行卡号")
    insurance_base = Column(Numeric(10, 2), comment="保险基数")
    social_security_no = Column(String(50), comment="社保号")
    housing_fund_no = Column(String(50), comment="公积金号")

    # 离职信息
    resignation_date = Column(Date, comment="离职日期")
    old_department = Column(String(100), comment="部门（旧）")

    # 关系
    employee = relationship("Employee", back_populates="hr_profile")


class HrTransaction(Base, TimestampMixin):
    """人事事务记录表（入职、离职、转正、调岗、加薪晋级等）"""

    __tablename__ = "hr_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, comment="员工ID"
    )
    transaction_type = Column(
        String(20),
        nullable=False,
        comment="事务类型: onboarding(入职), resignation(离职), confirmation(转正), transfer(调岗), promotion(晋升), salary_adjustment(调薪)",
    )
    transaction_date = Column(Date, nullable=False, comment="事务生效日期")
    status = Column(
        String(20),
        default="pending",
        comment="状态: pending(待处理), approved(已批准), completed(已完成), rejected(已拒绝)",
    )

    # 入职相关
    onboard_date = Column(Date, comment="入职日期")
    probation_months = Column(Integer, comment="试用期月数")
    initial_position = Column(String(100), comment="初始职位")
    initial_department = Column(String(100), comment="初始部门")
    initial_salary = Column(Numeric(12, 2), comment="初始薪资")

    # 离职相关
    resignation_date = Column(Date, comment="离职日期")
    last_working_date = Column(Date, comment="最后工作日")
    resignation_reason = Column(
        String(50),
        comment="离职原因: personal(个人原因), career(职业发展), family(家庭原因), health(健康原因), salary(薪资待遇), environment(工作环境), layoff(裁员), contract_end(合同到期), other(其他)",
    )
    resignation_remark = Column(Text, comment="离职备注")
    handover_status = Column(
        String(20),
        comment="交接状态: pending(待交接), in_progress(交接中), completed(已完成)",
    )
    handover_to = Column(Integer, ForeignKey("employees.id"), comment="交接人ID")

    # 转正相关
    confirmation_date = Column(Date, comment="转正日期")
    probation_evaluation = Column(
        String(20),
        comment="试用期评价: excellent(优秀), good(良好), qualified(合格), unqualified(不合格)",
    )
    confirmation_salary = Column(Numeric(12, 2), comment="转正后薪资")

    # 调岗相关
    from_department = Column(String(100), comment="原部门")
    to_department = Column(String(100), comment="新部门")
    from_position = Column(String(100), comment="原职位")
    to_position = Column(String(100), comment="新职位")
    transfer_reason = Column(Text, comment="调岗原因")

    # 晋升/调薪相关
    from_level = Column(String(50), comment="原级别")
    to_level = Column(String(50), comment="新级别")
    from_salary = Column(Numeric(12, 2), comment="原薪资")
    to_salary = Column(Numeric(12, 2), comment="新薪资")
    salary_change_ratio = Column(Numeric(5, 2), comment="薪资变动比例(%)")
    promotion_reason = Column(Text, comment="晋升/调薪原因")

    # 审批相关
    applicant_id = Column(Integer, ForeignKey("users.id"), comment="申请人ID")
    approver_id = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approved_at = Column(DateTime, comment="审批时间")
    approval_remark = Column(Text, comment="审批备注")

    # 通用备注
    remark = Column(Text, comment="备注")
    attachments = Column(Text, comment="附件路径(JSON数组)")

    # 关系
    employee = relationship("Employee", foreign_keys=[employee_id])
    handover_employee = relationship("Employee", foreign_keys=[handover_to])

    def __repr__(self):
        return (
            f"<HrTransaction {self.transaction_type} for employee {self.employee_id}>"
        )


class EmployeeContract(Base, TimestampMixin):
    """员工合同表"""

    __tablename__ = "employee_contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, comment="员工ID"
    )
    contract_no = Column(String(50), comment="合同编号")
    contract_type = Column(
        String(20),
        nullable=False,
        comment="合同类型: fixed_term(固定期限), indefinite(无固定期限), project(项目制), intern(实习协议), labor_dispatch(劳务派遣)",
    )

    # 合同期限
    start_date = Column(Date, nullable=False, comment="合同开始日期")
    end_date = Column(Date, comment="合同结束日期")
    duration_months = Column(Integer, comment="合同期限(月)")

    # 合同内容
    position = Column(String(100), comment="合同约定职位")
    department = Column(String(100), comment="合同约定部门")
    work_location = Column(String(200), comment="工作地点")
    base_salary = Column(Numeric(12, 2), comment="基本工资")
    probation_salary = Column(Numeric(12, 2), comment="试用期工资")
    probation_months = Column(Integer, comment="试用期月数")

    # 状态
    status = Column(
        String(20),
        default="active",
        comment="状态: draft(草稿), active(生效中), expired(已到期), terminated(已终止), renewed(已续签)",
    )
    sign_date = Column(Date, comment="签订日期")
    termination_date = Column(Date, comment="终止日期")
    termination_reason = Column(Text, comment="终止原因")

    # 续签相关
    is_renewed = Column(Boolean, default=False, comment="是否已续签")
    renewed_contract_id = Column(
        Integer, ForeignKey("employee_contracts.id"), comment="续签合同ID"
    )
    renewal_count = Column(Integer, default=0, comment="续签次数")

    # 提醒相关
    reminder_sent = Column(Boolean, default=False, comment="是否已发送到期提醒")
    reminder_sent_at = Column(DateTime, comment="提醒发送时间")

    # 附件
    contract_file = Column(String(500), comment="合同扫描件路径")
    remark = Column(Text, comment="备注")

    # 关系
    employee = relationship("Employee", foreign_keys=[employee_id])
    renewed_contract = relationship("EmployeeContract", remote_side=[id])

    def __repr__(self):
        return f"<EmployeeContract {self.contract_no} for employee {self.employee_id}>"


class ContractReminder(Base, TimestampMixin):
    """合同到期提醒记录表"""

    __tablename__ = "contract_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(
        Integer, ForeignKey("employee_contracts.id"), nullable=False, comment="合同ID"
    )
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, comment="员工ID"
    )

    reminder_type = Column(
        String(20),
        nullable=False,
        comment="提醒类型: two_months(提前两月), one_month(提前一月), two_weeks(提前两周), expired(已到期)",
    )
    reminder_date = Column(Date, nullable=False, comment="提醒日期")
    contract_end_date = Column(Date, nullable=False, comment="合同到期日")
    days_until_expiry = Column(Integer, comment="距离到期天数")

    # 提醒状态
    status = Column(
        String(20),
        default="pending",
        comment="状态: pending(待处理), notified(已通知), handled(已处理), ignored(已忽略)",
    )
    handled_at = Column(DateTime, comment="处理时间")
    handled_by = Column(Integer, ForeignKey("users.id"), comment="处理人ID")
    handle_action = Column(
        String(20), comment="处理动作: renew(续签), terminate(终止), extend(延期)"
    )
    handle_remark = Column(Text, comment="处理备注")

    # 通知相关
    notified_at = Column(DateTime, comment="通知时间")
    notification_method = Column(
        String(50), comment="通知方式: email, wechat, sms, system"
    )

    # 关系
    contract = relationship("EmployeeContract")
    employee = relationship("Employee")

    def __repr__(self):
        return (
            f"<ContractReminder {self.reminder_type} for contract {self.contract_id}>"
        )


class SalaryRecord(Base, TimestampMixin):
    """薪资记录表（记录员工薪资变动历史）
    
    【状态】未启用 - 薪资记录"""
    __tablename__ = "salary_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, comment="员工ID"
    )

    # 薪资信息
    effective_date = Column(Date, nullable=False, comment="生效日期")
    base_salary = Column(Numeric(12, 2), nullable=False, comment="基本工资")
    position_allowance = Column(Numeric(10, 2), default=0, comment="岗位津贴")
    skill_allowance = Column(Numeric(10, 2), default=0, comment="技能津贴")
    performance_bonus = Column(Numeric(10, 2), default=0, comment="绩效奖金基数")
    other_allowance = Column(Numeric(10, 2), default=0, comment="其他补贴")
    total_salary = Column(Numeric(12, 2), comment="月薪总计")

    # 变动信息
    change_type = Column(
        String(20),
        comment="变动类型: initial(入职定薪), confirmation(转正调薪), promotion(晋升调薪), annual(年度调薪), special(特殊调薪)",
    )
    change_reason = Column(Text, comment="变动原因")
    previous_salary = Column(Numeric(12, 2), comment="变动前薪资")
    change_amount = Column(Numeric(12, 2), comment="变动金额")
    change_ratio = Column(Numeric(5, 2), comment="变动比例(%)")

    # 关联事务
    transaction_id = Column(
        Integer, ForeignKey("hr_transactions.id"), comment="关联人事事务ID"
    )

    # 状态
    is_current = Column(Boolean, default=True, comment="是否当前薪资")
    remark = Column(Text, comment="备注")

    # 关系
    employee = relationship("Employee")
    transaction = relationship("HrTransaction")

    def __repr__(self):
        return f"<SalaryRecord {self.base_salary} for employee {self.employee_id}>"


class OrganizationUnitType(str, Enum):
    """组织单元类型"""

    COMPANY = "COMPANY"  # 公司
    BUSINESS_UNIT = "BUSINESS_UNIT"  # 事业部
    DEPARTMENT = "DEPARTMENT"  # 部门
    TEAM = "TEAM"  # 团队


class PositionCategory(str, Enum):
    """岗位类别"""

    MANAGEMENT = "MANAGEMENT"  # 管理类
    TECHNICAL = "TECHNICAL"  # 技术类
    SUPPORT = "SUPPORT"  # 支持类
    SALES = "SALES"  # 销售类
    PRODUCTION = "PRODUCTION"  # 生产类


class JobLevelCategory(str, Enum):
    """职级序列"""

    P = "P"  # 专业序列
    M = "M"  # 管理序列
    T = "T"  # 技术序列


class AssignmentType(str, Enum):
    """员工分配类型"""

    PERMANENT = "PERMANENT"  # 正式分配
    TEMPORARY = "TEMPORARY"  # 临时借调
    PROJECT = "PROJECT"  # 项目分配


class OrganizationUnit(Base, TimestampMixin):
    """
    组织单元表
    支持公司/事业部/部门/团队的树形结构
    """

    __tablename__ = "organization_units"

    id = Column(Integer, primary_key=True, autoincrement=True)
    unit_code = Column(String(50), unique=True, nullable=False, comment="组织编码")
    unit_name = Column(String(100), nullable=False, comment="组织名称")
    unit_type = Column(
        String(20),
        nullable=False,
        comment="类型: COMPANY/BUSINESS_UNIT/DEPARTMENT/TEAM",
    )
    parent_id = Column(
        Integer, ForeignKey("organization_units.id"), comment="上级组织ID"
    )
    manager_id = Column(Integer, ForeignKey("employees.id"), comment="负责人ID")
    level = Column(Integer, default=1, comment="层级深度")
    path = Column(String(500), comment="路径(如: /1/3/5/)")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    parent = relationship("OrganizationUnit", remote_side=[id], backref="children")
    manager = relationship("Employee", foreign_keys=[manager_id])
    positions = relationship("Position", back_populates="org_unit")
    employee_assignments = relationship(
        "EmployeeOrgAssignment", back_populates="org_unit"
    )

    __table_args__ = (
        Index("idx_org_unit_type", "unit_type"),
        Index("idx_org_parent_id", "parent_id"),
        Index("idx_org_path", "path"),
        Index("idx_org_active", "is_active"),
    )

    def get_full_path_name(self) -> str:
        """获取完整路径名称"""
        names = [self.unit_name]
        parent = self.parent
        while parent:
            names.insert(0, parent.unit_name)
            parent = parent.parent
        return " / ".join(names)

    def get_all_children_ids(self) -> List[int]:
        """获取所有下级组织ID（包括自己）"""
        ids = [self.id]
        for child in self.children:
            ids.extend(child.get_all_children_ids())
        return ids

    def __repr__(self):
        return f"<OrganizationUnit {self.unit_name}>"


class Position(Base, TimestampMixin):
    """岗位表"""

    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_code = Column(String(50), unique=True, nullable=False, comment="岗位编码")
    position_name = Column(String(100), nullable=False, comment="岗位名称")
    position_category = Column(
        String(20),
        nullable=False,
        comment="类别: MANAGEMENT/TECHNICAL/SUPPORT/SALES/PRODUCTION",
    )
    org_unit_id = Column(
        Integer, ForeignKey("organization_units.id"), comment="所属组织单元ID"
    )
    description = Column(Text, comment="岗位描述")
    responsibilities = Column(JSON, comment="岗位职责")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")

    # 关系
    org_unit = relationship("OrganizationUnit", back_populates="positions")
    position_roles = relationship("PositionRole", back_populates="position")
    employee_assignments = relationship(
        "EmployeeOrgAssignment", back_populates="position"
    )

    __table_args__ = (
        Index("idx_position_category", "position_category"),
        Index("idx_position_org", "org_unit_id"),
        Index("idx_position_active", "is_active"),
    )

    def __repr__(self):
        return f"<Position {self.position_name}>"


class JobLevel(Base, TimestampMixin):
    """职级表"""

    __tablename__ = "job_levels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level_code = Column(String(20), unique=True, nullable=False, comment="职级编码")
    level_name = Column(String(50), nullable=False, comment="职级名称")
    level_category = Column(String(10), nullable=False, comment="序列: P/M/T")
    level_rank = Column(Integer, nullable=False, comment="职级数值")
    description = Column(Text, comment="职级描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")

    # 关系
    employee_assignments = relationship(
        "EmployeeOrgAssignment", back_populates="job_level"
    )

    def __repr__(self):
        return f"<JobLevel {self.level_code}>"


class EmployeeOrgAssignment(Base, TimestampMixin):
    """员工组织分配表"""

    __tablename__ = "employee_org_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        comment="员工ID",
    )
    org_unit_id = Column(
        Integer,
        ForeignKey("organization_units.id", ondelete="CASCADE"),
        nullable=False,
        comment="组织单元ID",
    )
    position_id = Column(
        Integer, ForeignKey("positions.id", ondelete="SET NULL"), comment="岗位ID"
    )
    job_level_id = Column(
        Integer, ForeignKey("job_levels.id", ondelete="SET NULL"), comment="职级ID"
    )
    is_primary = Column(Boolean, default=True, comment="是否主要归属")
    assignment_type = Column(
        String(20), default=AssignmentType.PERMANENT.value, comment="分配类型"
    )
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")
    is_active = Column(Boolean, default=True, comment="是否有效")

    # 关系
    employee = relationship("Employee", backref="org_assignments")
    org_unit = relationship("OrganizationUnit", back_populates="employee_assignments")
    position = relationship("Position", back_populates="employee_assignments")
    job_level = relationship("JobLevel", back_populates="employee_assignments")

    __table_args__ = (
        UniqueConstraint(
            "employee_id", "org_unit_id", "is_primary", name="uk_eoa_emp_org_primary"
        ),
    )


class PositionRole(Base):
    """岗位默认角色表"""

    __tablename__ = "position_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(
        Integer, ForeignKey("positions.id", ondelete="CASCADE"), nullable=False
    )
    role_id = Column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    is_active = Column(Boolean, default=True)

    # 关系
    position = relationship("Position", back_populates="position_roles")
    role = relationship("Role")
