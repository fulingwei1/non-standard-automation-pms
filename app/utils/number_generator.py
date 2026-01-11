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
