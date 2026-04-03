# -*- coding: utf-8 -*-
"""
方案版本对比 API
端点：GET /solutions/{id}/compare
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.presale import PresaleSolution, PresaleSolutionCost
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/solutions", tags=["presale-solution-compare"])


def _solution_to_dict(sol: PresaleSolution, db: Session) -> dict:
    """将方案对象转为可比较的字典"""
    cost_items = (
        db.query(PresaleSolutionCost)
        .filter(PresaleSolutionCost.solution_id == sol.id)
        .order_by(PresaleSolutionCost.sort_order)
        .all()
    )
    return {
        "id": sol.id,
        "solution_no": sol.solution_no,
        "name": sol.name,
        "version": sol.version,
        "solution_type": sol.solution_type,
        "industry": sol.industry,
        "test_type": sol.test_type,
        "requirement_summary": sol.requirement_summary,
        "solution_overview": sol.solution_overview,
        "technical_spec": sol.technical_spec,
        "estimated_cost": float(sol.estimated_cost) if sol.estimated_cost else None,
        "suggested_price": float(sol.suggested_price) if sol.suggested_price else None,
        "estimated_hours": sol.estimated_hours,
        "estimated_duration": sol.estimated_duration,
        "status": sol.status,
        "author_name": sol.author_name,
        "created_at": str(sol.created_at) if sol.created_at else None,
        "cost_items": [
            {
                "category": c.category,
                "item_name": c.item_name,
                "specification": c.specification,
                "quantity": float(c.quantity) if c.quantity else None,
                "unit_price": float(c.unit_price) if c.unit_price else None,
                "amount": float(c.amount) if c.amount else None,
            }
            for c in cost_items
        ],
    }


def _compute_diff(old: dict, new: dict) -> dict:
    """计算两个版本之间的差异"""
    added = []
    removed = []
    modified = []

    # 比较顶层字段（排除 id, cost_items, created_at 等元数据字段）
    skip_keys = {"id", "solution_no", "cost_items", "created_at", "author_name"}
    all_keys = set(old.keys()) | set(new.keys())

    for key in all_keys:
        if key in skip_keys:
            continue
        old_val = old.get(key)
        new_val = new.get(key)
        if old_val != new_val:
            modified.append({
                "field": key,
                "old_value": old_val,
                "new_value": new_val,
            })

    # 比较成本明细
    old_costs = {c["item_name"]: c for c in old.get("cost_items", [])}
    new_costs = {c["item_name"]: c for c in new.get("cost_items", [])}

    for name in new_costs:
        if name not in old_costs:
            added.append({"type": "cost_item", "item": new_costs[name]})

    for name in old_costs:
        if name not in new_costs:
            removed.append({"type": "cost_item", "item": old_costs[name]})

    for name in old_costs:
        if name in new_costs and old_costs[name] != new_costs[name]:
            modified.append({
                "field": f"cost_item:{name}",
                "old_value": old_costs[name],
                "new_value": new_costs[name],
            })

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "summary": {
            "added_count": len(added),
            "removed_count": len(removed),
            "modified_count": len(modified),
        },
    }


def _build_timeline(solution: PresaleSolution, db: Session) -> list:
    """构建版本演进时间轴"""
    timeline = []

    # 从当前版本往上追溯所有祖先
    current = solution
    while current:
        timeline.append({
            "id": current.id,
            "version": current.version,
            "name": current.name,
            "status": current.status,
            "author_name": current.author_name,
            "created_at": str(current.created_at) if current.created_at else None,
        })
        if current.parent_id:
            current = db.query(PresaleSolution).filter(PresaleSolution.id == current.parent_id).first()
        else:
            current = None

    # 也找所有子版本
    children = (
        db.query(PresaleSolution)
        .filter(PresaleSolution.parent_id == solution.id)
        .order_by(PresaleSolution.created_at)
        .all()
    )
    for child in children:
        if child.id != solution.id:
            timeline.append({
                "id": child.id,
                "version": child.version,
                "name": child.name,
                "status": child.status,
                "author_name": child.author_name,
                "created_at": str(child.created_at) if child.created_at else None,
            })

    # 按 created_at 排序
    timeline.sort(key=lambda x: x.get("created_at") or "")
    return timeline


@router.get("/{solution_id}/compare", response_model=ResponseModel)
def compare_solution_versions(
    solution_id: int,
    compare_with: Optional[int] = Query(None, description="对比目标版本ID，不传则对比父版本"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案版本对比

    - 两个版本的内容差异对比
    - 变更摘要（新增/删除/修改）
    - 版本演进时间轴
    """
    solution = db.query(PresaleSolution).filter(PresaleSolution.id == solution_id).first()
    if not solution:
        return ResponseModel(code=404, message="方案不存在", data=None)

    # 确定对比目标
    if compare_with:
        target = db.query(PresaleSolution).filter(PresaleSolution.id == compare_with).first()
        if not target:
            return ResponseModel(code=404, message="对比目标版本不存在", data=None)
    elif solution.parent_id:
        target = (
            db.query(PresaleSolution)
            .filter(PresaleSolution.id == solution.parent_id)
            .first()
        )
        if not target:
            return ResponseModel(code=404, message="父版本不存在", data=None)
    else:
        return ResponseModel(
            code=400,
            message="该方案无父版本，请通过 compare_with 参数指定对比目标",
            data=None,
        )

    old_dict = _solution_to_dict(target, db)
    new_dict = _solution_to_dict(solution, db)
    diff = _compute_diff(old_dict, new_dict)
    timeline = _build_timeline(solution, db)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "current_version": new_dict,
            "compare_version": old_dict,
            "diff": diff,
            "timeline": timeline,
        },
    )
