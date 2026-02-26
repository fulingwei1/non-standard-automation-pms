# -*- coding: utf-8 -*-
"""
HR档案导入服务
"""

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from app.models.organization import Employee, EmployeeHrProfile
from app.utils.common import (  # noqa: F401
    clean_decimal,
    clean_phone,
    clean_str,
    parse_date,
)


def validate_excel_file(filename: str) -> None:
    """
    验证Excel文件类型

    Raises:
        HTTPException: 如果文件类型无效
    """
    from fastapi import HTTPException

    if not filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传Excel文件（.xlsx或.xls格式）")


def validate_required_columns(df: pd.DataFrame) -> None:
    """
    验证必需列

    Raises:
        HTTPException: 如果缺少必需列
    """
    from fastapi import HTTPException

    if '姓名' not in df.columns:
        raise HTTPException(status_code=400, detail="Excel中必须包含'姓名'列")


def get_existing_employees(db: Session) -> Tuple[Dict[str, Employee], set]:
    """
    获取现有员工映射和工号集合

    Returns:
        Tuple[Dict[str, Employee], set]: (姓名到员工的映射, 现有工号集合)
    """
    existing_employees = db.query(Employee).all()
    name_to_employee = {clean_str(e.name): e for e in existing_employees}
    existing_codes = {e.employee_code for e in existing_employees}
    return name_to_employee, existing_codes


def generate_employee_code(existing_codes: set) -> str:
    """
    生成员工工号

    格式：EMP-xxxxx

    Returns:
        str: 员工工号
    """
    from app.utils.code_config import CODE_PREFIX, SEQ_LENGTH

    prefix = CODE_PREFIX['EMPLOYEE']
    seq_length = SEQ_LENGTH['EMPLOYEE']
    separator = '-'

    # 从现有编码中提取最大序号
    max_seq = 0
    pattern = f"{prefix}{separator}"
    for code in existing_codes:
        if code.startswith(pattern):
            try:
                parts = code.split(separator)
                if len(parts) == 2:
                    seq = int(parts[1])
                    max_seq = max(max_seq, seq)
            except (ValueError, IndexError):
                pass

    # 从最大序号+1开始
    code_idx = max_seq + 1
    employee_code = f"{prefix}{separator}{code_idx:0{seq_length}d}"

    # 确保不冲突
    while employee_code in existing_codes:
        code_idx += 1
        employee_code = f"{prefix}{separator}{code_idx:0{seq_length}d}"

    existing_codes.add(employee_code)
    return employee_code


def build_department_name(row: pd.Series) -> Optional[str]:
    """
    组合部门名称

    Returns:
        Optional[str]: 部门名称
    """
    dept_parts = []
    for col in ['一级部门', '二级部门', '三级部门']:
        val = clean_str(row.get(col))
        if val:
            dept_parts.append(val)
    return '-'.join(dept_parts) if dept_parts else None


def determine_employment_status(row: pd.Series) -> Tuple[str, bool]:
    """
    确定在职状态

    Returns:
        Tuple[str, bool]: (employment_status, is_active)
    """
    status_val = clean_str(row.get('在职离职状态'))
    if status_val in ['离职', '已离职']:
        return 'resigned', False
    elif status_val == '试用期':
        return 'active', True
    else:
        return 'active', True


def determine_employment_type(row: pd.Series) -> str:
    """
    确定员工类型

    Returns:
        str: employment_type
    """
    is_confirmed = clean_str(row.get('是否转正'))
    status_val = clean_str(row.get('在职离职状态'))
    if is_confirmed == '否' or status_val == '试用期':
        return 'probation'
    else:
        return 'regular'


def create_or_update_employee(
    db: Session,
    row: pd.Series,
    name: str,
    name_to_employee: Dict[str, Employee],
    existing_codes: set
) -> Tuple[Employee, bool]:
    """
    创建或更新员工

    Returns:
        Tuple[Employee, bool]: (员工对象, 是否为新创建)
    """
    employee = name_to_employee.get(name)

    if not employee:
        # 创建新员工
        employee_code = generate_employee_code(existing_codes)
        department = build_department_name(row)
        employment_status, is_active = determine_employment_status(row)
        employment_type = determine_employment_type(row)

        employee = Employee(
            employee_code=employee_code,
            name=name,
            department=department,
            role=clean_str(row.get('职务')),
            phone=clean_phone(row.get('联系方式')),
            is_active=is_active,
            employment_status=employment_status,
            employment_type=employment_type,
            id_card=clean_str(row.get('身份证号')),
        )
        db.add(employee)
        db.flush()
        name_to_employee[name] = employee
        return employee, True
    else:
        # 更新员工基本信息
        if row.get('联系方式'):
            employee.phone = clean_phone(row.get('联系方式'))
        if row.get('身份证号'):
            employee.id_card = clean_str(row.get('身份证号'))
        return employee, False


