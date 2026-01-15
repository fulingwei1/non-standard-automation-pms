# -*- coding: utf-8 -*-
"""
项目扩展端点

包含项目复盘、经验教训、最佳实践、数据同步、ERP集成、
高级分析（资源优化、关联分析、风险矩阵、变更影响）等端点
"""

from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import (
    Project, Machine, ProjectStatusLog, ProjectPaymentPlan,
    ProjectMilestone, ProjectMember, FinancialProjectCost, ProjectStage
)
from app.models.pmo import PmoResourceAllocation, PmoProjectRisk, PmoChangeRequest
from app.models.project_review import ProjectReview, ProjectLesson, ProjectBestPractice
from app.schemas.project import (
    ResourceOptimizationResponse,
    ResourceConflictResponse,
    ProjectRelationResponse,
    RiskMatrixResponse,
    ChangeImpactRequest,
    ChangeImpactResponse,
    ProjectSummaryResponse,
    ProjectTimelineResponse,
    TimelineEvent,
    ProjectDashboardResponse,
    InProductionProjectSummary,
    FinancialProjectCostCreate,
    FinancialProjectCostResponse,
)
from app.schemas.project_review import (
    ProjectReviewCreate,
    ProjectReviewUpdate,
    ProjectReviewResponse,
    ProjectLessonCreate,
    ProjectLessonUpdate,
    ProjectLessonResponse,
    ProjectBestPracticeCreate,
    ProjectBestPracticeUpdate,
    ProjectBestPracticeResponse,
    BestPracticeRecommendationRequest,
)
from app.schemas.common import PaginatedResponse, ResponseModel

from .utils import generate_review_no, _sync_to_erp_system

router = APIRouter()


# 注: 概览和仪表盘端点已迁移至 overview.py


# ==================== 项目复盘模块 ====================

