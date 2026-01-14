# -*- coding: utf-8 -*-
"""
编号生成工具

提供统一的业务编号生成功能，消除重复代码
"""

from typing import Type, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.ext.declarative import DeclarativeMeta

from app.utils.code_config import (
    CODE_PREFIX,
    SEQ_LENGTH,
    get_material_category_code,
    validate_material_category_code,
)


def generate_sequential_no(
    db: Session,
    model_class: Type,
    no_field: str,
    prefix: str,
    date_format: str = "%y%m%d",
    seq_length: int = 3,
    separator: str = "-",
    use_date: bool = True
) -> str:
    """
    生成顺序编号
    
    格式：{prefix}{date}{separator}{seq:0{seq_length}d}
    示例：ECN-250115-001, PJ250115001
    
    Args:
        db: 数据库会话
        model_class: 模型类
        no_field: 编号字段名
        prefix: 前缀（如 "ECN", "PJ"）
        date_format: 日期格式，默认 "%y%m%d"（年月日）
        seq_length: 序号长度，默认3位
        separator: 分隔符，默认 "-"
        use_date: 是否使用日期，默认True
    
    Returns:
        生成的编号字符串
    
    Example:
        ```python
        # 生成ECN编号：ECN-250115-001
        ecn_no = generate_sequential_no(
            db, Ecn, 'ecn_no', 'ECN', 
            date_format='%y%m%d', separator='-', seq_length=3
        )
        
        # 生成项目编码：PJ250115001
        project_code = generate_sequential_no(
            db, Project, 'project_code', 'PJ',
            date_format='%y%m%d', separator='', seq_length=3
        )
        ```
    """
    today = datetime.now()
    date_str = today.strftime(date_format)
    
    if use_date:
        if separator:
            pattern_prefix = f"{prefix}{separator}{date_str}{separator}"
        else:
            pattern_prefix = f"{prefix}{date_str}"
    else:
        pattern_prefix = f"{prefix}{separator}" if separator else prefix
    
    # 查询当天最大编号
    pattern = f"{pattern_prefix}%"
    max_record = (
        db.query(model_class)
        .filter(getattr(model_class, no_field).like(pattern))
        .order_by(desc(getattr(model_class, no_field)))
        .first()
    )
    
    if max_record:
        try:
            max_no = getattr(max_record, no_field)
            # 提取序号部分
            if separator:
                # 格式：PREFIX-DATE-SEQ
                parts = max_no.split(separator)
                seq_str = parts[-1] if parts else "0"
            else:
                # 格式：PREFIXDATESEQ
                seq_str = max_no[-seq_length:]
            
            seq = int(seq_str) + 1
        except (ValueError, IndexError, AttributeError):
            seq = 1
    else:
        seq = 1
    
    # 格式化序号
    seq_str = str(seq).zfill(seq_length)
    
    # 组合编号
    if use_date:
        if separator:
            return f"{prefix}{separator}{date_str}{separator}{seq_str}"
        else:
            return f"{prefix}{date_str}{seq_str}"
    else:
        if separator:
            return f"{prefix}{separator}{seq_str}"
        else:
            return f"{prefix}{seq_str}"


def generate_monthly_no(
    db: Session,
    model_class: Type,
    no_field: str,
    prefix: str,
    separator: str = "-",
    seq_length: int = 3
) -> str:
    """
    生成月度编号（按月递增）
    
    格式：{prefix}{yymm}{separator}{seq:0{seq_length}d}
    示例：L2507-001, O2507-001
    
    Args:
        db: 数据库会话
        model_class: 模型类
        no_field: 编号字段名
        prefix: 前缀（如 "L", "O"）
        separator: 分隔符，默认 "-"
        seq_length: 序号长度，默认3位
    
    Returns:
        生成的编号字符串
    
    Example:
        ```python
        # 生成线索编码：L2507-001
        lead_code = generate_monthly_no(
            db, Lead, 'lead_code', 'L'
        )
        ```
    """
    today = datetime.now()
    month_str = today.strftime("%y%m")
    pattern_prefix = f"{prefix}{month_str}{separator}"
    
    # 查询当月最大编号
    pattern = f"{pattern_prefix}%"
    max_record = (
        db.query(model_class)
        .filter(getattr(model_class, no_field).like(pattern))
        .order_by(desc(getattr(model_class, no_field)))
        .first()
    )
    
    if max_record:
        try:
            max_no = getattr(max_record, no_field)
            seq_str = max_no.split(separator)[-1]
            seq = int(seq_str) + 1
        except (ValueError, IndexError, AttributeError):
            seq = 1
    else:
        seq = 1
    
    seq_str = str(seq).zfill(seq_length)
    return f"{pattern_prefix}{seq_str}"


