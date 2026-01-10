# -*- coding: utf-8 -*-
"""
项目导入服务
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import date
from decimal import Decimal
import io

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project, Customer
from app.models.user import User
from app.utils.project_utils import init_project_stages


def validate_excel_file(filename: str) -> None:
    """
    验证Excel文件类型
    
    Raises:
        HTTPException: 如果文件类型不支持
    """
    if not filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")


def parse_excel_data(file_content: bytes) -> pd.DataFrame:
    """
    解析Excel文件
    
    Returns:
        pd.DataFrame: 解析后的数据框
    """
    try:
        df = pd.read_excel(io.BytesIO(file_content))
        df = df.dropna(how='all')  # 去除空行
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="文件中没有数据")
        
        return df
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel文件解析失败: {str(e)}")


def validate_project_columns(df: pd.DataFrame) -> None:
    """
    验证项目导入的必需列
    
    Raises:
        HTTPException: 如果缺少必需的列
    """
    required_columns = ['项目编码*', '项目名称*']
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


def get_column_value(row: pd.Series, primary_col: str, alt_col: str = None) -> Optional[str]:
    """
    获取列值（支持带*和不带*的列名）
    
    Returns:
        Optional[str]: 列值，如果为空则返回None
    """
    if alt_col is None:
        alt_col = primary_col.replace('*', '')
    
    value = row.get(primary_col) or row.get(alt_col)
    if pd.isna(value):
        return None
    return str(value).strip() if value else None


def parse_project_row(
    row: pd.Series,
    index: int
) -> Tuple[Optional[str], Optional[str], List[str]]:
    """
    解析项目行数据
    
    Returns:
        Tuple[Optional[str], Optional[str], List[str]]: (项目编码, 项目名称, 错误列表)
    """
    errors = []
    
    project_code = get_column_value(row, '项目编码*', '项目编码')
    project_name = get_column_value(row, '项目名称*', '项目名称')
    
    if not project_code or not project_name:
        errors.append("项目编码和项目名称不能为空")
        return None, None, errors
    
    return project_code, project_name, []


def find_or_create_customer(
    db: Session,
    customer_name: str
) -> Optional[Customer]:
    """
    查找或创建客户
    
    Returns:
        Optional[Customer]: 客户对象
    """
    if not customer_name:
        return None
    
    customer = db.query(Customer).filter(
        Customer.customer_name == customer_name
    ).first()
    
    return customer


def find_project_manager(
    db: Session,
    pm_name: str
) -> Optional[User]:
    """
    查找项目经理
    
    Returns:
        Optional[User]: 用户对象
    """
    if not pm_name:
        return None
    
    # 先按真实姓名查找
    pm = db.query(User).filter(User.real_name == pm_name).first()
    if not pm:
        # 再按用户名查找
        pm = db.query(User).filter(User.username == pm_name).first()
    
    return pm


def parse_date_value(value: Any) -> Optional[date]:
    """
    解析日期值
    
    Returns:
        Optional[date]: 解析后的日期对象
    """
    if pd.isna(value):
        return None
    
    try:
        return pd.to_datetime(value).date()
    except:
        return None


def parse_decimal_value(value: Any) -> Optional[Decimal]:
    """
    解析金额值
    
    Returns:
        Optional[Decimal]: 解析后的Decimal对象
    """
    if pd.isna(value):
        return None
    
    try:
        return Decimal(str(value))
    except:
        return None


def populate_project_from_row(
    db: Session,
    project: Project,
    row: pd.Series
) -> None:
    """
    从Excel行数据填充项目信息
    """
    # 客户信息
    customer_name = get_column_value(row, '客户名称')
    if customer_name:
        customer = find_or_create_customer(db, customer_name)
        if customer:
            project.customer_id = customer.id
            project.customer_name = customer_name
            project.customer_contact = customer.contact_person
            project.customer_phone = customer.contact_phone
    
    # 合同信息
    if pd.notna(row.get('合同编号')):
        project.contract_no = str(row.get('合同编号')).strip()
    
    if pd.notna(row.get('项目类型')):
        project.project_type = str(row.get('项目类型')).strip()
    
    contract_date = parse_date_value(row.get('合同日期'))
    if contract_date:
        project.contract_date = contract_date
    
    contract_amount = parse_decimal_value(row.get('合同金额'))
    if contract_amount:
        project.contract_amount = contract_amount
    
    budget_amount = parse_decimal_value(row.get('预算金额'))
    if budget_amount:
        project.budget_amount = budget_amount
    
    planned_start = parse_date_value(row.get('计划开始日期'))
    if planned_start:
        project.planned_start_date = planned_start
    
    planned_end = parse_date_value(row.get('计划结束日期'))
    if planned_end:
        project.planned_end_date = planned_end
    
    # 项目经理
    pm_name = get_column_value(row, '项目经理')
    if pm_name:
        pm = find_project_manager(db, pm_name)
        if pm:
            project.pm_id = pm.id
            project.pm_name = pm.real_name or pm.username
    
    # 项目描述
    if pd.notna(row.get('项目描述')):
        project.description = str(row.get('项目描述')).strip()


def import_projects_from_dataframe(
    db: Session,
    df: pd.DataFrame,
    update_existing: bool
) -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    从DataFrame导入项目
    
    Returns:
        Tuple[int, int, List[Dict]]: (导入数, 更新数, 失败行列表)
    """
    imported_count = 0
    updated_count = 0
    failed_rows = []
    
    for index, row in df.iterrows():
        try:
            project_code, project_name, errors = parse_project_row(row, index)
            
            if errors:
                failed_rows.append({
                    "row_index": index + 2,
                    "error": errors[0]
                })
                continue
            
            # 检查项目是否已存在
            existing_project = db.query(Project).filter(
                Project.project_code == project_code
            ).first()
            
            if existing_project:
                if not update_existing:
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": f"项目编码 {project_code} 已存在"
                    })
                    continue
                
                # 更新现有项目
                project = existing_project
                populate_project_from_row(db, project, row)
                updated_count += 1
            else:
                # 创建新项目
                project = Project(
                    project_code=project_code,
                    project_name=project_name,
                    stage="S1",
                    status="ST01",
                    health="H1",
                    is_active=True
                )
                
                populate_project_from_row(db, project, row)
                db.add(project)
                db.flush()
                
                # 初始化项目阶段
                init_project_stages(db, project.id)
                imported_count += 1
        
        except Exception as e:
            failed_rows.append({
                "row_index": index + 2,
                "error": str(e)
            })
    
    return imported_count, updated_count, failed_rows