@router.get("/project-reviews", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_reviews(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目复盘报告列表
    """
    from app.services.data_scope_service import DataScopeService

    query = db.query(ProjectReview).join(Project, ProjectReview.project_id == Project.id)
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    if project_id:
        query = query.filter(ProjectReview.project_id == project_id)
    if start_date:
        query = query.filter(ProjectReview.review_date >= start_date)
    if end_date:
        query = query.filter(ProjectReview.review_date <= end_date)
    if status_filter:
        query = query.filter(ProjectReview.status == status_filter)

    total = query.count()
    offset = (page - 1) * page_size
    reviews = query.order_by(desc(ProjectReview.review_date)).offset(offset).limit(page_size).all()

    items = [ProjectReviewResponse.model_validate(r).model_dump() for r in reviews]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/project-reviews", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_data: ProjectReviewCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目复盘报告
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, review_data.project_id)

    if project.stage not in ["S9"] and project.status not in ["ST30"]:
        raise HTTPException(
            status_code=400,
            detail="项目未完成，无法创建复盘报告"
        )

    review_no = generate_review_no(db)

    # 获取参与人姓名
    participant_names = []
    if review_data.participants:
        users = db.query(User).filter(User.id.in_(review_data.participants)).all()
        participant_names = [u.real_name or u.username for u in users]

    reviewer = db.query(User).filter(User.id == review_data.reviewer_id).first()
    reviewer_name = reviewer.real_name or reviewer.username if reviewer else current_user.real_name or current_user.username

    review = ProjectReview(
        review_no=review_no,
        project_id=review_data.project_id,
        project_code=project.project_code,
        review_date=review_data.review_date,
        review_type=review_data.review_type,
        success_factors=review_data.success_factors,
        problems=review_data.problems,
        improvements=review_data.improvements,
        best_practices=review_data.best_practices,
        conclusion=review_data.conclusion,
        reviewer_id=review_data.reviewer_id,
        reviewer_name=reviewer_name,
        participants=review_data.participants,
        participant_names=", ".join(participant_names) if participant_names else None,
        status=review_data.status or "DRAFT"
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return ResponseModel(
        code=200,
        message="复盘报告创建成功",
        data=ProjectReviewResponse.model_validate(review).model_dump()
    )


@router.get("/project-reviews/{review_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_review_detail(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目复盘报告详情
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    lessons = db.query(ProjectLesson).filter(ProjectLesson.review_id == review_id).all()
    best_practices = db.query(ProjectBestPractice).filter(ProjectBestPractice.review_id == review_id).all()

    data = ProjectReviewResponse.model_validate(review).model_dump()
    data["lessons"] = [ProjectLessonResponse.model_validate(l).model_dump() for l in lessons]
    data["best_practices"] = [ProjectBestPracticeResponse.model_validate(bp).model_dump() for bp in best_practices]

    return ResponseModel(
        code=200,
        message="获取复盘报告详情成功",
        data=data
    )


@router.put("/project-reviews/{review_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    review_data: ProjectReviewUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目复盘报告
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    update_data = review_data.model_dump(exclude_unset=True)

    if "participants" in update_data and update_data["participants"]:
        users = db.query(User).filter(User.id.in_(update_data["participants"])).all()
        participant_names = [u.real_name or u.username for u in users]
        update_data["participant_names"] = ", ".join(participant_names)

    for key, value in update_data.items():
        setattr(review, key, value)

    db.commit()
    db.refresh(review)

    return ResponseModel(
        code=200,
        message="复盘报告更新成功",
        data=ProjectReviewResponse.model_validate(review).model_dump()
    )


@router.delete("/project-reviews/{review_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除项目复盘报告
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    if review.status == "PUBLISHED":
        raise HTTPException(status_code=400, detail="已发布的复盘报告不能删除")

    db.delete(review)
    db.commit()

    return ResponseModel(
        code=200,
        message="复盘报告删除成功"
    )


# 注: 数据同步和ERP集成端点已迁移至 sync.py

# ==================== 经验教训 ====================

@router.get("/{project_id}/lessons-learned", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_lessons_learned(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目经验教训
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    from app.models.pmo import PmoProjectClosure
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.project_id == project_id).first()

    lessons_from_closure = {
        "lessons_learned": closure.lessons_learned if closure else None,
        "improvement_suggestions": closure.improvement_suggestions if closure else None,
        "achievement": closure.achievement if closure else None,
    }

    from app.models.issue import Issue
    issues = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status.in_(["RESOLVED", "CLOSED"])
    ).order_by(desc(Issue.resolved_at)).all()

    lessons_by_category = {}
    for issue in issues:
        category = issue.category or "OTHER"
        if category not in lessons_by_category:
            lessons_by_category[category] = []

        lessons_by_category[category].append({
            "issue_no": issue.issue_no,
            "title": issue.title,
            "solution": issue.solution,
            "severity": issue.severity,
        })

    return ResponseModel(
        code=200,
        message="获取经验教训成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "lessons_from_closure": lessons_from_closure,
            "lessons_by_category": lessons_by_category,
        }
    )


# ==================== 最佳实践 ====================

@router.get("/best-practices", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def search_best_practices(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_reusable: Optional[bool] = Query(True, description="是否可复用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    搜索最佳实践库
    """
    query = db.query(ProjectBestPractice).join(
        ProjectReview, ProjectBestPractice.review_id == ProjectReview.id
    ).join(
        Project, ProjectReview.project_id == Project.id
    )

    if is_reusable:
        query = query.filter(ProjectBestPractice.is_reusable == True)

    if keyword:
        query = query.filter(
            or_(
                ProjectBestPractice.title.like(f"%{keyword}%"),
                ProjectBestPractice.description.like(f"%{keyword}%")
            )
        )

    if category:
        query = query.filter(ProjectBestPractice.category == category)

    total = query.count()
    offset = (page - 1) * page_size
    practices = query.order_by(desc(ProjectBestPractice.reuse_count)).offset(offset).limit(page_size).all()

    items = [ProjectBestPracticeResponse.model_validate(bp).model_dump() for bp in practices]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/best-practices/recommend", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def recommend_best_practices(
    *,
    db: Session = Depends(deps.get_db),
    request: BestPracticeRecommendationRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    推荐最佳实践
    """
    query = db.query(ProjectBestPractice).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.validation_status == "VALIDATED",
        ProjectBestPractice.status == "ACTIVE"
    )

    if request.category:
        query = query.filter(ProjectBestPractice.category == request.category)

    practices = query.all()

    recommendations = []
    for practice in practices:
        score = 0.0
        reasons = []

        if request.project_type and practice.applicable_project_types:
            if request.project_type in practice.applicable_project_types:
                score += 0.4
                reasons.append("项目类型匹配")

        if request.current_stage and practice.applicable_stages:
            if request.current_stage in practice.applicable_stages:
                score += 0.4
                reasons.append("阶段匹配")

        if practice.reuse_count:
            score += min(0.2, practice.reuse_count * 0.01)
            if practice.reuse_count > 5:
                reasons.append("高复用率")

        if score > 0:
            recommendations.append({
                "practice": ProjectBestPracticeResponse.model_validate(practice).model_dump(),
                "match_score": round(score, 2),
                "match_reasons": reasons
            })

    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    recommendations = recommendations[:request.limit]

    return ResponseModel(
        code=200,
        message="推荐最佳实践成功",
        data={"recommendations": recommendations}
    )


# ==================== 项目资源分配优化 ====================

@router.get("/{project_id}/resource-optimization", response_model=dict)
def get_resource_optimization(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    start_date: Optional[date] = Query(None, description="开始日期（默认：项目开始日期）"),
    end_date: Optional[date] = Query(None, description="结束日期（默认：项目结束日期）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目资源分配优化分析
    分析项目资源分配情况，提供优化建议
    """
    from app.models.progress import Task
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    if not start_date:
        start_date = project.planned_start_date or date.today()
    if not end_date:
        end_date = project.planned_end_date or (date.today() + timedelta(days=90))

    # 获取项目资源分配
    allocations = db.query(PmoResourceAllocation).filter(
        PmoResourceAllocation.project_id == project_id,
        PmoResourceAllocation.start_date <= end_date,
        PmoResourceAllocation.end_date >= start_date,
        PmoResourceAllocation.status != 'CANCELLED'
    ).all()

    # 获取项目任务
    tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.plan_start <= end_date,
        Task.plan_end >= start_date,
        Task.status != 'CANCELLED'
    ).all()

    # 分析资源负荷
    resource_load = {}
    for alloc in allocations:
        resource_id = alloc.resource_id
        if resource_id not in resource_load:
            resource_load[resource_id] = {
                'resource_id': resource_id,
                'resource_name': alloc.resource_name,
                'resource_dept': alloc.resource_dept,
                'total_allocation': 0,
                'allocations': [],
            }

        resource_load[resource_id]['total_allocation'] += alloc.allocation_percent
        resource_load[resource_id]['allocations'].append({
            'id': alloc.id,
            'start_date': alloc.start_date.isoformat() if alloc.start_date else None,
            'end_date': alloc.end_date.isoformat() if alloc.end_date else None,
            'allocation_percent': alloc.allocation_percent,
            'planned_hours': alloc.planned_hours,
            'status': alloc.status,
        })

    # 检查资源冲突
    conflicts = []
    recommendations = []

    for resource_id, data in resource_load.items():
        if data['total_allocation'] > 100:
            recommendations.append({
                'type': 'OVER_ALLOCATION',
                'resource_id': resource_id,
                'resource_name': data['resource_name'],
                'current_allocation': data['total_allocation'],
                'recommendation': f"资源 {data['resource_name']} 总分配率 {data['total_allocation']}%，建议调整分配比例或延期部分任务",
                'priority': 'HIGH' if data['total_allocation'] > 150 else 'MEDIUM'
            })

    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'analysis_period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        },
        'resource_summary': {
            'total_resources': len(resource_load),
            'over_allocated_resources': len([r for r in resource_load.values() if r['total_allocation'] > 100]),
            'total_conflicts': len(conflicts),
        },
        'resource_load': list(resource_load.values()),
        'conflicts': conflicts,
        'recommendations': recommendations,
    }


