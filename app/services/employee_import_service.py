# -*- coding: utf-8 -*-
"""
员工导入服务
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
import pandas as pd

from app.models.organization import Employee
from app.models.staff_matching import HrEmployeeProfile, HrTagDict, HrEmployeeTagEvaluation


def find_name_column(columns: List[str]) -> Optional[str]:
    """
    查找姓名列
    
    Returns:
        Optional[str]: 列名，如果未找到则返回None
    """
    for col in ['姓名', '名字', 'name', 'Name', '员工姓名']:
        if col in columns:
            return col
    return None


def find_department_columns(columns: List[str]) -> List[str]:
    """
    查找部门列
    
    Returns:
        List[str]: 部门列名列表
    """
    dept_cols = []
    for col in ['一级部门', '二级部门', '三级部门']:
        if col in columns:
            dept_cols.append(col)
    if not dept_cols and '部门' in columns:
        dept_cols = ['部门']
    return dept_cols


def find_other_columns(columns: List[str]) -> Dict[str, Optional[str]]:
    """
    查找其他列（职务、电话、状态等）
    
    Returns:
        Dict[str, Optional[str]]: 列名映射
    """
    position_col = next((c for c in ['职务', '岗位', '职位', 'position'] if c in columns), None)
    phone_col = next((c for c in ['联系方式', '手机', '电话', 'phone', '手机号'] if c in columns), None)
    status_col = next((c for c in ['在职离职状态', '状态', '在职状态'] if c in columns), None)
    
    return {
        'position': position_col,
        'phone': phone_col,
        'status': status_col
    }


def clean_name(val) -> Optional[str]:
    """清理姓名"""
    if pd.isna(val):
        return None
    result = str(val).strip()
    return result if result else None


def get_department_name(row: pd.Series, dept_cols: List[str]) -> Optional[str]:
    """
    获取部门名称
    
    Returns:
        Optional[str]: 部门名称
    """
    if not dept_cols:
        return None
    
    dept_parts = []
    for col in dept_cols:
        val = row.get(col)
        if pd.notna(val):
            val_str = str(val).strip()
            if val_str:
                dept_parts.append(val_str)
    
    return '-'.join(dept_parts) if dept_parts else None


def is_active_employee(status_val) -> bool:
    """
    判断员工是否在职
    
    Returns:
        bool: 是否在职
    """
    if pd.isna(status_val):
        return True
    
    status_str = str(status_val).strip()
    inactive_statuses = ['离职', '已离职', 'resigned', 'inactive']
    return status_str not in inactive_statuses


def generate_employee_code(code_idx: int, existing_codes: Set[str]) -> str:
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
    
    # 从最大序号+1开始，或使用传入的code_idx
    start_seq = max(max_seq + 1, code_idx)
    employee_code = f"{prefix}{separator}{start_seq:0{seq_length}d}"
    
    # 确保不冲突
    while employee_code in existing_codes:
        start_seq += 1
        employee_code = f"{prefix}{separator}{start_seq:0{seq_length}d}"
    
    return employee_code


def clean_phone(phone) -> Optional[str]:
    """清理电话号码"""
    if pd.isna(phone):
        return None
    phone_str = str(phone)
    if 'e' in phone_str.lower() or '.' in phone_str:
        try:
            phone_int = int(float(phone_str))
            phone_str = str(phone_int)
        except (ValueError, TypeError, OverflowError):
            pass
    return phone_str.strip() if phone_str.strip() else None


def create_hr_profile_for_employee(
    db: Session,
    employee: Employee,
    position: Optional[str],
    is_active: bool,
    evaluator_id: int,
    tag_dict: Dict[str, HrTagDict]
) -> None:
    """
    为员工创建HR档案并自动添加技能标签
    """
    now = datetime.now()
    today = now.date()
    
    # 创建员工档案
    profile = HrEmployeeProfile(
        employee_id=employee.id,
        skill_tags=[],
        domain_tags=[],
        attitude_tags=[],
        character_tags=[],
        special_tags=[],
        current_workload_pct=Decimal('0'),
        total_projects=0,
        profile_updated_at=now
    )
    db.add(profile)
    
    # 根据职位自动添加技能标签
    if position and is_active:
        skill_mappings = {
            'PLC': ['PLC编程'],
            '测试': ['ICT测试', 'FCT测试'],
            '机械': ['机械设计', '3D建模'],
            '电气': ['电气原理图'],
            '视觉': ['视觉系统'],
            '客服': ['故障排除', '现场经验'],
            '装配': ['装配调试'],
            'HMI': ['HMI开发'],
            '硬件': ['电气原理图'],
            '软件': ['PLC编程', 'HMI开发'],
        }
        
        matched_tags = set()
        for keyword, tag_names in skill_mappings.items():
            if keyword in position:
                for tag_name in tag_names:
                    if tag_name in tag_dict:
                        matched_tags.add(tag_name)
        
        for tag_name in matched_tags:
            tag = tag_dict.get(tag_name)
            if tag:
                eval_record = HrEmployeeTagEvaluation(
                    employee_id=employee.id,
                    tag_id=tag.id,
                    score=3,
                    evidence=f'根据职位 "{position}" 自动匹配',
                    evaluator_id=evaluator_id,
                    evaluate_date=today,
                    is_valid=True
                )
                db.add(eval_record)


def process_employee_row(
    db: Session,
    row: pd.Series,
    idx: int,
    name_col: str,
    dept_cols: List[str],
    column_map: Dict[str, Optional[str]],
    existing_map: Dict[Tuple[str, Optional[str]], Employee],
    existing_codes: Set[str],
    evaluator_id: int,
    tag_dict: Dict[str, HrTagDict]
) -> Tuple[Optional[int], Optional[str]]:
    """
    处理单行员工数据
    
    Returns:
        Tuple[Optional[int], Optional[str]]: (处理结果代码: 1=新增, 2=更新, 0=跳过, None=错误, 错误信息)
    """
    try:
        name = clean_name(row.get(name_col))
        if not name:
            return 0, None  # 跳过
        
        department = get_department_name(row, dept_cols) if dept_cols else None
        position = str(row.get(column_map['position'], '')).strip() if column_map['position'] and pd.notna(row.get(column_map['position'])) else None
        phone = clean_phone(row.get(column_map['phone'])) if column_map['phone'] else None
        is_active = is_active_employee(row.get(column_map['status'])) if column_map['status'] else True
        
        key = (name, department)
        
        if key in existing_map:
            # 更新现有员工
            employee = existing_map[key]
            if phone:
                employee.phone = phone
            if position:
                employee.role = position
            employee.is_active = is_active
            return 2, None  # 更新
        else:
            # 创建新员工
            employee_code = generate_employee_code(len(existing_codes) + 1, existing_codes)
            existing_codes.add(employee_code)
            
            employee = Employee(
                employee_code=employee_code,
                name=name,
                department=department,
                role=position,
                phone=phone,
                is_active=is_active
            )
            db.add(employee)
            db.flush()
            existing_map[key] = employee
            
            # 创建员工档案
            create_hr_profile_for_employee(
                db, employee, position, is_active, evaluator_id, tag_dict
            )
            
            return 1, None  # 新增
        
    except Exception as e:
        return None, f"第{idx + 2}行处理失败: {str(e)}"


def import_employees_from_dataframe(
    db: Session,
    df: pd.DataFrame,
    evaluator_id: int
) -> Dict[str, Any]:
    """
    从DataFrame导入员工数据
    
    Returns:
        Dict[str, Any]: 导入结果
    """
    # 检查必需列
    columns = df.columns.tolist()
    name_col = find_name_column(columns)
    if not name_col:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Excel中必须包含'姓名'列")
    
    # 识别列
    dept_cols = find_department_columns(columns)
    column_map = find_other_columns(columns)
    
    # 获取现有员工
    existing_employees = db.query(Employee).all()
    existing_map = {(e.name, e.department): e for e in existing_employees}
    existing_codes = {e.employee_code for e in existing_employees}
    
    # 获取标签字典
    tags = db.query(HrTagDict).filter(HrTagDict.is_active == True).all()
    tag_dict = {tag.tag_name: tag for tag in tags}
    
    imported_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []
    
    for idx, row in df.iterrows():
        result_code, error = process_employee_row(
            db, row, idx, name_col, dept_cols, column_map,
            existing_map, existing_codes, evaluator_id, tag_dict
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
