# -*- coding: utf-8 -*-
"""
项目风险管理
包含：风险CRUD、风险评估、风险跟踪
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.pmo import PmoProjectRisk
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


# 风险等级计算矩阵
RISK_LEVEL_MATRIX = {
    ("LOW", "LOW"): "LOW",
    ("LOW", "MEDIUM"): "LOW",
    ("LOW", "HIGH"): "MEDIUM",
    ("MEDIUM", "LOW"): "LOW",
    ("MEDIUM", "MEDIUM"): "MEDIUM",
    ("MEDIUM", "HIGH"): "HIGH",
    ("HIGH", "LOW"): "MEDIUM",
    ("HIGH", "MEDIUM"): "HIGH",
    ("HIGH", "HIGH"): "CRITICAL",
}


@router.get("/projects/{project_id}/risks", response_model=ResponseModel)
def get_project_risks(
    project_id: int,
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    risk_level: Optional[str] = Query(None, description="风险等级"),
    status: Optional[str] = Query(None, description="状态"),
    risk_category: Optional[str] = Query(None, description="风险类别"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取项目风险列表

    Args:
        project_id: 项目ID
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        risk_level: 风险等级筛选
        status: 状态筛选
        risk_category: 风险类别筛选
        current_user: 当前用户

    Returns:
        ResponseModel: 风险列表
    """
    query = db.query(PmoProjectRisk).filter(PmoProjectRisk.project_id == project_id)

    if risk_level:
        query = query.filter(PmoProjectRisk.risk_level == risk_level)
    if status:
        query = query.filter(PmoProjectRisk.status == status)
    if risk_category:
        query = query.filter(PmoProjectRisk.risk_category == risk_category)

    total = query.count()
    risks = query.order_by(desc(PmoProjectRisk.created_at)).offset(pagination.offset).limit(pagination.limit).all()

    risks_data = [{
        "id": r.id,
        "risk_no": r.risk_no,
        "risk_category": r.risk_category,
        "risk_name": r.risk_name,
        "description": r.description,
        "probability": r.probability,
        "impact": r.impact,
        "risk_level": r.risk_level,
        "response_strategy": r.response_strategy,
        "owner_name": r.owner_name,
        "status": r.status,
        "is_triggered": r.is_triggered,
        "follow_up_date": r.follow_up_date.isoformat() if r.follow_up_date else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in risks]

    # 统计
    level_counts = {}
    for r in risks:
        level = r.risk_level or "UNKNOWN"
        level_counts[level] = level_counts.get(level, 0) + 1

    return ResponseModel(
        code=200,
        message="获取风险列表成功",
        data={
            "total": total,
            "level_counts": level_counts,
            "items": risks_data
        }
    )


@router.get("/projects/risks/{risk_id}", response_model=ResponseModel)
def get_risk_detail(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取风险详情

    Args:
        risk_id: 风险ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 风险详情
    """
    risk = db.query(PmoProjectRisk).filter(PmoProjectRisk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")

    return ResponseModel(
        code=200,
        message="获取风险详情成功",
        data={
            "id": risk.id,
            "project_id": risk.project_id,
            "risk_no": risk.risk_no,
            "risk_category": risk.risk_category,
            "risk_name": risk.risk_name,
            "description": risk.description,
            "probability": risk.probability,
            "impact": risk.impact,
            "risk_level": risk.risk_level,
            "response_strategy": risk.response_strategy,
            "response_plan": risk.response_plan,
            "owner_id": risk.owner_id,
            "owner_name": risk.owner_name,
            "status": risk.status,
            "follow_up_date": risk.follow_up_date.isoformat() if risk.follow_up_date else None,
            "last_update": risk.last_update,
            "trigger_condition": risk.trigger_condition,
            "is_triggered": risk.is_triggered,
            "triggered_date": risk.triggered_date.isoformat() if risk.triggered_date else None,
            "closed_date": risk.closed_date.isoformat() if risk.closed_date else None,
            "closed_reason": risk.closed_reason,
            "created_at": risk.created_at.isoformat() if risk.created_at else None,
        }
    )


@router.post("/projects/{project_id}/risks", response_model=ResponseModel)
def create_project_risk(
    project_id: int,
    risk_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建项目风险

    Args:
        project_id: 项目ID
        risk_data: 风险数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 生成风险编号
    count = db.query(PmoProjectRisk).filter(PmoProjectRisk.project_id == project_id).count()
    risk_no = f"RISK-{project.project_code}-{count + 1:03d}"

    # 计算风险等级
    probability = risk_data.get("probability", "MEDIUM")
    impact = risk_data.get("impact", "MEDIUM")
    risk_level = RISK_LEVEL_MATRIX.get((probability, impact), "MEDIUM")

    risk = PmoProjectRisk(
        project_id=project_id,
        risk_no=risk_no,
        risk_category=risk_data.get("risk_category"),
        risk_name=risk_data.get("risk_name"),
        description=risk_data.get("description"),
        probability=probability,
        impact=impact,
        risk_level=risk_level,
        response_strategy=risk_data.get("response_strategy"),
        response_plan=risk_data.get("response_plan"),
        owner_id=risk_data.get("owner_id"),
        owner_name=risk_data.get("owner_name"),
        trigger_condition=risk_data.get("trigger_condition"),
        follow_up_date=date.fromisoformat(risk_data["follow_up_date"]) if risk_data.get("follow_up_date") else None,
        status="IDENTIFIED",
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)

    return ResponseModel(
        code=200,
        message="风险创建成功",
        data={"id": risk.id, "risk_no": risk_no, "risk_level": risk_level}
    )


@router.put("/projects/risks/{risk_id}", response_model=ResponseModel)
def update_project_risk(
    risk_id: int,
    risk_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新风险

    Args:
        risk_id: 风险ID
        risk_data: 更新数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    risk = db.query(PmoProjectRisk).filter(PmoProjectRisk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")

    updatable = [
        "risk_category", "risk_name", "description", "response_strategy",
        "response_plan", "owner_id", "owner_name", "trigger_condition",
        "last_update", "status"
    ]
    for field in updatable:
        if field in risk_data:
            setattr(risk, field, risk_data[field])

    # 重新计算风险等级
    if "probability" in risk_data or "impact" in risk_data:
        probability = risk_data.get("probability", risk.probability)
        impact = risk_data.get("impact", risk.impact)
        risk.probability = probability
        risk.impact = impact
        risk.risk_level = RISK_LEVEL_MATRIX.get((probability, impact), "MEDIUM")

    if "follow_up_date" in risk_data:
        risk.follow_up_date = date.fromisoformat(risk_data["follow_up_date"]) if risk_data["follow_up_date"] else None

    db.commit()

    return ResponseModel(code=200, message="风险更新成功", data={"id": risk.id, "risk_level": risk.risk_level})


@router.post("/projects/risks/{risk_id}/trigger", response_model=ResponseModel)
def trigger_risk(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    触发风险

    Args:
        risk_id: 风险ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 触发结果
    """
    risk = db.query(PmoProjectRisk).filter(PmoProjectRisk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")

    if risk.is_triggered:
        raise HTTPException(status_code=400, detail="该风险已触发")

    risk.is_triggered = True
    risk.triggered_date = date.today()
    risk.status = "TRIGGERED"
    db.commit()

    return ResponseModel(code=200, message="风险已触发", data={"id": risk.id})


@router.post("/projects/risks/{risk_id}/close", response_model=ResponseModel)
def close_risk(
    risk_id: int,
    close_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    关闭风险

    Args:
        risk_id: 风险ID
        close_data: 关闭数据（closed_reason）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 关闭结果
    """
    risk = db.query(PmoProjectRisk).filter(PmoProjectRisk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")

    if risk.status == "CLOSED":
        raise HTTPException(status_code=400, detail="该风险已关闭")

    risk.status = "CLOSED"
    risk.closed_date = date.today()
    risk.closed_reason = close_data.get("closed_reason", "")
    db.commit()

    return ResponseModel(code=200, message="风险已关闭", data={"id": risk.id})


@router.delete("/projects/risks/{risk_id}", response_model=ResponseModel)
def delete_project_risk(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    删除风险

    Args:
        risk_id: 风险ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 删除结果
    """
    risk = db.query(PmoProjectRisk).filter(PmoProjectRisk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")

    if risk.status not in ["IDENTIFIED", "CLOSED"]:
        raise HTTPException(status_code=400, detail="只能删除已识别或已关闭的风险")

    db.delete(risk)
    db.commit()

    return ResponseModel(code=200, message="风险删除成功", data={"id": risk_id})