def update_hr_profile_from_row(
    db: Session,
    profile: EmployeeHrProfile,
    row: pd.Series
) -> None:
    """
    从Excel行更新人事档案
    """
    # 组织信息
    profile.dept_level1 = clean_str(row.get('一级部门'))
    profile.dept_level2 = clean_str(row.get('二级部门'))
    profile.dept_level3 = clean_str(row.get('三级部门'))
    profile.direct_supervisor = clean_str(row.get('直接上级'))
    profile.position = clean_str(row.get('职务'))
    profile.job_level = clean_str(row.get('级别'))

    # 入职相关
    profile.hire_date = parse_date(row.get('入职时间'))
    profile.probation_end_date = parse_date(row.get('转正日期'))
    profile.is_confirmed = clean_str(row.get('是否转正')) == '是'
    profile.contract_sign_date = parse_date(row.get('签订日期'))
    profile.contract_end_date = parse_date(row.get('合同到期日'))

    # 个人基本信息
    profile.gender = clean_str(row.get('性别'))
    profile.birth_date = parse_date(row.get('出生年月'))
    age_val = row.get('年龄')
    profile.age = int(age_val) if pd.notna(age_val) else None
    profile.ethnicity = clean_str(row.get('民族'))
    profile.political_status = clean_str(row.get('政治面貌'))
    profile.marital_status = clean_str(row.get('婚姻状况'))
    profile.height_cm = clean_decimal(row.get('身高cm'))
    profile.weight_kg = clean_decimal(row.get('体重kg'))
    profile.native_place = clean_str(row.get('籍贯'))

    # 联系地址
    profile.home_address = clean_str(row.get('家庭住址'))
    profile.current_address = clean_str(row.get('目前住址'))
    profile.emergency_contact = clean_str(row.get('紧急\n联系人'))
    profile.emergency_phone = clean_str(row.get('紧急联系\n电话'))

    # 教育背景
    profile.graduate_school = clean_str(row.get('毕业院校'))
    profile.graduate_date = clean_str(row.get('毕业时间'))
    profile.major = clean_str(row.get('所学专业'))
    profile.education_level = clean_str(row.get('文化\n程度'))
    profile.foreign_language = clean_str(row.get('外语\n程度'))
    profile.hobbies = clean_str(row.get('特长爱好'))

    # 财务与社保
    profile.bank_account = clean_str(row.get('招商银行卡号/中国工商银行卡'))
    profile.insurance_base = clean_decimal(row.get('保险\n基数'))
    profile.social_security_no = clean_str(row.get('社保号'))
    profile.housing_fund_no = clean_str(row.get('公积金号'))

    # 离职信息
    profile.resignation_date = parse_date(row.get('离职日期'))
    profile.old_department = clean_str(row.get('部门（旧）'))


def process_hr_profile_row(
    db: Session,
    row: pd.Series,
    idx: int,
    name_to_employee: Dict[str, Employee],
    existing_codes: set
) -> Tuple[Optional[int], Optional[str]]:
    """
    处理单行HR档案数据

    Returns:
        Tuple[Optional[int], Optional[str]]: (处理结果代码: 1=新增, 2=更新, 0=跳过, None=错误, 错误信息)
    """
    try:
        name = clean_str(row.get('姓名'))
        if not name:
            return 0, None  # 跳过

        # 创建或更新员工
        employee, is_new = create_or_update_employee(
            db, row, name, name_to_employee, existing_codes
        )

        # 创建或更新人事档案
        profile = db.query(EmployeeHrProfile).filter(
            EmployeeHrProfile.employee_id == employee.id
        ).first()

        if not profile:
            profile = EmployeeHrProfile(employee_id=employee.id)
            db.add(profile)

        # 更新档案数据
        update_hr_profile_from_row(db, profile, row)

        return (1 if is_new else 2), None  # 1=新增, 2=更新

    except Exception as e:
        return None, f"第{idx + 2}行处理失败: {str(e)}"


def import_hr_profiles_from_dataframe(
    db: Session,
    df: pd.DataFrame
) -> Dict[str, Any]:
    """
    从DataFrame导入HR档案数据

    Returns:
        Dict[str, Any]: 导入结果
    """
    # 获取现有员工
    name_to_employee, existing_codes = get_existing_employees(db)

    imported_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []

    for idx, row in df.iterrows():
        result_code, error = process_hr_profile_row(
            db, row, idx, name_to_employee, existing_codes
        )

        if error:
            errors.append(error)
        elif result_code == 1:
            imported_count += 1
        elif result_code == 2:
            updated_count += 1
        elif result_code == 0:
            skipped_count += 1

    return {
        "imported": imported_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "errors": errors[:10] if errors else []
    }
