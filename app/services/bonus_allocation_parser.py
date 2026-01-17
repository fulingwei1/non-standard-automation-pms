# -*- coding: utf-8 -*-
"""
奖金分配表解析服务
"""

import io
import os
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.bonus import BonusCalculation, TeamBonusAllocation
from app.models.user import User


def validate_file_type(filename: str) -> None:
    """
    验证文件类型

    Raises:
        HTTPException: 如果文件类型不支持
    """
    if not filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")


def save_uploaded_file(file: UploadFile) -> Tuple[str, str, int]:
    """
    保存上传的文件

    Returns:
        Tuple[str, str, int]: (文件路径, 相对路径, 文件大小)
    """
    upload_dir = os.path.join(settings.UPLOAD_DIR, "bonus_allocation_sheets")
    os.makedirs(upload_dir, exist_ok=True)

    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    relative_path = os.path.relpath(file_path, settings.UPLOAD_DIR)

    return file_path, relative_path, 0  # 文件大小将在读取后更新


async def read_and_save_file(file: UploadFile, file_path: str) -> Tuple[bytes, int]:
    """
    读取并保存文件

    Returns:
        Tuple[bytes, int]: (文件内容, 文件大小)
    """
    file_content = await file.read()
    file_size = len(file_content)

    with open(file_path, "wb") as f:
        f.write(file_content)

    return file_content, file_size


def parse_excel_file(file_content: bytes) -> pd.DataFrame:
    """
    解析Excel文件

    Returns:
        pd.DataFrame: 解析后的数据框
    """
    try:
        df = pd.read_excel(io.BytesIO(file_content))
        df = df.dropna(how='all')  # 删除空行
        return df
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel文件解析失败: {str(e)}")


def validate_required_columns(df: pd.DataFrame) -> None:
    """
    验证必需的列

    Raises:
        HTTPException: 如果缺少必需的列
    """
    # 验证必需列（支持两种模式）
    has_calculation_id = '计算记录ID*' in df.columns or '计算记录ID' in df.columns
    has_allocation_id = '团队奖金分配ID*' in df.columns or '团队奖金分配ID' in df.columns

    if not has_calculation_id and not has_allocation_id:
        raise HTTPException(
            status_code=400,
            detail="Excel文件必须包含'计算记录ID*'或'团队奖金分配ID*'列之一"
        )

    # 验证其他必需列
    required_columns = ['受益人ID*', '发放金额*', '发放日期*']
    missing_columns = []
    for col in required_columns:
        if col not in df.columns:
            alt_col = col.replace('*', '')
            if alt_col not in df.columns:
                missing_columns.append(col)

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Excel文件缺少必需的列：{', '.join(missing_columns)}"
        )


def get_column_value(row: pd.Series, primary_col: str, alt_col: str = None) -> Any:
    """
    获取列值（支持带*和不带*的列名）

    Returns:
        Any: 列值
    """
    if alt_col is None:
        alt_col = primary_col.replace('*', '')
    return row.get(primary_col) or row.get(alt_col)


