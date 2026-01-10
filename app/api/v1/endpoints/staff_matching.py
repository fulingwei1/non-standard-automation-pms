# -*- coding: utf-8 -*-
"""
AI驱动人员智能匹配 API端点
"""

from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.api import deps
from app.models.staff_matching import (
    HrTagDict, HrEmployeeTagEvaluation, HrEmployeeProfile,
    HrProjectPerformance, MesProjectStaffingNeed, HrAIMatchingLog,
    TagTypeEnum, StaffingStatusEnum
)
from app.models.organization import Employee
from app.models.project import Project
from app.models.user import User
from app.schemas import staff_matching as schemas
from app.services.staff_matching_service import StaffMatchingService
from app.core import security

router = APIRouter()


# ==================== 标签管理 ====================

@router.get("/tags", response_model=List[schemas.TagDictResponse])
def list_tags(
    tag_type: Optional[str] = Query(None, description="标签类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取标签列表"""
    query = db.query(HrTagDict)

    if tag_type:
        query = query.filter(HrTagDict.tag_type == tag_type)
    if is_active is not None:
        query = query.filter(HrTagDict.is_active == is_active)
    if keyword:
        query = query.filter(
            or_(
                HrTagDict.tag_code.contains(keyword),
                HrTagDict.tag_name.contains(keyword)
            )
        )

    tags = query.order_by(HrTagDict.tag_type, HrTagDict.sort_order).offset(skip).limit(limit).all()
    return tags


@router.get("/tags/tree", response_model=List[schemas.TagDictTreeNode])
def get_tag_tree(
    tag_type: Optional[str] = Query(None, description="标签类型筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取标签层级树"""
    query = db.query(HrTagDict).filter(HrTagDict.is_active == True)

    if tag_type:
        query = query.filter(HrTagDict.tag_type == tag_type)

    all_tags = query.order_by(HrTagDict.sort_order).all()

    # 构建树结构
    tag_dict = {tag.id: {
        'id': tag.id,
        'tag_code': tag.tag_code,
        'tag_name': tag.tag_name,
        'tag_type': tag.tag_type,
        'weight': tag.weight,
        'is_required': tag.is_required,
        'sort_order': tag.sort_order,
        'children': []
    } for tag in all_tags}

    roots = []
    for tag in all_tags:
        if tag.parent_id and tag.parent_id in tag_dict:
            tag_dict[tag.parent_id]['children'].append(tag_dict[tag.id])
        else:
            roots.append(tag_dict[tag.id])

    return roots


@router.post("/tags", response_model=schemas.TagDictResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: schemas.TagDictCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:create"))
):
    """创建标签"""
    # 检查编码唯一性
    existing = db.query(HrTagDict).filter(HrTagDict.tag_code == tag_data.tag_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"标签编码已存在: {tag_data.tag_code}")

    tag = HrTagDict(**tag_data.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/tags/{tag_id}", response_model=schemas.TagDictResponse)
def update_tag(
    tag_id: int,
    tag_data: schemas.TagDictUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:update"))
):
    """更新标签"""
    tag = db.query(HrTagDict).filter(HrTagDict.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    for field, value in tag_data.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)

    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/tags/{tag_id}")
def delete_tag(
    tag_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """删除标签（软删除）"""
    tag = db.query(HrTagDict).filter(HrTagDict.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    tag.is_active = False
    db.commit()
    return {"message": "标签已删除"}


# ==================== 员工标签评估 ====================

@router.get("/evaluations", response_model=List[schemas.EmployeeTagEvaluationResponse])
def list_evaluations(
    employee_id: Optional[int] = Query(None, description="员工ID"),
    tag_id: Optional[int] = Query(None, description="标签ID"),
    tag_type: Optional[str] = Query(None, description="标签类型"),
    is_valid: Optional[bool] = Query(True, description="是否有效"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取员工标签评估列表"""
    query = db.query(HrEmployeeTagEvaluation).join(HrTagDict)

    if employee_id:
        query = query.filter(HrEmployeeTagEvaluation.employee_id == employee_id)
    if tag_id:
        query = query.filter(HrEmployeeTagEvaluation.tag_id == tag_id)
    if tag_type:
        query = query.filter(HrTagDict.tag_type == tag_type)
    if is_valid is not None:
        query = query.filter(HrEmployeeTagEvaluation.is_valid == is_valid)

    evaluations = query.order_by(HrEmployeeTagEvaluation.evaluate_date.desc()).offset(skip).limit(limit).all()

    # 附加关联信息
    result = []
    for eval in evaluations:
        eval_dict = {
            'id': eval.id,
            'employee_id': eval.employee_id,
            'tag_id': eval.tag_id,
            'score': eval.score,
            'evidence': eval.evidence,
            'evaluator_id': eval.evaluator_id,
            'evaluate_date': eval.evaluate_date,
            'is_valid': eval.is_valid,
            'created_at': eval.created_at,
            'tag_name': eval.tag.tag_name if eval.tag else None,
            'tag_type': eval.tag.tag_type if eval.tag else None,
            'evaluator_name': eval.evaluator.real_name if eval.evaluator else None
        }
        result.append(eval_dict)

    return result


@router.post("/evaluations", response_model=schemas.EmployeeTagEvaluationResponse, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    eval_data: schemas.EmployeeTagEvaluationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:create"))
):
    """创建员工标签评估"""
    # 验证员工和标签存在
    employee = db.query(Employee).filter(Employee.id == eval_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    tag = db.query(HrTagDict).filter(HrTagDict.id == eval_data.tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    evaluation = HrEmployeeTagEvaluation(
        **eval_data.model_dump(),
        evaluator_id=current_user.id
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return {
        'id': evaluation.id,
        'employee_id': evaluation.employee_id,
        'tag_id': evaluation.tag_id,
        'score': evaluation.score,
        'evidence': evaluation.evidence,
        'evaluator_id': evaluation.evaluator_id,
        'evaluate_date': evaluation.evaluate_date,
        'is_valid': evaluation.is_valid,
        'created_at': evaluation.created_at,
        'tag_name': tag.tag_name,
        'tag_type': tag.tag_type,
        'evaluator_name': current_user.real_name
    }


@router.post("/evaluations/batch", status_code=status.HTTP_201_CREATED)
def batch_create_evaluations(
    batch_data: schemas.EmployeeTagEvaluationBatch,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:create"))
):
    """批量创建员工标签评估"""
    # 验证员工存在
    employee = db.query(Employee).filter(Employee.id == batch_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    created_count = 0
    for eval_item in batch_data.evaluations:
        tag_id = eval_item.get('tag_id')
        score = eval_item.get('score')
        evidence = eval_item.get('evidence', '')

        if not tag_id or not score:
            continue

        # 检查标签存在
        tag = db.query(HrTagDict).filter(HrTagDict.id == tag_id).first()
        if not tag:
            continue

        evaluation = HrEmployeeTagEvaluation(
            employee_id=batch_data.employee_id,
            tag_id=tag_id,
            score=score,
            evidence=evidence,
            evaluator_id=current_user.id,
            evaluate_date=batch_data.evaluate_date
        )
        db.add(evaluation)
        created_count += 1

    db.commit()

    # 更新员工档案
    StaffMatchingService.aggregate_employee_profile(db, batch_data.employee_id)

    return {"message": f"成功创建 {created_count} 条评估记录"}


@router.put("/evaluations/{eval_id}", response_model=schemas.EmployeeTagEvaluationResponse)
def update_evaluation(
    eval_id: int,
    eval_data: schemas.EmployeeTagEvaluationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:update"))
):
    """更新员工标签评估"""
    evaluation = db.query(HrEmployeeTagEvaluation).filter(HrEmployeeTagEvaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="评估记录不存在")

    for field, value in eval_data.model_dump(exclude_unset=True).items():
        setattr(evaluation, field, value)

    db.commit()
    db.refresh(evaluation)

    return {
        'id': evaluation.id,
        'employee_id': evaluation.employee_id,
        'tag_id': evaluation.tag_id,
        'score': evaluation.score,
        'evidence': evaluation.evidence,
        'evaluator_id': evaluation.evaluator_id,
        'evaluate_date': evaluation.evaluate_date,
        'is_valid': evaluation.is_valid,
        'created_at': evaluation.created_at,
        'tag_name': evaluation.tag.tag_name if evaluation.tag else None,
        'tag_type': evaluation.tag.tag_type if evaluation.tag else None,
        'evaluator_name': evaluation.evaluator.real_name if evaluation.evaluator else None
    }


@router.delete("/evaluations/{eval_id}")
def delete_evaluation(
    eval_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """删除评估记录（软删除）"""
    evaluation = db.query(HrEmployeeTagEvaluation).filter(HrEmployeeTagEvaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="评估记录不存在")

    evaluation.is_valid = False
    db.commit()
    return {"message": "评估记录已删除"}


# ==================== 员工档案 ====================

@router.get("/profiles", response_model=List[schemas.EmployeeProfileSummary])
def list_profiles(
    department: Optional[str] = Query(None, description="部门筛选"),
    employment_status: Optional[str] = Query(None, description="在职状态: active(在职), resigned(离职), all(全部)"),
    employment_type: Optional[str] = Query(None, description="员工类型: regular(正式), probation(试用期), intern(实习期)"),
    min_workload: Optional[float] = Query(None, description="最小工作负载"),
    max_workload: Optional[float] = Query(None, description="最大工作负载"),
    has_skill: Optional[int] = Query(None, description="包含技能ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取员工档案列表"""
    query = db.query(Employee, HrEmployeeProfile).outerjoin(
        HrEmployeeProfile, Employee.id == HrEmployeeProfile.employee_id
    )

    # 默认只显示在职员工，除非明确请求全部或离职
    if employment_status == 'all':
        pass  # 不过滤
    elif employment_status == 'resigned':
        query = query.filter(Employee.employment_status == 'resigned')
    else:
        # 默认显示在职员工
        query = query.filter(Employee.employment_status == 'active')

    # 员工类型筛选
    if employment_type:
        query = query.filter(Employee.employment_type == employment_type)

    if department:
        query = query.filter(Employee.department.contains(department))
    if min_workload is not None:
        query = query.filter(
            or_(
                HrEmployeeProfile.id == None,
                HrEmployeeProfile.current_workload_pct >= min_workload
            )
        )
    if max_workload is not None:
        query = query.filter(
            or_(
                HrEmployeeProfile.id == None,
                HrEmployeeProfile.current_workload_pct <= max_workload
            )
        )

    results = query.offset(skip).limit(limit).all()

    profiles = []
    for employee, profile in results:
        # 获取前3个技能
        top_skills = []
        if profile and profile.skill_tags:
            skill_tags = profile.skill_tags if isinstance(profile.skill_tags, list) else []
            top_skills = [s.get('tag_name', '') for s in skill_tags[:3]]

        profiles.append({
            'id': profile.id if profile else 0,
            'employee_id': employee.id,
            'employee_name': employee.name,
            'employee_code': employee.employee_code,
            'department': employee.department,
            'employment_status': getattr(employee, 'employment_status', 'active') or 'active',
            'employment_type': getattr(employee, 'employment_type', 'regular') or 'regular',
            'top_skills': top_skills,
            'attitude_score': profile.attitude_score if profile else None,
            'quality_score': profile.quality_score if profile else None,
            'current_workload_pct': profile.current_workload_pct if profile else 0,
            'available_hours': profile.available_hours if profile else 0,
            'total_projects': profile.total_projects if profile else 0,
            'avg_performance_score': profile.avg_performance_score if profile else None
        })

    return profiles


@router.get("/profiles/{employee_id}", response_model=schemas.EmployeeProfileResponse)
def get_profile(
    employee_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取员工档案详情"""
    profile = db.query(HrEmployeeProfile).filter(
        HrEmployeeProfile.employee_id == employee_id
    ).first()

    if not profile:
        # 尝试创建档案
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="员工不存在")

        profile = StaffMatchingService.aggregate_employee_profile(db, employee_id)

    return profile


@router.post("/profiles/{employee_id}/refresh")
def refresh_profile(
    employee_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """刷新员工档案聚合数据"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    # 更新标签聚合
    profile = StaffMatchingService.aggregate_employee_profile(db, employee_id)

    # 更新工作负载
    StaffMatchingService.update_employee_workload(db, employee_id)

    return {"message": "档案已刷新", "profile_id": profile.id}


# ==================== 项目绩效 ====================

@router.get("/performance", response_model=List[schemas.ProjectPerformanceResponse])
def list_performance(
    employee_id: Optional[int] = Query(None, description="员工ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    contribution_level: Optional[str] = Query(None, description="贡献等级"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取项目绩效列表"""
    query = db.query(HrProjectPerformance)

    if employee_id:
        query = query.filter(HrProjectPerformance.employee_id == employee_id)
    if project_id:
        query = query.filter(HrProjectPerformance.project_id == project_id)
    if contribution_level:
        query = query.filter(HrProjectPerformance.contribution_level == contribution_level)

    performances = query.order_by(HrProjectPerformance.evaluation_date.desc()).offset(skip).limit(limit).all()

    result = []
    for perf in performances:
        result.append({
            'id': perf.id,
            'employee_id': perf.employee_id,
            'project_id': perf.project_id,
            'role_code': perf.role_code,
            'role_name': perf.role_name,
            'performance_score': perf.performance_score,
            'quality_score': perf.quality_score,
            'collaboration_score': perf.collaboration_score,
            'on_time_rate': perf.on_time_rate,
            'contribution_level': perf.contribution_level,
            'hours_spent': perf.hours_spent,
            'evaluation_date': perf.evaluation_date,
            'evaluator_id': perf.evaluator_id,
            'comments': perf.comments,
            'created_at': perf.created_at,
            'project_name': perf.project.name if perf.project else None,
            'employee_name': perf.employee.name if perf.employee else None
        })

    return result


@router.post("/performance", response_model=schemas.ProjectPerformanceResponse, status_code=status.HTTP_201_CREATED)
def create_performance(
    perf_data: schemas.ProjectPerformanceCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:create"))
):
    """创建项目绩效记录"""
    # 验证员工和项目存在
    employee = db.query(Employee).filter(Employee.id == perf_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    project = db.query(Project).filter(Project.id == perf_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查是否已存在
    existing = db.query(HrProjectPerformance).filter(
        HrProjectPerformance.employee_id == perf_data.employee_id,
        HrProjectPerformance.project_id == perf_data.project_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该员工在此项目的绩效记录已存在")

    performance = HrProjectPerformance(
        **perf_data.model_dump(),
        evaluator_id=current_user.id
    )
    db.add(performance)
    db.commit()
    db.refresh(performance)

    # 更新员工档案
    StaffMatchingService.aggregate_employee_profile(db, perf_data.employee_id)

    return {
        'id': performance.id,
        'employee_id': performance.employee_id,
        'project_id': performance.project_id,
        'role_code': performance.role_code,
        'role_name': performance.role_name,
        'performance_score': performance.performance_score,
        'quality_score': performance.quality_score,
        'collaboration_score': performance.collaboration_score,
        'on_time_rate': performance.on_time_rate,
        'contribution_level': performance.contribution_level,
        'hours_spent': performance.hours_spent,
        'evaluation_date': performance.evaluation_date,
        'evaluator_id': performance.evaluator_id,
        'comments': performance.comments,
        'created_at': performance.created_at,
        'project_name': project.name,
        'employee_name': employee.name
    }


@router.get("/performance/employee/{employee_id}", response_model=List[schemas.ProjectPerformanceResponse])
def get_employee_performance_history(
    employee_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取员工项目绩效历史"""
    performances = db.query(HrProjectPerformance).filter(
        HrProjectPerformance.employee_id == employee_id
    ).order_by(HrProjectPerformance.evaluation_date.desc()).all()

    result = []
    for perf in performances:
        result.append({
            'id': perf.id,
            'employee_id': perf.employee_id,
            'project_id': perf.project_id,
            'role_code': perf.role_code,
            'role_name': perf.role_name,
            'performance_score': perf.performance_score,
            'quality_score': perf.quality_score,
            'collaboration_score': perf.collaboration_score,
            'on_time_rate': perf.on_time_rate,
            'contribution_level': perf.contribution_level,
            'hours_spent': perf.hours_spent,
            'evaluation_date': perf.evaluation_date,
            'evaluator_id': perf.evaluator_id,
            'comments': perf.comments,
            'created_at': perf.created_at,
            'project_name': perf.project.name if perf.project else None,
            'employee_name': perf.employee.name if perf.employee else None
        })

    return result


# ==================== 人员需求 ====================

@router.get("/staffing-needs", response_model=List[schemas.StaffingNeedResponse])
def list_staffing_needs(
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取人员需求列表"""
    query = db.query(MesProjectStaffingNeed)

    if project_id:
        query = query.filter(MesProjectStaffingNeed.project_id == project_id)
    if status:
        query = query.filter(MesProjectStaffingNeed.status == status)
    if priority:
        query = query.filter(MesProjectStaffingNeed.priority == priority)

    needs = query.order_by(
        MesProjectStaffingNeed.priority,
        MesProjectStaffingNeed.created_at.desc()
    ).offset(skip).limit(limit).all()

    result = []
    for need in needs:
        result.append({
            'id': need.id,
            'project_id': need.project_id,
            'role_code': need.role_code,
            'role_name': need.role_name,
            'headcount': need.headcount,
            'required_skills': need.required_skills,
            'preferred_skills': need.preferred_skills,
            'required_domains': need.required_domains,
            'required_attitudes': need.required_attitudes,
            'min_level': need.min_level,
            'priority': need.priority,
            'start_date': need.start_date,
            'end_date': need.end_date,
            'allocation_pct': need.allocation_pct,
            'status': need.status,
            'requester_id': need.requester_id,
            'filled_count': need.filled_count,
            'remark': need.remark,
            'created_at': need.created_at,
            'project_name': need.project.name if need.project else None,
            'requester_name': need.requester.real_name if need.requester else None
        })

    return result


@router.get("/staffing-needs/{need_id}", response_model=schemas.StaffingNeedResponse)
def get_staffing_need(
    need_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取人员需求详情"""
    need = db.query(MesProjectStaffingNeed).filter(MesProjectStaffingNeed.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="人员需求不存在")

    return {
        'id': need.id,
        'project_id': need.project_id,
        'role_code': need.role_code,
        'role_name': need.role_name,
        'headcount': need.headcount,
        'required_skills': need.required_skills,
        'preferred_skills': need.preferred_skills,
        'required_domains': need.required_domains,
        'required_attitudes': need.required_attitudes,
        'min_level': need.min_level,
        'priority': need.priority,
        'start_date': need.start_date,
        'end_date': need.end_date,
        'allocation_pct': need.allocation_pct,
        'status': need.status,
        'requester_id': need.requester_id,
        'filled_count': need.filled_count,
        'remark': need.remark,
        'created_at': need.created_at,
        'project_name': need.project.name if need.project else None,
        'requester_name': need.requester.real_name if need.requester else None
    }


@router.post("/staffing-needs", response_model=schemas.StaffingNeedResponse, status_code=status.HTTP_201_CREATED)
def create_staffing_need(
    need_data: schemas.StaffingNeedCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:create"))
):
    """创建人员需求"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == need_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 转换技能要求为JSON
    required_skills_json = [req.model_dump() for req in need_data.required_skills]
    preferred_skills_json = [req.model_dump() for req in need_data.preferred_skills] if need_data.preferred_skills else None
    required_domains_json = [req.model_dump() for req in need_data.required_domains] if need_data.required_domains else None
    required_attitudes_json = [req.model_dump() for req in need_data.required_attitudes] if need_data.required_attitudes else None

    need = MesProjectStaffingNeed(
        project_id=need_data.project_id,
        role_code=need_data.role_code,
        role_name=need_data.role_name,
        headcount=need_data.headcount,
        required_skills=required_skills_json,
        preferred_skills=preferred_skills_json,
        required_domains=required_domains_json,
        required_attitudes=required_attitudes_json,
        min_level=need_data.min_level,
        priority=need_data.priority,
        start_date=need_data.start_date,
        end_date=need_data.end_date,
        allocation_pct=need_data.allocation_pct,
        requester_id=current_user.id,
        remark=need_data.remark
    )
    db.add(need)
    db.commit()
    db.refresh(need)

    return {
        'id': need.id,
        'project_id': need.project_id,
        'role_code': need.role_code,
        'role_name': need.role_name,
        'headcount': need.headcount,
        'required_skills': need.required_skills,
        'preferred_skills': need.preferred_skills,
        'required_domains': need.required_domains,
        'required_attitudes': need.required_attitudes,
        'min_level': need.min_level,
        'priority': need.priority,
        'start_date': need.start_date,
        'end_date': need.end_date,
        'allocation_pct': need.allocation_pct,
        'status': need.status,
        'requester_id': need.requester_id,
        'filled_count': need.filled_count,
        'remark': need.remark,
        'created_at': need.created_at,
        'project_name': project.name,
        'requester_name': current_user.real_name
    }


@router.put("/staffing-needs/{need_id}", response_model=schemas.StaffingNeedResponse)
def update_staffing_need(
    need_id: int,
    need_data: schemas.StaffingNeedUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:update"))
):
    """更新人员需求"""
    need = db.query(MesProjectStaffingNeed).filter(MesProjectStaffingNeed.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="人员需求不存在")

    update_data = need_data.model_dump(exclude_unset=True)

    # 转换技能要求
    if 'required_skills' in update_data and update_data['required_skills']:
        update_data['required_skills'] = [req.model_dump() if hasattr(req, 'model_dump') else req for req in update_data['required_skills']]
    if 'preferred_skills' in update_data and update_data['preferred_skills']:
        update_data['preferred_skills'] = [req.model_dump() if hasattr(req, 'model_dump') else req for req in update_data['preferred_skills']]
    if 'required_domains' in update_data and update_data['required_domains']:
        update_data['required_domains'] = [req.model_dump() if hasattr(req, 'model_dump') else req for req in update_data['required_domains']]
    if 'required_attitudes' in update_data and update_data['required_attitudes']:
        update_data['required_attitudes'] = [req.model_dump() if hasattr(req, 'model_dump') else req for req in update_data['required_attitudes']]

    for field, value in update_data.items():
        setattr(need, field, value)

    db.commit()
    db.refresh(need)

    return {
        'id': need.id,
        'project_id': need.project_id,
        'role_code': need.role_code,
        'role_name': need.role_name,
        'headcount': need.headcount,
        'required_skills': need.required_skills,
        'preferred_skills': need.preferred_skills,
        'required_domains': need.required_domains,
        'required_attitudes': need.required_attitudes,
        'min_level': need.min_level,
        'priority': need.priority,
        'start_date': need.start_date,
        'end_date': need.end_date,
        'allocation_pct': need.allocation_pct,
        'status': need.status,
        'requester_id': need.requester_id,
        'filled_count': need.filled_count,
        'remark': need.remark,
        'created_at': need.created_at,
        'project_name': need.project.name if need.project else None,
        'requester_name': need.requester.real_name if need.requester else None
    }


@router.delete("/staffing-needs/{need_id}")
def cancel_staffing_need(
    need_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """取消人员需求"""
    need = db.query(MesProjectStaffingNeed).filter(MesProjectStaffingNeed.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="人员需求不存在")

    need.status = 'CANCELLED'
    db.commit()
    return {"message": "人员需求已取消"}


# ==================== AI匹配 ====================

@router.post("/matching/execute/{staffing_need_id}")
def execute_matching(
    staffing_need_id: int,
    top_n: int = Query(10, ge=1, le=50, description="返回候选人数量"),
    include_overloaded: bool = Query(False, description="是否包含超负荷员工"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """执行AI匹配"""
    try:
        result = StaffMatchingService.match_candidates(
            db=db,
            staffing_need_id=staffing_need_id,
            top_n=top_n,
            include_overloaded=include_overloaded
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")


@router.get("/matching/results/{staffing_need_id}", response_model=List[schemas.MatchingLogResponse])
def get_matching_results(
    staffing_need_id: int,
    request_id: Optional[str] = Query(None, description="匹配请求ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取匹配结果"""
    query = db.query(HrAIMatchingLog).filter(
        HrAIMatchingLog.staffing_need_id == staffing_need_id
    )

    if request_id:
        query = query.filter(HrAIMatchingLog.request_id == request_id)
    else:
        # 获取最新一次匹配
        latest_request = db.query(HrAIMatchingLog.request_id).filter(
            HrAIMatchingLog.staffing_need_id == staffing_need_id
        ).order_by(HrAIMatchingLog.matching_time.desc()).first()

        if latest_request:
            query = query.filter(HrAIMatchingLog.request_id == latest_request[0])

    logs = query.order_by(HrAIMatchingLog.rank).all()

    result = []
    for log in logs:
        result.append({
            'id': log.id,
            'request_id': log.request_id,
            'project_id': log.project_id,
            'staffing_need_id': log.staffing_need_id,
            'candidate_employee_id': log.candidate_employee_id,
            'total_score': log.total_score,
            'dimension_scores': log.dimension_scores,
            'rank': log.rank,
            'recommendation_type': log.recommendation_type,
            'is_accepted': log.is_accepted,
            'accept_time': log.accept_time,
            'acceptor_id': log.acceptor_id,
            'reject_reason': log.reject_reason,
            'matching_time': log.matching_time,
            'project_name': log.project.name if log.project else None,
            'employee_name': log.candidate.name if log.candidate else None,
            'acceptor_name': log.acceptor.real_name if log.acceptor else None
        })

    return result


@router.post("/matching/accept")
def accept_candidate(
    accept_data: schemas.MatchingAcceptRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """采纳候选人"""
    success = StaffMatchingService.accept_candidate(
        db=db,
        matching_log_id=accept_data.matching_log_id,
        acceptor_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="匹配记录不存在")

    return {"message": "候选人已采纳"}


@router.post("/matching/reject")
def reject_candidate(
    reject_data: schemas.MatchingRejectRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """拒绝候选人"""
    success = StaffMatchingService.reject_candidate(
        db=db,
        matching_log_id=reject_data.matching_log_id,
        reject_reason=reject_data.reject_reason
    )

    if not success:
        raise HTTPException(status_code=404, detail="匹配记录不存在")

    return {"message": "已拒绝候选人"}


@router.get("/matching/history", response_model=List[schemas.MatchingLogResponse])
def get_matching_history(
    project_id: Optional[int] = Query(None, description="项目ID"),
    staffing_need_id: Optional[int] = Query(None, description="需求ID"),
    employee_id: Optional[int] = Query(None, description="员工ID"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取匹配历史"""
    logs = StaffMatchingService.get_matching_history(
        db=db,
        project_id=project_id,
        staffing_need_id=staffing_need_id,
        employee_id=employee_id,
        limit=limit
    )

    result = []
    for log in logs:
        result.append({
            'id': log.id,
            'request_id': log.request_id,
            'project_id': log.project_id,
            'staffing_need_id': log.staffing_need_id,
            'candidate_employee_id': log.candidate_employee_id,
            'total_score': log.total_score,
            'dimension_scores': log.dimension_scores,
            'rank': log.rank,
            'recommendation_type': log.recommendation_type,
            'is_accepted': log.is_accepted,
            'accept_time': log.accept_time,
            'acceptor_id': log.acceptor_id,
            'reject_reason': log.reject_reason,
            'matching_time': log.matching_time,
            'project_name': log.project.name if log.project else None,
            'employee_name': log.candidate.name if log.candidate else None,
            'acceptor_name': log.acceptor.real_name if log.acceptor else None
        })

    return result


# ==================== 仪表板 ====================

@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取人员匹配仪表板"""
    # 需求统计
    open_needs = db.query(func.count(MesProjectStaffingNeed.id)).filter(
        MesProjectStaffingNeed.status == 'OPEN'
    ).scalar() or 0

    matching_needs = db.query(func.count(MesProjectStaffingNeed.id)).filter(
        MesProjectStaffingNeed.status == 'MATCHING'
    ).scalar() or 0

    filled_needs = db.query(func.count(MesProjectStaffingNeed.id)).filter(
        MesProjectStaffingNeed.status == 'FILLED'
    ).scalar() or 0

    # 按优先级统计
    priority_counts = db.query(
        MesProjectStaffingNeed.priority,
        func.count(MesProjectStaffingNeed.id)
    ).filter(
        MesProjectStaffingNeed.status.in_(['OPEN', 'MATCHING'])
    ).group_by(MesProjectStaffingNeed.priority).all()

    needs_by_priority = {p: c for p, c in priority_counts}

    # 匹配统计
    total_requests = db.query(func.count(func.distinct(HrAIMatchingLog.request_id))).scalar() or 0
    total_matched = db.query(func.count(HrAIMatchingLog.id)).scalar() or 0
    accepted = db.query(func.count(HrAIMatchingLog.id)).filter(
        HrAIMatchingLog.is_accepted == True
    ).scalar() or 0
    rejected = db.query(func.count(HrAIMatchingLog.id)).filter(
        HrAIMatchingLog.is_accepted == False
    ).scalar() or 0
    pending = total_matched - accepted - rejected

    avg_score = db.query(func.avg(HrAIMatchingLog.total_score)).filter(
        HrAIMatchingLog.is_accepted == True
    ).scalar()

    success_rate = (accepted / total_matched * 100) if total_matched > 0 else 0

    # 最近匹配
    recent_logs = db.query(HrAIMatchingLog).order_by(
        HrAIMatchingLog.matching_time.desc()
    ).limit(10).all()

    recent_matches = []
    for log in recent_logs:
        recent_matches.append({
            'id': log.id,
            'request_id': log.request_id,
            'project_id': log.project_id,
            'staffing_need_id': log.staffing_need_id,
            'candidate_employee_id': log.candidate_employee_id,
            'total_score': log.total_score,
            'dimension_scores': log.dimension_scores,
            'rank': log.rank,
            'recommendation_type': log.recommendation_type,
            'is_accepted': log.is_accepted,
            'matching_time': log.matching_time,
            'project_name': log.project.name if log.project else None,
            'employee_name': log.candidate.name if log.candidate else None
        })

    return {
        'open_needs': open_needs,
        'matching_needs': matching_needs,
        'filled_needs': filled_needs,
        'total_headcount_needed': 0,  # TODO: 统计
        'total_headcount_filled': 0,  # TODO: 统计
        'needs_by_priority': needs_by_priority,
        'matching_stats': {
            'total_requests': total_requests,
            'total_candidates_matched': total_matched,
            'accepted_count': accepted,
            'rejected_count': rejected,
            'pending_count': pending,
            'avg_score': round(float(avg_score), 2) if avg_score else None,
            'success_rate': round(success_rate, 2)
        },
        'recent_matches': recent_matches
    }