# ==================== 项目关联分析 ====================

@router.get("/{project_id}/relations", response_model=dict)
def get_project_relations(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    relation_type: Optional[str] = Query(None, description="关联类型筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目关联分析
    分析项目之间的关联关系（物料转移、共享资源、共享客户等）
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    relations = []

    # 查找同客户项目
    if project.customer_id:
        same_customer_projects = db.query(Project).filter(
            Project.customer_id == project.customer_id,
            Project.id != project_id,
            Project.is_active == True
        ).limit(10).all()

        for p in same_customer_projects:
            relations.append({
                'relation_type': 'SAME_CUSTOMER',
                'related_project_id': p.id,
                'related_project_code': p.project_code,
                'related_project_name': p.project_name,
                'description': f'同客户项目: {project.customer_name}'
            })

    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'relations': relations,
    }


@router.post("/{project_id}/auto-discover-relations", response_model=dict, status_code=status.HTTP_200_OK)
def auto_discover_project_relations(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    min_confidence: float = Query(0.3, ge=0.0, le=1.0, description="最小置信度阈值"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    自动发现项目关联关系
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    discovered_relations = []

    # 相同客户的项目
    if project.customer_id:
        same_customer = db.query(Project).filter(
            Project.customer_id == project.customer_id,
            Project.id != project_id,
            Project.is_active == True
        ).all()
        for p in same_customer:
            discovered_relations.append({
                'relation_type': 'SAME_CUSTOMER',
                'related_project_id': p.id,
                'related_project_code': p.project_code,
                'confidence': 0.8,
            })

    # 相同项目经理的项目
    if project.pm_id:
        same_pm = db.query(Project).filter(
            Project.pm_id == project.pm_id,
            Project.id != project_id,
            Project.is_active == True
        ).all()
        for p in same_pm:
            discovered_relations.append({
                'relation_type': 'SAME_PM',
                'related_project_id': p.id,
                'related_project_code': p.project_code,
                'confidence': 0.7,
            })

    # 过滤置信度
    final_relations = [r for r in discovered_relations if r['confidence'] >= min_confidence]

    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'min_confidence': min_confidence,
        'total_discovered': len(final_relations),
        'relations': final_relations,
    }


# ==================== 项目风险矩阵 ====================

@router.get("/{project_id}/risk-matrix", response_model=dict)
def get_project_risk_matrix(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    include_closed: bool = Query(False, description="是否包含已关闭风险"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目风险矩阵
    生成项目风险矩阵，按概率和影响程度分类
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    query = db.query(PmoProjectRisk).filter(PmoProjectRisk.project_id == project_id)

    if not include_closed:
        query = query.filter(PmoProjectRisk.status != 'CLOSED')

    risks = query.all()

    risk_matrix = {
        'LOW_LOW': [], 'LOW_MEDIUM': [], 'LOW_HIGH': [],
        'MEDIUM_LOW': [], 'MEDIUM_MEDIUM': [], 'MEDIUM_HIGH': [],
        'HIGH_LOW': [], 'HIGH_MEDIUM': [], 'HIGH_HIGH': [],
    }

    risk_by_level = {'LOW': [], 'MEDIUM': [], 'HIGH': [], 'CRITICAL': []}

    for risk in risks:
        risk_info = {
            'id': risk.id,
            'risk_no': risk.risk_no,
            'risk_name': risk.risk_name,
            'risk_category': risk.risk_category,
            'probability': risk.probability,
            'impact': risk.impact,
            'risk_level': risk.risk_level,
            'status': risk.status,
        }

        prob = risk.probability or 'LOW'
        impact = risk.impact or 'LOW'
        matrix_key = f"{prob}_{impact}"
        if matrix_key in risk_matrix:
            risk_matrix[matrix_key].append(risk_info)

        level = risk.risk_level or 'LOW'
        if level in risk_by_level:
            risk_by_level[level].append(risk_info)

    stats = {
        'total_risks': len(risks),
        'by_level': {level: len(items) for level, items in risk_by_level.items()},
        'critical_risks': len(risk_by_level.get('CRITICAL', [])),
    }

    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'stats': stats,
        'risk_matrix': risk_matrix,
        'risk_by_level': risk_by_level,
    }


# ==================== 项目变更影响分析 ====================

@router.get("/{project_id}/change-impact", response_model=dict)
def get_change_impact_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    change_id: Optional[int] = Query(None, description="变更ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目变更影响分析
    分析项目变更对其他项目、资源、成本等的影响
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    query = db.query(PmoChangeRequest).filter(PmoChangeRequest.project_id == project_id)

    if change_id:
        query = query.filter(PmoChangeRequest.id == change_id)

    changes = query.all()

    impact_analysis = []
    for change in changes:
        impact_analysis.append({
            'change_id': change.id,
            'change_no': change.change_no,
            'change_type': change.change_type,
            'status': change.status,
            'impact_scope': change.impact_scope,
            'cost_impact': float(change.cost_impact) if change.cost_impact else 0,
            'schedule_impact': change.schedule_impact,
        })

    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'total_changes': len(changes),
        'impact_analysis': impact_analysis,
    }


# ==================== 项目概览数据 ====================

@router.get("/{project_id}/summary", response_model=ResponseModel)
def get_project_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目概览数据
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.models.progress import Task
    from app.models.alert import Alert
    from app.models.issue import Issue
    from app.models.project import ProjectDocument, ProjectCost

    project = check_project_access_or_raise(db, current_user, project_id)

    machine_count = db.query(Machine).filter(Machine.project_id == project_id).count()
    milestone_count = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).count()
    completed_milestone_count = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "COMPLETED"
    ).count()

    task_count = db.query(Task).filter(Task.project_id == project_id).count()
    completed_task_count = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == "COMPLETED"
    ).count()

    member_count = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).count()

    alert_count = db.query(Alert).filter(
        Alert.project_id == project_id,
        Alert.status != "RESOLVED"
    ).count()

    issue_count = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status != "CLOSED"
    ).count()

    document_count = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).count()

    costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()
    total_cost = float(sum(cost.cost_amount or 0 for cost in costs))

    return ResponseModel(
        code=200,
        message="获取项目概览成功",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "customer_name": project.customer_name,
            "pm_name": project.pm_name,
            "stage": project.stage or "S1",
            "status": project.status or "ST01",
            "health": project.health,
            "progress_pct": float(project.progress_pct or 0),
            "contract_amount": float(project.contract_amount or 0),
            "machine_count": machine_count,
            "milestone_count": milestone_count,
            "completed_milestone_count": completed_milestone_count,
            "task_count": task_count,
            "completed_task_count": completed_task_count,
            "member_count": member_count,
            "alert_count": alert_count,
            "issue_count": issue_count,
            "document_count": document_count,
            "total_cost": total_cost,
        }
    )


