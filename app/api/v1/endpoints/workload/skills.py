# -*- coding: utf-8 -*-
"""
技能管理端点

包含用户技能查询、工序列表、技能匹配
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/skills", response_model=ResponseModel)
def get_user_skills(
    *,
    db: Session = Depends(deps.get_db),
    user_id: Optional[int] = Query(None, description="用户ID（不指定则返回所有用户的技能）"),
    process_type: Optional[str] = Query(None, description="工序类型筛选"),
    include_expired: bool = Query(False, description="是否包含已过期的技能"),
    current_user: User = Depends(security.require_permission("workload:read")),
) -> Any:
    """
    获取用户技能列表

    支持按用户ID或工序类型筛选
    """
    from app.models.production import ProcessDict, Worker, WorkerSkill

    skills_data = []

    # 构建查询
    if user_id:
        # 先查找Worker记录
        worker = db.query(Worker).filter(
            Worker.user_id == user_id,
            Worker.is_active == True
        ).first()

        if worker:
            worker_skills = db.query(WorkerSkill).filter(
                WorkerSkill.worker_id == worker.id
            )
        else:
            # 如果没有Worker记录，从User的职位推断
            user = db.query(User).filter(User.id == user_id).first()
            return ResponseModel(
                code=200,
                message="查询成功（从用户职位推断）",
                data={
                    "user_id": user_id,
                    "user_name": user.real_name if user else None,
                    "skills": [{
                        "skill_id": None,
                        "process_id": None,
                        "process_code": None,
                        "process_name": user.position if user else None,
                        "process_type": "GENERAL",
                        "skill_level": "INTERMEDIATE",
                        "certified_date": None,
                        "expiry_date": None,
                        "is_valid": True,
                        "source": "user_position"
                    }] if user and user.position else []
                }
            )
    else:
        # 获取所有技能
        worker_skills = db.query(WorkerSkill)

    # 应用筛选条件
    if not include_expired:
        worker_skills = worker_skills.filter(
            (WorkerSkill.expiry_date >= date.today()) | (WorkerSkill.expiry_date.is_(None))
        )

    skills = worker_skills.all()

    for ws in skills:
        # 获取工序信息
        process = db.query(ProcessDict).filter(
            ProcessDict.id == ws.process_id
        ).first()

        if process_type and process.process_type != process_type:
            continue

        # 获取工人和用户信息
        worker = db.query(Worker).filter(Worker.id == ws.worker_id).first()
        user = None
        if worker:
            user = db.query(User).filter(User.id == worker.user_id).first()

        if process:
            is_valid = True
            if ws.expiry_date:
                is_valid = ws.expiry_date >= date.today()

            skills_data.append({
                "skill_id": ws.id,
                "worker_id": ws.worker_id,
                "user_id": user.id if user else None,
                "user_name": user.real_name if user else (worker.worker_name if worker else None),
                "process_id": process.id,
                "process_code": process.process_code,
                "process_name": process.process_name,
                "process_type": process.process_type,
                "skill_level": ws.skill_level,
                "certified_date": ws.certified_date.isoformat() if ws.certified_date else None,
                "expiry_date": ws.expiry_date.isoformat() if ws.expiry_date else None,
                "is_valid": is_valid,
                "remark": ws.remark
            })

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "total": len(skills_data),
            "skills": skills_data
        }
    )


@router.get("/skills/processes", response_model=ResponseModel)
def get_available_processes(
    *,
    db: Session = Depends(deps.get_db),
    process_type: Optional[str] = Query(None, description="工序类型筛选"),
    current_user: User = Depends(security.require_permission("workload:read")),
) -> Any:
    """
    获取可用的工序列表（技能字典）

    用于技能分配时选择工序
    """
    from app.models.production import ProcessDict

    query = db.query(ProcessDict).filter(ProcessDict.is_active == True)

    if process_type:
        query = query.filter(ProcessDict.process_type == process_type)

    processes = query.order_by(ProcessDict.process_code).all()

    process_list = []
    for p in processes:
        process_list.append({
            "id": p.id,
            "process_code": p.process_code,
            "process_name": p.process_name,
            "process_type": p.process_type,
            "standard_hours": float(p.standard_hours) if p.standard_hours else None,
            "description": p.description
        })

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "total": len(process_list),
            "processes": process_list
        }
    )


@router.get("/skills/matching", response_model=ResponseModel)
def match_users_by_skill(
    *,
    db: Session = Depends(deps.get_db),
    process_id: Optional[int] = Query(None, description="需要的工序ID"),
    skill_level: Optional[str] = Query(None, description="最低技能等级要求"),
    min_available_hours: Optional[float] = Query(0, description="最小可用工时"),
    current_user: User = Depends(security.require_permission("workload:read")),
) -> Any:
    """
    根据技能匹配合适的人员

    返回具有指定工序技能且有空闲时间的人员列表
    """
    if process_id is None:
        return ResponseModel(
            code=200,
            message="未指定工序，返回空匹配结果",
            data={
                "process_id": None,
                "process_name": None,
                "required_level": skill_level or "JUNIOR",
                "matched_count": 0,
                "workers": [],
            },
        )

    from app.models.production import ProcessDict, Worker, WorkerSkill

    # 获取工序信息
    process = db.query(ProcessDict).filter(ProcessDict.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="工序不存在")

    # 查找具有该工序技能的工人
    worker_skills = db.query(WorkerSkill).filter(
        WorkerSkill.process_id == process_id
    )

    # 技能等级筛选
    level_order = {"EXPERT": 4, "SENIOR": 3, "INTERMEDIATE": 2, "JUNIOR": 1}
    if skill_level:
        min_level = level_order.get(skill_level, 0)
        worker_skills = worker_skills.filter(
            WorkerSkill.skill_level.in_([
                lvl for lvl, order in level_order.items() if order >= min_level
            ])
        )

    # 检查技能有效性
    worker_skills = worker_skills.filter(
        (WorkerSkill.expiry_date >= date.today()) | (WorkerSkill.expiry_date.is_(None))
    )

    matched_workers = []
    for ws in worker_skills.all():
        worker = db.query(Worker).filter(
            Worker.id == ws.worker_id,
            Worker.is_active == True
        ).first()

        if not worker or not worker.user_id:
            continue

        user = db.query(User).filter(User.id == worker.user_id).first()
        if not user or not user.is_active:
            continue

        # 计算可用工时（简化版）
        assigned_hours = 0
        from app.models.progress import Task
        tasks = db.query(Task).filter(
            Task.owner_id == user.id,
            Task.status.in_(["TODO", "IN_PROGRESS"])
        ).all()
        for task in tasks:
            if task.estimate_hours:
                assigned_hours += float(task.estimate_hours)

        available_hours = max(0, 40 - assigned_hours)  # 假设每周40小时

        if available_hours >= min_available_hours:
            matched_workers.append({
                "user_id": user.id,
                "user_name": user.real_name or user.username,
                "worker_id": worker.id,
                "department": user.department,
                "position": user.position,
                "skill_level": ws.skill_level,
                "certified_date": ws.certified_date.isoformat() if ws.certified_date else None,
                "available_hours": round(available_hours, 2),
                "match_score": level_order.get(ws.skill_level, 0) * 10 + available_hours / 4
            })

    # 按匹配度排序
    matched_workers.sort(key=lambda x: x["match_score"], reverse=True)

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "process_id": process_id,
            "process_name": process.process_name,
            "required_level": skill_level or "JUNIOR",
            "matched_count": len(matched_workers),
            "workers": matched_workers
        }
    )


# ==================== 兼容性端点 ====================

@router.get("/workload/skills/processes", response_model=ResponseModel)
def get_available_processes_compat(
    *,
    db: Session = Depends(deps.get_db),
    process_type: Optional[str] = Query(None, description="工序类型筛选"),
    current_user: User = Depends(security.require_permission("workload:read")),
) -> Any:
    return get_available_processes(
        db=db, process_type=process_type, current_user=current_user
    )


@router.get("/workload/skills/matching", response_model=ResponseModel)
def match_users_by_skill_compat(
    *,
    db: Session = Depends(deps.get_db),
    process_id: Optional[int] = Query(None, description="需要的工序ID"),
    skill_level: Optional[str] = Query(None, description="最低技能等级要求"),
    min_available_hours: Optional[float] = Query(0, description="最小可用工时"),
    current_user: User = Depends(security.require_permission("workload:read")),
) -> Any:
    return match_users_by_skill(
        db=db,
        process_id=process_id,
        skill_level=skill_level,
        min_available_hours=min_available_hours,
        current_user=current_user,
    )
