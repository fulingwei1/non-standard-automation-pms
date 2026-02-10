# -*- coding: utf-8 -*-
"""
售前费用管理 API endpoints
"""

from datetime import date
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.presale_expense import PresaleExpense
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.labor_cost_service import LaborCostExpenseService
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


class ExpenseLostProjectsRequest(BaseModel):
    """费用化未中标项目请求"""
    project_ids: Optional[List[int]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


@router.post("/expenses/expense-lost-projects", response_model=ResponseModel)
def expense_lost_projects(
    request: ExpenseLostProjectsRequest = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    将未中标项目工时费用化
    """
    service = LaborCostExpenseService(db)
    result = service.expense_lost_projects(
        project_ids=request.project_ids,
        start_date=request.start_date,
        end_date=request.end_date,
        created_by=current_user.id
    )

    # 将费用写入数据库
    expenses_created = []
    for expense_data in result['expenses']:
        # 获取项目信息
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == expense_data['project_id']).first()

        expense = PresaleExpense(
            project_id=expense_data['project_id'],
            project_code=expense_data.get('project_code') or (project.project_code if project else None),
            project_name=expense_data.get('project_name') or (project.project_name if project else None),
            lead_id=expense_data.get('lead_id'),
            opportunity_id=expense_data.get('opportunity_id'),
            expense_type=expense_data['expense_type'],
            expense_category=expense_data['expense_category'],
            amount=Decimal(str(expense_data['amount'])),
            labor_hours=expense_data.get('labor_hours'),
            hourly_rate=expense_data.get('hourly_rate'),
            user_id=expense_data.get('user_id'),
            user_name=expense_data.get('user_name'),
            department_id=expense_data.get('department_id'),
            department_name=expense_data.get('department_name'),
            salesperson_id=expense_data.get('salesperson_id'),
            salesperson_name=expense_data.get('salesperson_name'),
            expense_date=expense_data['expense_date'],
            description=expense_data.get('description'),
            loss_reason=expense_data.get('loss_reason'),
            created_by=expense_data.get('created_by') or current_user.id
        )
        db.add(expense)
        expenses_created.append(expense)

    db.commit()

    return ResponseModel(
        code=200,
        message=f"成功费用化 {len(expenses_created)} 条记录",
        data={
            'total_projects': result['total_projects'],
            'total_expenses': len(expenses_created),
            'total_amount': result['total_amount'],
            'total_hours': result['total_hours']
        }
    )


@router.get("/expenses/lost-project-expenses", response_model=ResponseModel)
def get_lost_project_expenses(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    salesperson_id: Optional[int] = Query(None, description="销售人员ID"),
    department_id: Optional[int] = Query(None, description="部门ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取未中标项目费用列表
    """
    # 如果指定了project_id，直接从数据库查询
    if project_id:
        expenses = db.query(PresaleExpense).filter(
            PresaleExpense.project_id == project_id
        ).all()

        expense_list = []
        total_amount = Decimal('0')
        total_hours = 0.0

        for exp in expenses:
            expense_list.append({
                'id': exp.id,
                'project_id': exp.project_id,
                'project_code': exp.project_code,
                'project_name': exp.project_name,
                'expense_category': exp.expense_category,
                'labor_hours': float(exp.labor_hours or 0),
                'amount': float(exp.amount),
                'expense_date': exp.expense_date.isoformat() if exp.expense_date else None,
                'salesperson_id': exp.salesperson_id,
                'salesperson_name': exp.salesperson_name,
                'loss_reason': exp.loss_reason,
                'description': exp.description
            })
            total_amount += exp.amount
            total_hours += float(exp.labor_hours or 0)

        return ResponseModel(
            code=200,
            message="查询成功",
            data={
                'items': expense_list,
                'total': len(expense_list),
                'page': 1,
                'page_size': len(expense_list),
                'total_pages': 1,
                'summary': {
                    'total_amount': float(total_amount),
                    'total_hours': round(total_hours, 1)
                }
            }
        )

    # 否则使用服务计算
    service = LaborCostExpenseService(db)
    result = service.get_lost_project_expenses(
        start_date=start_date,
        end_date=end_date,
        salesperson_id=salesperson_id,
        department_id=department_id
    )

    # 分页
    total = len(result['expenses'])
    paginated_expenses = result['expenses'][offset:offset + page_size]

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            'items': paginated_expenses,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'summary': {
                'total_amount': result['total_amount'],
                'total_hours': result['total_hours']
            }
        }
    )


@router.get("/expenses/expense-statistics", response_model=ResponseModel)
def get_expense_statistics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    group_by: str = Query('person', description="分组方式：person/department/time"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取费用统计（按人员、按部门、按时间）
    """
    service = LaborCostExpenseService(db)
    result = service.get_expense_statistics(
        start_date=start_date,
        end_date=end_date,
        group_by=group_by
    )

    return ResponseModel(
        code=200,
        message="查询成功",
        data=result
    )
