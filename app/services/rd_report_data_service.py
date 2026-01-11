# -*- coding: utf-8 -*-
"""
研发费用报表数据服务

提取研发费用报表的数据查询和构建逻辑
"""

from typing import Dict, List, Any, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.rd_project import RdProject, RdCost, RdCostType
from app.models.timesheet import Timesheet
from app.models.user import User


def build_auxiliary_ledger_data(
    db: Session,
    year: int,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    构建研发费用辅助账数据
    
    Args:
        db: 数据库会话
        year: 年度
        project_id: 研发项目ID（可选）
    
    Returns:
        报表数据字典
    """
    query = db.query(RdCost).join(RdProject).filter(
        func.extract('year', RdCost.cost_date) == year
    )
    if project_id:
        query = query.filter(RdCost.rd_project_id == project_id)

    costs = query.order_by(RdCost.rd_project_id, RdCost.cost_date, RdCost.cost_type_id).all()

    details = []
    for cost in costs:
        project = db.query(RdProject).filter(RdProject.id == cost.rd_project_id).first()
        cost_type = db.query(RdCostType).filter(RdCostType.id == cost.cost_type_id).first()
        details.append({
            "项目名称": project.project_name if project else "",
            "费用类型": cost_type.type_name if cost_type else "",
            "费用日期": str(cost.cost_date) if cost.cost_date else "",
            "费用单号": cost.cost_no or "",
            "费用说明": cost.cost_description or "",
            "费用金额": float(cost.cost_amount or 0),
            "可加计扣除": float(cost.deductible_amount or 0),
        })

    return {
        "details": details,
        "title": f"{year}年研发费用辅助账"
    }


def build_deduction_detail_data(
    db: Session,
    year: int,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    构建研发费用加计扣除明细数据
    
    Args:
        db: 数据库会话
        year: 年度
        project_id: 研发项目ID（可选）
    
    Returns:
        报表数据字典
    """
    query = db.query(RdCost).join(RdProject).filter(
        func.extract('year', RdCost.cost_date) == year,
        RdCost.deductible_amount > 0
    )
    if project_id:
        query = query.filter(RdCost.rd_project_id == project_id)

    costs = query.order_by(RdCost.rd_project_id, RdCost.cost_type_id).all()

    details = []
    for cost in costs:
        project = db.query(RdProject).filter(RdProject.id == cost.rd_project_id).first()
        cost_type = db.query(RdCostType).filter(RdCostType.id == cost.cost_type_id).first()
        details.append({
            "项目名称": project.project_name if project else "",
            "费用类型": cost_type.type_name if cost_type else "",
            "费用说明": cost.cost_description or "",
            "费用金额": float(cost.cost_amount or 0),
            "可加计扣除": float(cost.deductible_amount or 0),
        })

    total_deductible = sum(float(c.deductible_amount or 0) for c in costs)

    return {
        "summary": {"年度": year, "总可加计扣除": f"¥{total_deductible:,.2f}"},
        "details": details,
        "title": f"{year}年研发费用加计扣除明细"
    }


def build_high_tech_data(
    db: Session,
    year: int
) -> Dict[str, Any]:
    """
    构建高新企业研发费用表数据
    
    Args:
        db: 数据库会话
        year: 年度
    
    Returns:
        报表数据字典
    """
    costs = db.query(RdCost).join(RdProject).filter(
        func.extract('year', RdCost.cost_date) == year
    ).all()

    by_type = {}
    total_cost = 0

    for cost in costs:
        cost_type = db.query(RdCostType).filter(RdCostType.id == cost.cost_type_id).first()
        type_name = cost_type.type_name if cost_type else "其他"
        if type_name not in by_type:
            by_type[type_name] = 0
        by_type[type_name] += float(cost.cost_amount or 0)
        total_cost += float(cost.cost_amount or 0)

    details = [{"费用类型": k, "金额": f"¥{v:,.2f}"} for k, v in by_type.items()]

    return {
        "summary": {"年度": year, "研发费用总计": f"¥{total_cost:,.2f}"},
        "details": details,
        "title": f"{year}年高新企业研发费用表"
    }


def build_intensity_data(
    db: Session,
    year: int
) -> Dict[str, Any]:
    """
    构建研发投入强度报表数据
    
    Args:
        db: 数据库会话
        year: 年度
    
    Returns:
        报表数据字典
    """
    rd_costs = db.query(func.sum(RdCost.cost_amount)).filter(
        func.extract('year', RdCost.cost_date) == year
    ).scalar() or 0

    details = [{
        "年度": year,
        "研发费用": f"¥{float(rd_costs):,.2f}",
        "营业收入": "待从销售模块获取",
        "研发投入强度": "待计算",
    }]

    return {
        "details": details,
        "title": f"{year}年研发投入强度报表"
    }


def build_personnel_data(
    db: Session,
    year: int
) -> Dict[str, Any]:
    """
    构建研发人员统计数据
    
    Args:
        db: 数据库会话
        year: 年度
    
    Returns:
        报表数据字典
    """
    rd_projects = db.query(RdProject).filter(
        func.extract('year', RdProject.start_date) <= year,
        func.extract('year', RdProject.end_date) >= year
    ).all()

    rd_user_ids = set()
    for project in rd_projects:
        if project.linked_project_id:
            timesheets = db.query(Timesheet).filter(
                Timesheet.project_id == project.linked_project_id,
                func.extract('year', Timesheet.work_date) == year,
                Timesheet.status == 'APPROVED'
            ).all()
            rd_user_ids.update([ts.user_id for ts in timesheets])

    details = []
    for user_id in rd_user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            details.append({
                "姓名": user.real_name or user.username,
                "部门": user.department or "",
                "岗位": user.position or "",
            })

    all_users = db.query(User).filter(User.is_active == True).count()

    return {
        "summary": {
            "年度": year,
            "总人数": all_users,
            "研发人员数": len(rd_user_ids),
            "研发人员占比": f"{len(rd_user_ids) / all_users * 100:.1f}%" if all_users > 0 else "0%"
        },
        "details": details,
        "title": f"{year}年研发人员统计"
    }


def get_rd_report_data(
    db: Session,
    report_type: str,
    year: int,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    获取研发费用报表数据
    
    Args:
        db: 数据库会话
        report_type: 报表类型
        year: 年度
        project_id: 研发项目ID（可选）
    
    Returns:
        报表数据字典，包含 data 和 title 字段
    """
    if report_type == 'auxiliary-ledger':
        return build_auxiliary_ledger_data(db, year, project_id)
    elif report_type == 'deduction-detail':
        return build_deduction_detail_data(db, year, project_id)
    elif report_type == 'high-tech':
        return build_high_tech_data(db, year)
    elif report_type == 'intensity':
        return build_intensity_data(db, year)
    elif report_type == 'personnel':
        return build_personnel_data(db, year)
    else:
        raise ValueError(f"不支持的报表类型: {report_type}")
