# -*- coding: utf-8 -*-
"""
标准成本与项目集成端点
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.budget import ProjectBudget, ProjectBudgetItem
from app.models.project import Project
from app.models.standard_cost import StandardCost
from app.models.user import User
from app.schemas.standard_cost import (
    ApplyStandardCostRequest,
    ApplyStandardCostResponse,
    ProjectCostComparisonRequest,
    ProjectCostComparisonResponse,
    ProjectCostComparisonItem,
)

router = APIRouter()


def _generate_budget_no(db: Session) -> str:
    """生成预算编号"""
    from datetime import datetime
    today = datetime.now()
    prefix = f"BUD{today.strftime('%Y%m%d')}"
    
    # 查找当天最大序号
    last_budget = db.query(ProjectBudget).filter(
        ProjectBudget.budget_no.like(f"{prefix}%")
    ).order_by(ProjectBudget.budget_no.desc()).first()
    
    if last_budget and last_budget.budget_no:
        last_seq = int(last_budget.budget_no[-4:])
        new_seq = last_seq + 1
    else:
        new_seq = 1
    
    return f"{prefix}{new_seq:04d}"


def _generate_budget_version(db: Session, project_id: int) -> str:
    """生成预算版本号"""
    last_version = db.query(ProjectBudget).filter(
        ProjectBudget.project_id == project_id
    ).order_by(ProjectBudget.version.desc()).first()
    
    if last_version and last_version.version:
        try:
            last_num = int(last_version.version.replace('V', ''))
            new_num = last_num + 1
        except:
            new_num = 1
    else:
        new_num = 1
    
    return f"V{new_num}"


@router.post("/projects/{project_id}/costs/apply-standard", response_model=ApplyStandardCostResponse)
def apply_standard_cost_to_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    request: ApplyStandardCostRequest,
    current_user: User = Depends(security.require_permission("cost:manage")),
) -> Any:
    """
    应用标准成本到项目预算
    
    根据提供的成本项列表和数量，自动创建项目预算
    权限要求：cost:manage
    """
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 生成预算编号和版本
    budget_no = _generate_budget_no(db)
    version = _generate_budget_version(db, project_id)
    
    # 计算总金额并准备预算明细
    total_amount = Decimal('0')
    budget_items_data = []
    
    for idx, item in enumerate(request.cost_items, start=1):
        cost_code = item.get('cost_code')
        quantity = Decimal(str(item.get('quantity', 1)))
        
        # 查找标准成本
        standard_cost = db.query(StandardCost).filter(
            StandardCost.cost_code == cost_code,
            StandardCost.is_active == True
        ).first()
        
        if not standard_cost:
            raise HTTPException(
                status_code=404,
                detail=f"标准成本 {cost_code} 不存在或已停用"
            )
        
        # 计算金额
        item_amount = standard_cost.standard_cost * quantity
        total_amount += item_amount
        
        # 准备预算明细数据
        budget_items_data.append({
            'item_no': idx,
            'cost_category': standard_cost.cost_category,
            'cost_item': f"{standard_cost.cost_name}({standard_cost.cost_code})",
            'description': f"{standard_cost.specification or ''} {quantity}{standard_cost.unit}",
            'budget_amount': item_amount,
            'remark': f"标准成本：{standard_cost.standard_cost}/{standard_cost.unit}"
        })
    
    # 创建预算
    budget = ProjectBudget(
        budget_no=budget_no,
        project_id=project_id,
        budget_name=request.budget_name,
        budget_type="STANDARD_BASED",
        version=version,
        total_amount=total_amount,
        status="DRAFT",
        effective_date=request.effective_date or date.today(),
        is_active=True,
        created_by=current_user.id,
        remark=request.notes
    )
    db.add(budget)
    db.flush()
    
    # 创建预算明细
    for item_data in budget_items_data:
        item = ProjectBudgetItem(
            budget_id=budget.id,
            **item_data
        )
        db.add(item)
    
    db.commit()
    db.refresh(budget)
    
    return ApplyStandardCostResponse(
        budget_id=budget.id,
        budget_no=budget.budget_no,
        project_id=project_id,
        total_amount=total_amount,
        applied_items_count=len(budget_items_data),
        message=f"成功应用 {len(budget_items_data)} 项标准成本，创建预算 {budget_no}"
    )


@router.get("/projects/{project_id}/costs/compare-standard", response_model=ProjectCostComparisonResponse)
def compare_project_cost_with_standard(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    comparison_date: date = None,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    项目实际成本 vs 标准成本对比
    
    对比项目实际成本与标准成本的差异
    权限要求：cost:read
    """
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if comparison_date is None:
        comparison_date = date.today()
    
    # 获取项目预算（包含成本明细）
    budget = db.query(ProjectBudget).filter(
        ProjectBudget.project_id == project_id,
        ProjectBudget.status == "APPROVED"
    ).order_by(ProjectBudget.created_at.desc()).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="项目没有已批准的预算")
    
    # 构建对比数据
    comparison_items = []
    total_standard = Decimal('0')
    total_actual = Decimal('0')
    
    for item in budget.items:
        # 尝试从成本项名称中提取标准成本编码
        cost_code = None
        if '(' in item.cost_item and ')' in item.cost_item:
            cost_code = item.cost_item.split('(')[1].split(')')[0]
        
        if cost_code:
            # 查找对应的标准成本
            standard_cost = db.query(StandardCost).filter(
                StandardCost.cost_code == cost_code,
                StandardCost.is_active == True
            ).first()
            
            if standard_cost:
                standard_total = item.budget_amount
                actual_total = item.budget_amount  # 实际应从成本记录中获取
                
                variance = actual_total - standard_total if actual_total else None
                variance_rate = (variance / standard_total * 100) if variance and standard_total else None
                
                comparison_items.append(ProjectCostComparisonItem(
                    cost_code=standard_cost.cost_code,
                    cost_name=standard_cost.cost_name,
                    cost_category=standard_cost.cost_category,
                    unit=standard_cost.unit,
                    standard_cost=standard_cost.standard_cost,
                    actual_cost=standard_cost.standard_cost,  # 实际应从成本记录中获取
                    quantity=Decimal('1'),  # 实际应从成本记录中获取
                    standard_total=standard_total,
                    actual_total=actual_total,
                    variance=variance,
                    variance_rate=variance_rate
                ))
                
                total_standard += standard_total
                total_actual += actual_total if actual_total else Decimal('0')
    
    total_variance = total_actual - total_standard
    total_variance_rate = (total_variance / total_standard * 100) if total_standard else Decimal('0')
    
    return ProjectCostComparisonResponse(
        project_id=project_id,
        project_code=project.project_code,
        project_name=project.project_name,
        comparison_date=comparison_date,
        items=comparison_items,
        total_standard_cost=total_standard,
        total_actual_cost=total_actual,
        total_variance=total_variance,
        total_variance_rate=total_variance_rate
    )