def parse_row_data(
    row: pd.Series,
    row_num: int,
    db: Session
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    解析单行数据

    Returns:
        Tuple[Optional[Dict], List[str]]: (有效数据, 错误列表)
    """
    errors = []

    try:
        # 获取计算记录ID或团队奖金分配ID
        calc_id = None
        team_allocation_id = None

        calc_id_raw = get_column_value(row, '计算记录ID*', '计算记录ID')
        if not pd.isna(calc_id_raw):
            calc_id = int(float(calc_id_raw))

        allocation_id_raw = get_column_value(row, '团队奖金分配ID*', '团队奖金分配ID')
        if not pd.isna(allocation_id_raw):
            team_allocation_id = int(float(allocation_id_raw))

        if not calc_id and not team_allocation_id:
            errors.append("必须提供'计算记录ID'或'团队奖金分配ID'之一")

        # 获取受益人ID
        user_id_raw = get_column_value(row, '受益人ID*', '受益人ID')
        if pd.isna(user_id_raw):
            errors.append("受益人ID不能为空")
            return None, errors
        else:
            user_id = int(float(user_id_raw))

        # 获取计算金额（如果使用团队奖金分配ID，计算金额可选）
        calc_amount = None
        calc_amount_raw = get_column_value(row, '计算金额*', '计算金额')
        if not pd.isna(calc_amount_raw):
            calc_amount = Decimal(str(float(calc_amount_raw)))
        elif team_allocation_id:
            # 如果使用团队奖金分配ID，计算金额可以从分配记录中获取
            pass
        else:
            errors.append("计算金额不能为空")

        # 获取发放金额
        dist_amount_raw = get_column_value(row, '发放金额*', '发放金额')
        if pd.isna(dist_amount_raw):
            errors.append("发放金额不能为空")
            return None, errors
        else:
            dist_amount = Decimal(str(float(dist_amount_raw)))

        # 获取发放日期
        dist_date_raw = get_column_value(row, '发放日期*', '发放日期')
        if pd.isna(dist_date_raw):
            errors.append("发放日期不能为空")
            return None, errors
        else:
            dist_date = parse_date(dist_date_raw)

        # 可选字段
        user_name = row.get('受益人姓名', '')
        payment_method = row.get('发放方式', '')
        voucher_no = row.get('凭证号', '')
        payment_account = row.get('付款账户', '')
        payment_remark = row.get('付款备注', '')

        # 验证数据
        validation_errors = validate_row_data(
            db, calc_id, team_allocation_id, user_id, calc_amount, dist_amount
        )
        errors.extend(validation_errors)

        if errors:
            return None, errors

        # 如果使用团队奖金分配ID且没有提供计算金额，使用发放金额作为计算金额
        if team_allocation_id and calc_amount is None:
            calc_amount = dist_amount

        return {
            'calculation_id': calc_id,
            'team_allocation_id': team_allocation_id,
            'user_id': user_id,
            'user_name': str(user_name) if user_name else None,
            'calculated_amount': float(calc_amount),
            'distributed_amount': float(dist_amount),
            'distribution_date': dist_date.isoformat(),
            'payment_method': str(payment_method) if payment_method else None,
            'voucher_no': str(voucher_no) if voucher_no else None,
            'payment_account': str(payment_account) if payment_account else None,
            'payment_remark': str(payment_remark) if payment_remark else None,
        }, []

    except Exception as e:
        return None, [f"解析错误: {str(e)}"]


def parse_date(date_value: Any) -> date:
    """
    解析日期

    Returns:
        date: 解析后的日期对象
    """
    if isinstance(date_value, str):
        return datetime.strptime(date_value, '%Y-%m-%d').date()
    elif isinstance(date_value, datetime):
        return date_value.date()
    else:
        return pd.to_datetime(date_value).date()


def validate_row_data(
    db: Session,
    calc_id: Optional[int],
    team_allocation_id: Optional[int],
    user_id: int,
    calc_amount: Optional[Decimal],
    dist_amount: Decimal
) -> List[str]:
    """
    验证行数据

    Returns:
        List[str]: 错误列表
    """
    errors = []

    # 如果使用团队奖金分配ID，验证分配记录是否存在
    if team_allocation_id:
        allocation = db.query(TeamBonusAllocation).filter(
            TeamBonusAllocation.id == team_allocation_id
        ).first()
        if not allocation:
            errors.append(f"团队奖金分配ID {team_allocation_id} 不存在")
    else:
        # 验证计算记录是否存在
        if calc_id:
            calculation = db.query(BonusCalculation).filter(
                BonusCalculation.id == calc_id
            ).first()
            if not calculation:
                errors.append(f"计算记录ID {calc_id} 不存在")

    # 验证受益人是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        errors.append(f"受益人ID {user_id} 不存在")

    return errors


def parse_allocation_sheet(
    df: pd.DataFrame,
    db: Session
) -> Tuple[List[Dict[str, Any]], Dict[int, List[str]]]:
    """
    解析整个分配表

    Returns:
        Tuple[List[Dict], Dict[int, List[str]]]: (有效行数据, 错误字典)
    """
    valid_rows = []
    parse_errors = {}

    for idx, row in df.iterrows():
        row_num = idx + 2  # Excel行号（从2开始，第1行是表头）
        data, errors = parse_row_data(row, row_num, db)

        if errors:
            parse_errors[row_num] = errors
        else:
            valid_rows.append(data)

    return valid_rows, parse_errors