def generate_employee_code(db: Session) -> str:
    """
    生成员工编号
    
    格式：EMP-xxxxx
    示例：EMP-00001, EMP-00002
    
    Args:
        db: 数据库会话
    
    Returns:
        生成的员工编号字符串
    """
    from app.models.organization import Employee
    
    prefix = CODE_PREFIX['EMPLOYEE']
    seq_length = SEQ_LENGTH['EMPLOYEE']
    separator = '-'
    
    # 查询所有符合格式的编号
    pattern = f"{prefix}{separator}%"
    max_record = (
        db.query(Employee)
        .filter(Employee.employee_code.like(pattern))
        .order_by(desc(Employee.employee_code))
        .first()
    )
    
    if max_record:
        try:
            max_code = max_record.employee_code
            # 提取序号部分：EMP-00001 -> 00001
            parts = max_code.split(separator)
            if len(parts) == 2:
                seq_str = parts[1]
                seq = int(seq_str) + 1
            else:
                seq = 1
        except (ValueError, IndexError, AttributeError):
            seq = 1
    else:
        seq = 1
    
    # 格式化序号
    seq_str = str(seq).zfill(seq_length)
    return f"{prefix}{separator}{seq_str}"


def generate_customer_code(db: Session) -> str:
    """
    生成客户编号
    
    格式：CUS-xxxxxxx
    示例：CUS-0000001, CUS-0000002
    
    Args:
        db: 数据库会话
    
    Returns:
        生成的客户编号字符串
    """
    from app.models.project import Customer
    
    prefix = CODE_PREFIX['CUSTOMER']
    seq_length = SEQ_LENGTH['CUSTOMER']
    separator = '-'
    
    # 查询所有符合格式的编号
    pattern = f"{prefix}{separator}%"
    max_record = (
        db.query(Customer)
        .filter(Customer.customer_code.like(pattern))
        .order_by(desc(Customer.customer_code))
        .first()
    )
    
    if max_record:
        try:
            max_code = max_record.customer_code
            # 提取序号部分：CUS-0000001 -> 0000001
            parts = max_code.split(separator)
            if len(parts) == 2:
                seq_str = parts[1]
                seq = int(seq_str) + 1
            else:
                seq = 1
        except (ValueError, IndexError, AttributeError):
            seq = 1
    else:
        seq = 1
    
    # 格式化序号
    seq_str = str(seq).zfill(seq_length)
    return f"{prefix}{separator}{seq_str}"


def generate_material_code(db: Session, category_code: Optional[str] = None) -> str:
    """
    生成物料编号
    
    格式：MAT-{类别码}-xxxxx
    示例：MAT-ME-00001, MAT-EL-00015
    
    Args:
        db: 数据库会话
        category_code: 物料分类编码（如 'ME-01-01'），如果为None则使用'OT'
    
    Returns:
        生成的物料编号字符串
    """
    from app.models.material import Material
    
    prefix = CODE_PREFIX['MATERIAL']
    seq_length = SEQ_LENGTH['MATERIAL']
    separator = '-'
    
    # 从分类编码中提取类别码
    if category_code:
        material_category_code = get_material_category_code(category_code)
    else:
        material_category_code = 'OT'  # 默认其他
    
    # 构建查询模式：MAT-{类别码}-%
    pattern = f"{prefix}{separator}{material_category_code}{separator}%"
    
    # 查询该类别下的最大编号
    max_record = (
        db.query(Material)
        .filter(Material.material_code.like(pattern))
        .order_by(desc(Material.material_code))
        .first()
    )
    
    if max_record:
        try:
            max_code = max_record.material_code
            # 提取序号部分：MAT-ME-00001 -> 00001
            parts = max_code.split(separator)
            if len(parts) == 3 and parts[0] == prefix and parts[1] == material_category_code:
                seq_str = parts[2]
                seq = int(seq_str) + 1
            else:
                seq = 1
        except (ValueError, IndexError, AttributeError):
            seq = 1
    else:
        seq = 1
    
    # 格式化序号
    seq_str = str(seq).zfill(seq_length)
    return f"{prefix}{separator}{material_category_code}{separator}{seq_str}"
