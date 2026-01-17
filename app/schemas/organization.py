# -*- coding: utf-8 -*-
"""
组织架构 Schema
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from .common import TimestampSchema


class DepartmentCreate(BaseModel):
    """创建部门"""

    dept_code: str = Field(max_length=20, description="部门编码")
    dept_name: str = Field(max_length=50, description="部门名称")
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None
    level: int = 1
    sort_order: int = 0


class DepartmentUpdate(BaseModel):
    """更新部门"""

    dept_name: Optional[str] = None
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None
    level: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class DepartmentResponse(TimestampSchema):
    """部门响应"""

    id: int
    dept_code: str
    dept_name: str
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None
    level: int
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    """创建员工"""

    employee_code: str = Field(max_length=10, description="工号")
    name: str = Field(max_length=50, description="姓名")
    department: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    wechat_userid: Optional[str] = None


class EmployeeUpdate(BaseModel):
    """更新员工"""

    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    wechat_userid: Optional[str] = None
    is_active: Optional[bool] = None


class EmployeeResponse(TimestampSchema):
    """员工响应"""

    id: int
    employee_code: str
    name: str
    department: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    wechat_userid: Optional[str] = None
    is_active: bool
    employment_status: Optional[str] = None
    employment_type: Optional[str] = None
    id_card: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 人事档案 Schema ====================


class EmployeeHrProfileCreate(BaseModel):
    """创建人事档案"""

    employee_id: int = Field(description="员工ID")
    # 组织信息
    dept_level1: Optional[str] = Field(None, max_length=50, description="一级部门")
    dept_level2: Optional[str] = Field(None, max_length=50, description="二级部门")
    dept_level3: Optional[str] = Field(None, max_length=50, description="三级部门")
    direct_supervisor: Optional[str] = Field(None, max_length=50, description="直接上级")
    position: Optional[str] = Field(None, max_length=100, description="职务")
    job_level: Optional[str] = Field(None, max_length=50, description="级别")
    # 入职相关
    hire_date: Optional[date] = Field(None, description="入职时间")
    probation_end_date: Optional[date] = Field(None, description="转正日期")
    is_confirmed: Optional[bool] = Field(False, description="是否转正")
    contract_sign_date: Optional[date] = Field(None, description="合同签订日期")
    contract_end_date: Optional[date] = Field(None, description="合同到期日")
    # 个人基本信息
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    birth_date: Optional[date] = Field(None, description="出生年月")
    age: Optional[int] = Field(None, description="年龄")
    ethnicity: Optional[str] = Field(None, max_length=20, description="民族")
    political_status: Optional[str] = Field(None, max_length=20, description="政治面貌")
    marital_status: Optional[str] = Field(None, max_length=20, description="婚姻状况")
    height_cm: Optional[Decimal] = Field(None, description="身高(cm)")
    weight_kg: Optional[Decimal] = Field(None, description="体重(kg)")
    native_place: Optional[str] = Field(None, max_length=50, description="籍贯")
    # 联系地址
    home_address: Optional[str] = Field(None, max_length=200, description="家庭住址")
    current_address: Optional[str] = Field(None, max_length=200, description="目前住址")
    emergency_contact: Optional[str] = Field(None, max_length=50, description="紧急联系人")
    emergency_phone: Optional[str] = Field(None, max_length=20, description="紧急联系电话")
    # 教育背景
    graduate_school: Optional[str] = Field(None, max_length=100, description="毕业院校")
    graduate_date: Optional[str] = Field(None, max_length=20, description="毕业时间")
    major: Optional[str] = Field(None, max_length=100, description="所学专业")
    education_level: Optional[str] = Field(None, max_length=20, description="文化程度")
    foreign_language: Optional[str] = Field(None, max_length=50, description="外语程度")
    hobbies: Optional[str] = Field(None, max_length=200, description="特长爱好")
    # 财务与社保
    bank_account: Optional[str] = Field(None, max_length=50, description="银行卡号")
    insurance_base: Optional[Decimal] = Field(None, description="保险基数")
    social_security_no: Optional[str] = Field(None, max_length=50, description="社保号")
    housing_fund_no: Optional[str] = Field(None, max_length=50, description="公积金号")
    # 离职信息
    resignation_date: Optional[date] = Field(None, description="离职日期")
    old_department: Optional[str] = Field(None, max_length=100, description="部门（旧）")


class EmployeeHrProfileUpdate(BaseModel):
    """更新人事档案"""

    # 组织信息
    dept_level1: Optional[str] = None
    dept_level2: Optional[str] = None
    dept_level3: Optional[str] = None
    direct_supervisor: Optional[str] = None
    position: Optional[str] = None
    job_level: Optional[str] = None
    # 入职相关
    hire_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    is_confirmed: Optional[bool] = None
    contract_sign_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    # 个人基本信息
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    age: Optional[int] = None
    ethnicity: Optional[str] = None
    political_status: Optional[str] = None
    marital_status: Optional[str] = None
    height_cm: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None
    native_place: Optional[str] = None
    # 联系地址
    home_address: Optional[str] = None
    current_address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    # 教育背景
    graduate_school: Optional[str] = None
    graduate_date: Optional[str] = None
    major: Optional[str] = None
    education_level: Optional[str] = None
    foreign_language: Optional[str] = None
    hobbies: Optional[str] = None
    # 财务与社保
    bank_account: Optional[str] = None
    insurance_base: Optional[Decimal] = None
    social_security_no: Optional[str] = None
    housing_fund_no: Optional[str] = None
    # 离职信息
    resignation_date: Optional[date] = None
    old_department: Optional[str] = None


class EmployeeHrProfileResponse(TimestampSchema):
    """人事档案响应"""

    id: int
    employee_id: int
    # 组织信息
    dept_level1: Optional[str] = None
    dept_level2: Optional[str] = None
    dept_level3: Optional[str] = None
    direct_supervisor: Optional[str] = None
    position: Optional[str] = None
    job_level: Optional[str] = None
    # 入职相关
    hire_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    is_confirmed: Optional[bool] = None
    contract_sign_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    # 个人基本信息
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    age: Optional[int] = None
    ethnicity: Optional[str] = None
    political_status: Optional[str] = None
    marital_status: Optional[str] = None
    height_cm: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None
    native_place: Optional[str] = None
    # 联系地址
    home_address: Optional[str] = None
    current_address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    # 教育背景
    graduate_school: Optional[str] = None
    graduate_date: Optional[str] = None
    major: Optional[str] = None
    education_level: Optional[str] = None
    foreign_language: Optional[str] = None
    hobbies: Optional[str] = None
    # 财务与社保
    bank_account: Optional[str] = None
    insurance_base: Optional[Decimal] = None
    social_security_no: Optional[str] = None
    housing_fund_no: Optional[str] = None
    # 离职信息
    resignation_date: Optional[date] = None
    old_department: Optional[str] = None

    class Config:
        from_attributes = True


class EmployeeWithHrProfileResponse(EmployeeResponse):
    """带人事档案的员工响应"""

    hr_profile: Optional[EmployeeHrProfileResponse] = None

    class Config:
        from_attributes = True


# ==================== 人事事务 Schema ====================


class HrTransactionCreate(BaseModel):
    """创建人事事务"""

    employee_id: int = Field(description="员工ID")
    transaction_type: str = Field(description="事务类型: onboarding, resignation, confirmation, transfer, promotion, salary_adjustment")
    transaction_date: date = Field(description="事务生效日期")

    # 入职相关
    onboard_date: Optional[date] = None
    probation_months: Optional[int] = None
    initial_position: Optional[str] = None
    initial_department: Optional[str] = None
    initial_salary: Optional[Decimal] = None

    # 离职相关
    resignation_date: Optional[date] = None
    last_working_date: Optional[date] = None
    resignation_reason: Optional[str] = None
    resignation_remark: Optional[str] = None
    handover_to: Optional[int] = None

    # 转正相关
    confirmation_date: Optional[date] = None
    probation_evaluation: Optional[str] = None
    confirmation_salary: Optional[Decimal] = None

    # 调岗相关
    from_department: Optional[str] = None
    to_department: Optional[str] = None
    from_position: Optional[str] = None
    to_position: Optional[str] = None
    transfer_reason: Optional[str] = None

    # 晋升/调薪相关
    from_level: Optional[str] = None
    to_level: Optional[str] = None
    from_salary: Optional[Decimal] = None
    to_salary: Optional[Decimal] = None
    salary_change_ratio: Optional[Decimal] = None
    promotion_reason: Optional[str] = None

    remark: Optional[str] = None


class HrTransactionResponse(TimestampSchema):
    """人事事务响应"""

    id: int
    employee_id: int
    transaction_type: str
    transaction_date: date
    status: str

    # 入职相关
    onboard_date: Optional[date] = None
    probation_months: Optional[int] = None
    initial_position: Optional[str] = None
    initial_department: Optional[str] = None
    initial_salary: Optional[Decimal] = None

    # 离职相关
    resignation_date: Optional[date] = None
    last_working_date: Optional[date] = None
    resignation_reason: Optional[str] = None
    resignation_remark: Optional[str] = None
    handover_status: Optional[str] = None

    # 转正相关
    confirmation_date: Optional[date] = None
    probation_evaluation: Optional[str] = None
    confirmation_salary: Optional[Decimal] = None

    # 调岗相关
    from_department: Optional[str] = None
    to_department: Optional[str] = None
    from_position: Optional[str] = None
    to_position: Optional[str] = None

    # 晋升/调薪相关
    from_level: Optional[str] = None
    to_level: Optional[str] = None
    from_salary: Optional[Decimal] = None
    to_salary: Optional[Decimal] = None
    salary_change_ratio: Optional[Decimal] = None

    remark: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 合同管理 Schema ====================


class EmployeeContractCreate(BaseModel):
    """创建员工合同"""

    employee_id: int = Field(description="员工ID")
    contract_no: Optional[str] = Field(None, max_length=50, description="合同编号")
    contract_type: str = Field(description="合同类型: fixed_term, indefinite, project, intern, labor_dispatch")
    start_date: date = Field(description="合同开始日期")
    end_date: Optional[date] = Field(None, description="合同结束日期")
    duration_months: Optional[int] = Field(None, description="合同期限(月)")

    position: Optional[str] = None
    department: Optional[str] = None
    work_location: Optional[str] = None
    base_salary: Optional[Decimal] = None
    probation_salary: Optional[Decimal] = None
    probation_months: Optional[int] = None
    sign_date: Optional[date] = None
    contract_file: Optional[str] = None
    remark: Optional[str] = None


class EmployeeContractUpdate(BaseModel):
    """更新员工合同"""

    contract_no: Optional[str] = None
    contract_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_months: Optional[int] = None
    position: Optional[str] = None
    department: Optional[str] = None
    work_location: Optional[str] = None
    base_salary: Optional[Decimal] = None
    probation_salary: Optional[Decimal] = None
    probation_months: Optional[int] = None
    status: Optional[str] = None
    sign_date: Optional[date] = None
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None
    contract_file: Optional[str] = None
    remark: Optional[str] = None


class EmployeeContractResponse(TimestampSchema):
    """员工合同响应"""

    id: int
    employee_id: int
    contract_no: Optional[str] = None
    contract_type: str
    start_date: date
    end_date: Optional[date] = None
    duration_months: Optional[int] = None

    position: Optional[str] = None
    department: Optional[str] = None
    work_location: Optional[str] = None
    base_salary: Optional[Decimal] = None
    probation_salary: Optional[Decimal] = None
    probation_months: Optional[int] = None

    status: str
    sign_date: Optional[date] = None
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None

    is_renewed: bool
    renewal_count: int
    reminder_sent: bool
    contract_file: Optional[str] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class ContractReminderResponse(TimestampSchema):
    """合同到期提醒响应"""

    id: int
    contract_id: int
    employee_id: int
    reminder_type: str
    reminder_date: date
    contract_end_date: date
    days_until_expiry: Optional[int] = None
    status: str
    handle_action: Optional[str] = None
    handle_remark: Optional[str] = None

    class Config:
        from_attributes = True
