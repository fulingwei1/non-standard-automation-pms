# -*- coding: utf-8 -*-
"""
项目成本分摊模块

提供成本分摊到机台或项目的功能。
路由: /projects/{project_id}/costs/{cost_id}/allocate
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import ProjectCost
from app.models.user import User
from app.schemas.budget import ProjectCostAllocationRequest
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/{cost_id}/allocate", response_model=ResponseModel)
def allocate_cost(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Path(..., description="项目ID"),
    cost_id: int = Path(..., description="成本ID"),
    allocation_request: ProjectCostAllocationRequest,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    分摊成本到多个机台或项目
    验证成本记录属于指定项目
    """
    from app.services.cost_allocation_service import CostAllocationService

    # 验证成本记录存在且属于指定项目
    cost = db.query(ProjectCost).filter(
        ProjectCost.id == cost_id,
        ProjectCost.project_id == project_id
    ).first()
    if not cost:
        raise HTTPException(status_code=404, detail="成本记录不存在或不属于该项目")

    try:
        if allocation_request.rule_id:
            # 使用规则分摊
            allocated_costs = CostAllocationService.allocate_cost_by_rule(
                db, cost_id, allocation_request.rule_id, created_by=current_user.id
            )
        elif allocation_request.allocation_targets:
            # 手工分摊
            # 判断是分摊到机台还是项目
            first_target = allocation_request.allocation_targets[0]
            if "machine_id" in first_target:
                # 分摊到机台
                allocated_costs = CostAllocationService.allocate_cost_to_machines(
                    db, cost_id, allocation_request.allocation_targets, created_by=current_user.id
                )
            elif "project_id" in first_target:
                # 分摊到项目
                allocated_costs = CostAllocationService.allocate_cost_to_projects(
                    db, cost_id, allocation_request.allocation_targets, created_by=current_user.id
                )
            else:
                raise HTTPException(status_code=400, detail="allocation_targets必须包含machine_id或project_id")
        else:
            raise HTTPException(status_code=400, detail="必须提供rule_id或allocation_targets")

        db.commit()

        return ResponseModel(
            code=200,
            message=f"成功分摊成本，创建{len(allocated_costs)}条分摊记录",
            data={
                "allocated_count": len(allocated_costs),
                "allocated_costs": [
                    {
                        "id": cost.id,
                        "project_id": cost.project_id,
                        "machine_id": cost.machine_id,
                        "amount": float(cost.amount)
                    }
                    for cost in allocated_costs
                ]
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分摊失败：{str(e)}")