@router.get("/in-production/summary", response_model=ResponseModel)
def get_in_production_projects_summary(
    db: Session = Depends(deps.get_db),
    stage: Optional[str] = Query(None, description="阶段筛选：S4-S8"),
    health: Optional[str] = Query(None, description="健康度筛选：H1-H3"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    在产项目进度汇总（专门给生产总监/经理看）
    """
    query = db.query(Project).filter(
        Project.stage.in_(["S4", "S5", "S6", "S7", "S8"]),
        Project.is_active == True
    )

    from app.services.data_scope_service import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    if stage:
        query = query.filter(Project.stage == stage)
    if health:
        query = query.filter(Project.health == health)

    projects = query.all()

    result = []
    for project in projects:
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project.id,
            ProjectMilestone.status != "COMPLETED"
        ).order_by(ProjectMilestone.planned_date).limit(5).all()

        today = date.today()
        overdue_milestones = [
            m for m in milestones
            if m.planned_date and m.planned_date < today and m.status != "COMPLETED"
        ]

        next_milestone = milestones[0].milestone_name if milestones else None
        next_milestone_date = milestones[0].planned_date if milestones else None

        result.append({
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "stage": project.stage or "S4",
            "health": project.health,
            "progress": float(project.progress_pct or 0),
            "planned_end_date": project.planned_end_date.isoformat() if project.planned_end_date else None,
            "overdue_milestones_count": len(overdue_milestones),
            "next_milestone": next_milestone,
            "next_milestone_date": next_milestone_date.isoformat() if next_milestone_date else None,
        })

    return ResponseModel(
        code=200,
        message="获取在产项目汇总成功",
        data={"total": len(result), "projects": result}
    )


@router.get("/{project_id}/project-dashboard", response_model=ResponseModel)
def get_single_project_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取单个项目仪表盘数据
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.models.progress import Task
    from app.models.issue import Issue

    project = check_project_access_or_raise(db, current_user, project_id)

    today = date.today()

    # 任务统计
    total_tasks = db.query(Task).filter(Task.project_id == project_id).count()
    completed_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == "COMPLETED"
    ).count()

    # 里程碑统计
    total_milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id
    ).count()
    completed_milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "COMPLETED"
    ).count()

    # 风险统计
    risk_count = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.project_id == project_id,
        PmoProjectRisk.status != "CLOSED"
    ).count()

    # 问题统计
    issue_count = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status.notin_(["RESOLVED", "CLOSED"])
    ).count()

    return ResponseModel(
        code=200,
        message="获取项目仪表盘成功",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "stage": project.stage,
            "health": project.health,
            "progress_pct": float(project.progress_pct or 0),
            "task_stats": {
                "total": total_tasks,
                "completed": completed_tasks,
                "completion_rate": round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
            },
            "milestone_stats": {
                "total": total_milestones,
                "completed": completed_milestones,
            },
            "risk_count": risk_count,
            "issue_count": issue_count,
        }
    )


# ==================== 复盘报告状态管理 ====================

@router.put("/project-reviews/{review_id}/publish", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def publish_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发布项目复盘报告
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    review.status = "PUBLISHED"
    db.commit()
    db.refresh(review)

    return ResponseModel(
        code=200,
        message="复盘报告发布成功",
        data=ProjectReviewResponse.model_validate(review).model_dump()
    )


@router.put("/project-reviews/{review_id}/archive", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def archive_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    归档项目复盘报告
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    review.status = "ARCHIVED"
    db.commit()
    db.refresh(review)

    return ResponseModel(
        code=200,
        message="复盘报告归档成功",
        data=ProjectReviewResponse.model_validate(review).model_dump()
    )


# ==================== 经验教训管理 ====================

@router.get("/project-reviews/{review_id}/lessons", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_lessons(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    lesson_type: Optional[str] = Query(None, description="类型筛选：SUCCESS/FAILURE"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取复盘报告的经验教训列表
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    query = db.query(ProjectLesson).filter(ProjectLesson.review_id == review_id)

    if lesson_type:
        query = query.filter(ProjectLesson.lesson_type == lesson_type)
    if status_filter:
        query = query.filter(ProjectLesson.status == status_filter)

    total = query.count()
    offset = (page - 1) * page_size
    lessons = query.order_by(desc(ProjectLesson.created_at)).offset(offset).limit(page_size).all()

    items = [ProjectLessonResponse.model_validate(l).model_dump() for l in lessons]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/project-reviews/{review_id}/lessons", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_lesson(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    lesson_data: ProjectLessonCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建经验教训
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    if lesson_data.review_id != review_id:
        raise HTTPException(status_code=400, detail="review_id不匹配")

    lesson = ProjectLesson(**lesson_data.model_dump())
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return ResponseModel(
        code=200,
        message="经验教训创建成功",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.get("/project-reviews/lessons/{lesson_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_lesson_detail(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取经验教训详情
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)

    return ResponseModel(
        code=200,
        message="获取经验教训详情成功",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.put("/project-reviews/lessons/{lesson_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_lesson(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    lesson_data: ProjectLessonUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新经验教训
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)

    update_data = lesson_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lesson, key, value)

    db.commit()
    db.refresh(lesson)

    return ResponseModel(
        code=200,
        message="经验教训更新成功",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.delete("/project-reviews/lessons/{lesson_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_project_lesson(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除经验教训
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)

    db.delete(lesson)
    db.commit()

    return ResponseModel(
        code=200,
        message="经验教训删除成功"
    )


@router.put("/project-reviews/lessons/{lesson_id}/resolve", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def resolve_project_lesson(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记经验教训已解决
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)

    lesson.status = "RESOLVED"
    lesson.resolved_date = date.today()
    db.commit()
    db.refresh(lesson)

    return ResponseModel(
        code=200,
        message="经验教训已标记为已解决",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.put("/project-reviews/lessons/{lesson_id}/status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_lesson_status(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    new_status: str = Body(..., description="新状态：OPEN/IN_PROGRESS/RESOLVED/CLOSED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新经验教训状态
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)

    if new_status not in ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]:
        raise HTTPException(status_code=400, detail="无效的状态值")

    lesson.status = new_status
    if new_status in ["RESOLVED", "CLOSED"]:
        lesson.resolved_date = date.today()

    db.commit()
    db.refresh(lesson)

    return ResponseModel(
        code=200,
        message="经验教训状态更新成功",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.post("/project-reviews/lessons/batch-update", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_update_lessons(
    *,
    db: Session = Depends(deps.get_db),
    lesson_ids: List[int] = Body(..., description="经验教训ID列表"),
    update_data: Dict[str, Any] = Body(..., description="更新数据"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新经验教训
    """
    lessons = db.query(ProjectLesson).filter(ProjectLesson.id.in_(lesson_ids)).all()

    if not lessons:
        raise HTTPException(status_code=404, detail="未找到经验教训")

    from app.utils.permission_helpers import check_project_access_or_raise
    for lesson in lessons:
        check_project_access_or_raise(db, current_user, lesson.project_id)

    updated_count = 0
    for lesson in lessons:
        for key, value in update_data.items():
            if hasattr(lesson, key):
                setattr(lesson, key, value)
        updated_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"成功更新{updated_count}条经验教训",
        data={"updated_count": updated_count}
    )


# ==================== 最佳实践管理 ====================

@router.get("/project-reviews/{review_id}/best-practices", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_best_practices(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_reusable: Optional[bool] = Query(None, description="是否可复用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取复盘报告的最佳实践列表
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    query = db.query(ProjectBestPractice).filter(ProjectBestPractice.review_id == review_id)

    if category:
        query = query.filter(ProjectBestPractice.category == category)
    if is_reusable is not None:
        query = query.filter(ProjectBestPractice.is_reusable == is_reusable)

    total = query.count()
    offset = (page - 1) * page_size
    practices = query.order_by(desc(ProjectBestPractice.created_at)).offset(offset).limit(page_size).all()

    items = [ProjectBestPracticeResponse.model_validate(bp).model_dump() for bp in practices]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/project-reviews/{review_id}/best-practices", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    practice_data: ProjectBestPracticeCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建最佳实践
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    if practice_data.review_id != review_id:
        raise HTTPException(status_code=400, detail="review_id不匹配")

    practice = ProjectBestPractice(**practice_data.model_dump())
    db.add(practice)
    db.commit()
    db.refresh(practice)

    return ResponseModel(
        code=200,
        message="最佳实践创建成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.get("/project-reviews/best-practices/{practice_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_best_practice_detail(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最佳实践详情
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()

    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, practice.project_id)

    return ResponseModel(
        code=200,
        message="获取最佳实践详情成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.put("/project-reviews/best-practices/{practice_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    practice_data: ProjectBestPracticeUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新最佳实践
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()

    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, practice.project_id)

    update_data = practice_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(practice, key, value)

    db.commit()
    db.refresh(practice)

    return ResponseModel(
        code=200,
        message="最佳实践更新成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.delete("/project-reviews/best-practices/{practice_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除最佳实践
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()

    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, practice.project_id)

    db.delete(practice)
    db.commit()

    return ResponseModel(
        code=200,
        message="最佳实践删除成功"
    )


@router.put("/project-reviews/best-practices/{practice_id}/validate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def validate_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    validation_status: str = Body(..., description="验证状态：VALIDATED/REJECTED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    验证最佳实践
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()

    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, practice.project_id)

    if validation_status not in ["VALIDATED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="验证状态必须是VALIDATED或REJECTED")

    practice.validation_status = validation_status
    practice.validation_date = date.today()
    practice.validated_by = current_user.id
    db.commit()
    db.refresh(practice)

    return ResponseModel(
        code=200,
        message="最佳实践验证成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.post("/project-reviews/best-practices/{practice_id}/reuse", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def reuse_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    复用最佳实践（增加复用计数）
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()

    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")

    if not practice.is_reusable:
        raise HTTPException(status_code=400, detail="该最佳实践不可复用")

    practice.reuse_count = (practice.reuse_count or 0) + 1
    practice.last_reused_at = datetime.now()
    db.commit()
    db.refresh(practice)

    return ResponseModel(
        code=200,
        message="最佳实践复用成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.post("/project-reviews/best-practices/{practice_id}/apply", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def apply_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    target_project_id: int = Body(..., description="目标项目ID"),
    notes: Optional[str] = Body(None, description="应用备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应用最佳实践到项目（增加复用计数）
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()

    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")

    if not practice.is_reusable:
        raise HTTPException(status_code=400, detail="该最佳实践不可复用")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, target_project_id)

    practice.reuse_count = (practice.reuse_count or 0) + 1
    practice.last_reused_at = datetime.now()

    db.commit()
    db.refresh(practice)

    return ResponseModel(
        code=200,
        message="最佳实践应用成功",
        data={
            "practice": ProjectBestPracticeResponse.model_validate(practice).model_dump(),
            "applied_to_project_id": target_project_id,
            "notes": notes
        }
    )


# ==================== 最佳实践库高级功能 ====================

@router.get("/best-practices/categories", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_best_practice_categories(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最佳实践分类列表
    """
    categories = db.query(ProjectBestPractice.category).filter(
        ProjectBestPractice.category.isnot(None),
        ProjectBestPractice.is_reusable == True
    ).distinct().all()

    category_list = [cat[0] for cat in categories if cat[0]]

    return ResponseModel(
        code=200,
        message="获取分类列表成功",
        data={"categories": category_list}
    )


@router.get("/best-practices/statistics", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_best_practice_statistics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最佳实践统计信息
    """
    total = db.query(ProjectBestPractice).filter(ProjectBestPractice.is_reusable == True).count()
    validated = db.query(ProjectBestPractice).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.validation_status == "VALIDATED"
    ).count()
    pending = db.query(ProjectBestPractice).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.validation_status == "PENDING"
    ).count()

    total_reuse = db.query(func.sum(ProjectBestPractice.reuse_count)).filter(
        ProjectBestPractice.is_reusable == True
    ).scalar() or 0

    return ResponseModel(
        code=200,
        message="获取统计信息成功",
        data={
            "total": total,
            "validated": validated,
            "pending": pending,
            "total_reuse": total_reuse,
        }
    )


@router.get("/best-practices/popular", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_popular_best_practices(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取热门最佳实践（按复用次数排序）
    """
    query = db.query(ProjectBestPractice).join(
        ProjectReview, ProjectBestPractice.review_id == ProjectReview.id
    ).join(
        Project, ProjectReview.project_id == Project.id
    ).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.validation_status == "VALIDATED",
        ProjectBestPractice.status == "ACTIVE"
    )

    if category:
        query = query.filter(ProjectBestPractice.category == category)

    total = query.count()
    offset = (page - 1) * page_size
    practices = query.order_by(
        desc(ProjectBestPractice.reuse_count),
        desc(ProjectBestPractice.created_at)
    ).offset(offset).limit(page_size).all()

    items = [ProjectBestPracticeResponse.model_validate(bp).model_dump() for bp in practices]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


# ==================== 经验教训库高级功能 ====================

@router.get("/lessons-learned", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def search_lessons_learned(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    lesson_type: Optional[str] = Query(None, description="类型筛选：SUCCESS/FAILURE"),
    category: Optional[str] = Query(None, description="分类筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    跨项目搜索经验教训库
    """
    query = db.query(ProjectLesson).join(
        ProjectReview, ProjectLesson.review_id == ProjectReview.id
    ).join(
        Project, ProjectReview.project_id == Project.id
    )

    if keyword:
        query = query.filter(
            or_(
                ProjectLesson.title.like(f"%{keyword}%"),
                ProjectLesson.description.like(f"%{keyword}%")
            )
        )

    if lesson_type:
        query = query.filter(ProjectLesson.lesson_type == lesson_type)

    if category:
        query = query.filter(ProjectLesson.category == category)

    if status_filter:
        query = query.filter(ProjectLesson.status == status_filter)

    if project_id:
        query = query.filter(ProjectLesson.project_id == project_id)

    total = query.count()
    offset = (page - 1) * page_size
    lessons = query.order_by(desc(ProjectLesson.created_at)).offset(offset).limit(page_size).all()

    items = [ProjectLessonResponse.model_validate(lesson).model_dump() for lesson in lessons]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/lessons-learned/statistics", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_lessons_statistics(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取经验教训统计信息
    """
    query = db.query(ProjectLesson)

    if project_id:
        query = query.filter(ProjectLesson.project_id == project_id)

    total = query.count()
    success_count = query.filter(ProjectLesson.lesson_type == "SUCCESS").count()
    failure_count = query.filter(ProjectLesson.lesson_type == "FAILURE").count()

    resolved_count = query.filter(ProjectLesson.status.in_(["RESOLVED", "CLOSED"])).count()
    unresolved_count = total - resolved_count

    today = date.today()
    overdue_count = query.filter(
        ProjectLesson.due_date.isnot(None),
        ProjectLesson.due_date < today,
        ProjectLesson.status.notin_(["RESOLVED", "CLOSED"])
    ).count()

    return ResponseModel(
        code=200,
        message="获取统计信息成功",
        data={
            "total": total,
            "success_count": success_count,
            "failure_count": failure_count,
            "resolved_count": resolved_count,
            "unresolved_count": unresolved_count,
            "overdue_count": overdue_count
        }
    )


@router.get("/lessons-learned/categories", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_lesson_categories(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取经验教训分类列表
    """
    categories = db.query(ProjectLesson.category).filter(
        ProjectLesson.category.isnot(None)
    ).distinct().all()

    category_list = [cat[0] for cat in categories if cat[0]]

    return ResponseModel(
        code=200,
        message="获取分类列表成功",
        data={"categories": category_list}
    )


@router.get("/projects/{project_id}/best-practices/recommend", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_best_practice_recommendations(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目推荐的最佳实践（基于项目信息自动匹配）
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    request = BestPracticeRecommendationRequest(
        project_id=project_id,
        project_type=project.project_type if hasattr(project, 'project_type') else None,
        current_stage=project.stage if hasattr(project, 'stage') else None,
        limit=limit
    )

    return recommend_best_practices(db=db, request=request, current_user=current_user)


# ==================== 项目成本管理 ====================

@router.get("/projects/{project_id}/cost-summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_cost_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目成本汇总
    获取项目的成本汇总统计信息
    """
    from app.models.project import ProjectCost
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    # 总成本统计
    total_result = db.query(
        func.sum(ProjectCost.amount).label('total_amount'),
        func.sum(ProjectCost.tax_amount).label('total_tax'),
        func.count(ProjectCost.id).label('total_count')
    ).filter(ProjectCost.project_id == project_id).first()

    total_amount = float(total_result.total_amount) if total_result.total_amount else 0
    total_tax = float(total_result.total_tax) if total_result.total_tax else 0
    total_count = total_result.total_count or 0

    # 按成本类型统计
    type_stats = db.query(
        ProjectCost.cost_type,
        func.sum(ProjectCost.amount).label('amount'),
        func.count(ProjectCost.id).label('count')
    ).filter(
        ProjectCost.project_id == project_id
    ).group_by(ProjectCost.cost_type).all()

    type_summary = [
        {
            "cost_type": stat.cost_type,
            "amount": round(float(stat.amount) if stat.amount else 0, 2),
            "count": stat.count or 0,
            "percentage": round((float(stat.amount) / total_amount * 100) if total_amount > 0 else 0, 2)
        }
        for stat in type_stats
    ]

    # 按成本分类统计
    category_stats = db.query(
        ProjectCost.cost_category,
        func.sum(ProjectCost.amount).label('amount'),
        func.count(ProjectCost.id).label('count')
    ).filter(
        ProjectCost.project_id == project_id
    ).group_by(ProjectCost.cost_category).all()

    category_summary = [
        {
            "cost_category": stat.cost_category,
            "amount": round(float(stat.amount) if stat.amount else 0, 2),
            "count": stat.count or 0,
            "percentage": round((float(stat.amount) / total_amount * 100) if total_amount > 0 else 0, 2)
        }
        for stat in category_stats
    ]

    # 预算对比
    budget_amount = float(project.budget_amount or 0)
    actual_cost = float(project.actual_cost or 0)
    cost_variance = actual_cost - budget_amount
    cost_variance_pct = (cost_variance / budget_amount * 100) if budget_amount > 0 else 0

    # 合同对比
    contract_amount = float(project.contract_amount or 0)
    profit = contract_amount - actual_cost
    profit_margin = (profit / contract_amount * 100) if contract_amount > 0 else 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "budget_info": {
                "budget_amount": round(budget_amount, 2),
                "actual_cost": round(actual_cost, 2),
                "cost_variance": round(cost_variance, 2),
                "cost_variance_pct": round(cost_variance_pct, 2),
                "is_over_budget": cost_variance > 0
            },
            "contract_info": {
                "contract_amount": round(contract_amount, 2),
                "profit": round(profit, 2),
                "profit_margin": round(profit_margin, 2)
            },
            "cost_summary": {
                "total_amount": round(total_amount, 2),
                "total_tax": round(total_tax, 2),
                "total_with_tax": round(total_amount + total_tax, 2),
                "total_count": total_count
            },
            "by_type": type_summary,
            "by_category": category_summary,
        }
    )


@router.get("/projects/{project_id}/cost-details", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_cost_details(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    cost_type: Optional[str] = Query(None, description="成本类型筛选"),
    cost_category: Optional[str] = Query(None, description="成本分类筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    成本明细列表
    获取项目的成本明细记录列表，支持分页和筛选
    """
    from app.models.project import ProjectCost
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectCost).filter(ProjectCost.project_id == project_id)

    if machine_id:
        query = query.filter(ProjectCost.machine_id == machine_id)
    if cost_type:
        query = query.filter(ProjectCost.cost_type == cost_type)
    if cost_category:
        query = query.filter(ProjectCost.cost_category == cost_category)
    if start_date:
        query = query.filter(ProjectCost.cost_date >= start_date)
    if end_date:
        query = query.filter(ProjectCost.cost_date <= end_date)

    total = query.count()
    offset = (page - 1) * page_size
    costs = query.order_by(desc(ProjectCost.cost_date), desc(ProjectCost.created_at)).offset(offset).limit(page_size).all()

    cost_details = []
    for cost in costs:
        machine = None
        if cost.machine_id:
            machine = db.query(Machine).filter(Machine.id == cost.machine_id).first()

        cost_details.append({
            "id": cost.id,
            "cost_no": cost.cost_no,
            "cost_date": cost.cost_date.isoformat() if cost.cost_date else None,
            "cost_type": cost.cost_type,
            "cost_category": cost.cost_category,
            "amount": float(cost.amount) if cost.amount else 0,
            "tax_amount": float(cost.tax_amount) if cost.tax_amount else 0,
            "total_amount": float(cost.amount or 0) + float(cost.tax_amount or 0),
            "machine_id": cost.machine_id,
            "machine_code": machine.machine_code if machine else None,
            "machine_name": machine.machine_name if machine else None,
            "description": cost.description,
            "remark": cost.remark,
        })

    return PaginatedResponse(
        items=cost_details,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )
