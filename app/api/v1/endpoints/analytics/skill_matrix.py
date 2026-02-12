# -*- coding: utf-8 -*-
"""
技能矩阵分析 API

按技能查找可用人员、技能缺口分析
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.project import ProjectStageResourcePlan
from app.models.staff_matching import HrEmployeeTagEvaluation, HrTagDict
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/analytics/skill-matrix", response_model=ResponseModel)
def get_global_skill_matrix(
    db: Session = Depends(get_db),
    tag_type: Optional[str] = Query("SKILL", description="标签类型"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    全局技能矩阵
    """
    # 获取所有技能标签
    tags = db.query(HrTagDict).filter(
        HrTagDict.tag_type == tag_type,
        HrTagDict.is_active,
    ).order_by(HrTagDict.sort_order).all()

    skill_matrix = []
    for tag in tags:
        # 统计拥有该技能的员工数和平均分
        stats = db.query(
            func.count(HrEmployeeTagEvaluation.employee_id).label("count"),
            func.avg(HrEmployeeTagEvaluation.score).label("avg_score"),
        ).filter(
            HrEmployeeTagEvaluation.tag_id == tag.id,
        ).first()

        skill_matrix.append({
            "tag_id": tag.id,
            "tag_code": tag.tag_code,
            "tag_name": tag.tag_name,
            "employee_count": stats.count or 0,
            "avg_score": round(float(stats.avg_score or 0), 1),
            "is_required": tag.is_required,
        })

    # 按员工数排序
    skill_matrix.sort(key=lambda x: x["employee_count"], reverse=True)

    return ResponseModel(data={
        "tag_type": tag_type,
        "skills": skill_matrix,
        "total_skills": len(skill_matrix),
    })


@router.get("/analytics/skill-matrix/skills", response_model=ResponseModel)
def get_skill_list(
    db: Session = Depends(get_db),
    tag_type: Optional[str] = Query("SKILL"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    技能列表（带人数统计）
    """
    tags = db.query(HrTagDict).filter(
        HrTagDict.tag_type == tag_type,
        HrTagDict.is_active,
    ).all()

    result = []
    for tag in tags:
        count = db.query(func.count(HrEmployeeTagEvaluation.id)).filter(
            HrEmployeeTagEvaluation.tag_id == tag.id,
        ).scalar() or 0

        result.append({
            "tag_id": tag.id,
            "tag_code": tag.tag_code,
            "tag_name": tag.tag_name,
            "employee_count": count,
            "description": tag.description,
        })

    result.sort(key=lambda x: x["employee_count"], reverse=True)

    return ResponseModel(data=result)


@router.get("/analytics/skill-matrix/skills/{skill_code}", response_model=ResponseModel)
def get_skill_employees(
    skill_code: str,
    db: Session = Depends(get_db),
    min_score: Optional[int] = Query(None, ge=1, le=5, description="最低评分"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    特定技能的人员列表
    """
    tag = db.query(HrTagDict).filter(HrTagDict.tag_code == skill_code).first()
    if not tag:
        return ResponseModel(data={"skill": None, "employees": []})

    query = db.query(HrEmployeeTagEvaluation).filter(
        HrEmployeeTagEvaluation.tag_id == tag.id,
    )

    if min_score:
        query = query.filter(HrEmployeeTagEvaluation.score >= min_score)

    evaluations = query.order_by(HrEmployeeTagEvaluation.score.desc()).all()

    employees = []
    for eval in evaluations:
        emp = db.query(User).filter(User.id == eval.employee_id).first()
        if emp and emp.is_active:
            employees.append({
                "id": emp.id,
                "name": emp.username,
                "department": emp.department.name if emp.department else None,
                "score": eval.score,
                "evaluated_at": eval.updated_at,
            })

    return ResponseModel(data={
        "skill": {
            "tag_id": tag.id,
            "tag_code": tag.tag_code,
            "tag_name": tag.tag_name,
        },
        "employees": employees,
        "total_count": len(employees),
    })


@router.get("/analytics/skill-matrix/search", response_model=ResponseModel)
def search_available_employees(
    db: Session = Depends(get_db),
    skills: str = Query(..., description="需要的技能编码，逗号分隔"),
    min_score: int = Query(3, ge=1, le=5, description="最低技能评分"),
    department_id: Optional[int] = Query(None, description="限定部门"),
    available_from: Optional[date] = Query(None, description="可用开始日期"),
    available_to: Optional[date] = Query(None, description="可用结束日期"),
    min_availability: int = Query(30, ge=0, le=100, description="最低可用率%"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    按技能+可用性搜索人员
    """
    skill_codes = [s.strip() for s in skills.split(",")]

    # 获取技能标签
    tags = db.query(HrTagDict).filter(HrTagDict.tag_code.in_(skill_codes)).all()
    tag_ids = [t.id for t in tags]

    if not tag_ids:
        return ResponseModel(data={"candidates": [], "search_criteria": {"skills": skill_codes}})

    # 找到具备所有技能的员工
    # 使用子查询统计每个员工符合条件的技能数
    qualified_employees = db.query(
        HrEmployeeTagEvaluation.employee_id,
        func.count(HrEmployeeTagEvaluation.id).label("skill_count"),
        func.avg(HrEmployeeTagEvaluation.score).label("avg_score"),
    ).filter(
        HrEmployeeTagEvaluation.tag_id.in_(tag_ids),
        HrEmployeeTagEvaluation.score >= min_score,
    ).group_by(
        HrEmployeeTagEvaluation.employee_id
    ).having(
        func.count(HrEmployeeTagEvaluation.id) >= len(tag_ids)  # 具备所有技能
    ).all()

    employee_ids = [e.employee_id for e in qualified_employees]
    score_map = {e.employee_id: float(e.avg_score) for e in qualified_employees}

    if not employee_ids:
        return ResponseModel(data={"candidates": [], "search_criteria": {"skills": skill_codes}})

    # 进一步过滤
    employees_query = db.query(User).filter(
        User.id.in_(employee_ids),
        User.is_active,
    )

    if department_id:
        employees_query = employees_query.filter(User.department_id == department_id)

    employees = employees_query.all()

    # 计算可用性
    candidates = []
    for emp in employees:
        availability = 100.0  # 默认完全可用

        if available_from and available_to:
            # 计算该时间段的已分配比例
            allocated = db.query(func.sum(ProjectStageResourcePlan.allocation_pct)).filter(
                ProjectStageResourcePlan.assigned_employee_id == emp.id,
                ProjectStageResourcePlan.planned_start <= available_to,
                ProjectStageResourcePlan.planned_end >= available_from,
            ).scalar() or 0

            availability = max(0, 100.0 - float(allocated))

        if availability < min_availability:
            continue

        # 计算匹配度（技能分数 * 可用性权重）
        avg_score = score_map.get(emp.id, 0)
        match_score = (avg_score / 5.0 * 60) + (availability / 100.0 * 40)

        candidates.append({
            "id": emp.id,
            "name": emp.username,
            "department": emp.department.name if emp.department else None,
            "avg_skill_score": round(avg_score, 1),
            "availability_pct": round(availability, 1),
            "match_score": round(match_score, 1),
        })

    # 按匹配度排序
    candidates.sort(key=lambda x: x["match_score"], reverse=True)

    return ResponseModel(data={
        "candidates": candidates,
        "total_count": len(candidates),
        "search_criteria": {
            "skills": skill_codes,
            "min_score": min_score,
            "available_from": available_from,
            "available_to": available_to,
            "min_availability": min_availability,
        },
    })


@router.get("/analytics/skill-matrix/gaps", response_model=ResponseModel)
def get_skill_gaps(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    技能缺口分析
    """
    # 获取标记为必需的技能
    required_skills = db.query(HrTagDict).filter(
        HrTagDict.is_required,
        HrTagDict.is_active,
    ).all()

    critical_gaps = []
    training_opportunities = []

    for skill in required_skills:
        # 统计具备该技能的员工
        qualified = db.query(HrEmployeeTagEvaluation).filter(
            HrEmployeeTagEvaluation.tag_id == skill.id,
            HrEmployeeTagEvaluation.score >= 3,  # 至少3分才算合格
        ).count()

        # 假设每个必需技能至少需要3人
        min_required = 3
        gap = max(0, min_required - qualified)

        if gap > 0:
            critical_gaps.append({
                "skill": {
                    "code": skill.tag_code,
                    "name": skill.tag_name,
                },
                "severity": "CRITICAL" if qualified == 0 else ("HIGH" if gap >= 2 else "MEDIUM"),
                "current_headcount": qualified,
                "required_headcount": min_required,
                "gap": gap,
                "recommendation": "紧急招聘或外部顾问" if qualified == 0 else "建议安排培训或招聘",
            })

        # 查找可培训的人员（有该技能但分数较低）
        potential_trainees = db.query(HrEmployeeTagEvaluation).filter(
            HrEmployeeTagEvaluation.tag_id == skill.id,
            HrEmployeeTagEvaluation.score >= 1,
            HrEmployeeTagEvaluation.score < 3,
        ).all()

        if potential_trainees:
            trainees = []
            for eval in potential_trainees[:3]:  # 最多显示3个
                emp = db.query(User).filter(User.id == eval.employee_id).first()
                if emp:
                    trainees.append({
                        "id": emp.id,
                        "name": emp.username,
                        "current_score": eval.score,
                        "readiness": eval.score * 33,  # 简单的准备度计算
                    })

            if trainees:
                training_opportunities.append({
                    "skill": {
                        "code": skill.tag_code,
                        "name": skill.tag_name,
                    },
                    "potential_trainees": trainees,
                })

    return ResponseModel(data={
        "critical_gaps": critical_gaps,
        "training_opportunities": training_opportunities,
        "summary": {
            "total_gaps": len(critical_gaps),
            "critical_count": len([g for g in critical_gaps if g["severity"] == "CRITICAL"]),
            "training_candidates": sum(len(t["potential_trainees"]) for t in training_opportunities),
        },
    })


# ==================== Department Skill Matrix ====================

@router.get("/departments/{dept_id}/skill-matrix", response_model=ResponseModel)
def get_department_skill_matrix(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    部门技能矩阵
    """
    # 获取部门成员
    members = db.query(User).filter(
        User.department_id == dept_id,
        User.is_active,
    ).all()

    member_ids = [m.id for m in members]

    if not member_ids:
        return ResponseModel(data={
            "department_id": dept_id,
            "members": [],
            "skills": [],
        })

    # 获取所有技能标签
    skills = db.query(HrTagDict).filter(
        HrTagDict.tag_type == "SKILL",
        HrTagDict.is_active,
    ).all()

    # 获取该部门成员的技能评估
    evaluations = db.query(HrEmployeeTagEvaluation).filter(
        HrEmployeeTagEvaluation.employee_id.in_(member_ids),
    ).all()

    # 构建矩阵
    eval_map = {}
    for eval in evaluations:
        key = (eval.employee_id, eval.tag_id)
        eval_map[key] = eval.score

    matrix = []
    for member in members:
        member_skills = []
        for skill in skills:
            score = eval_map.get((member.id, skill.id), 0)
            if score > 0:
                member_skills.append({
                    "tag_code": skill.tag_code,
                    "tag_name": skill.tag_name,
                    "score": score,
                })

        matrix.append({
            "employee_id": member.id,
            "employee_name": member.username,
            "skills": member_skills,
            "skill_count": len(member_skills),
        })

    return ResponseModel(data={
        "department_id": dept_id,
        "members": matrix,
        "total_members": len(members),
        "available_skills": [{"code": s.tag_code, "name": s.tag_name} for s in skills],
    })
