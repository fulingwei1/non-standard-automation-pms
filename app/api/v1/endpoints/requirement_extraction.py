# -*- coding: utf-8 -*-
"""
项目需求 AI 抽取与工程师推荐 API
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.requirement_extraction_service import RequirementExtractionService

router = APIRouter()


@router.get("/projects/{project_id}/requirements", summary="抽取项目工程师需求")
def extract_requirements(
    project_id: int = Path(..., description="项目 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从项目信息中 AI 抽取工程师需求
    
    包括：
    1. 生产能力需求
    2. 售后服务需求
    3. 设计需求
    4. 调试需求
    """
    service = RequirementExtractionService(db)
    requirements = service.extract_requirements_from_project(project_id)
    
    if 'error' in requirements:
        raise HTTPException(status_code=404, detail=requirements['error'])
    
    return requirements


@router.post("/requirements/{requirement_id}/recommend", summary="推荐工程师")
def recommend_engineers(
    requirement_id: int = Path(..., description="需求 ID"),
    limit: int = Query(5, ge=1, le=20, description="推荐人数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    根据需求推荐合适的工程师
    
    考虑因素：
    1. 技能匹配度
    2. 能力匹配度（多项目/标准化/AI）
    3. 当前可用性
    """
    # 查询需求
    from app.models.project_requirements import ProjectRequirement
    requirement = db.query(ProjectRequirement).filter(
        ProjectRequirement.id == requirement_id
    ).first()
    
    if not requirement:
        raise HTTPException(status_code=404, detail="需求不存在")
    
    # 构建需求字典
    req_dict = {
        'required_skills': requirement.required_skills.split(',') if requirement.required_skills else [],
        'production_complexity': requirement.production_complexity,
        'required_experience_years': requirement.required_experience_years,
        'min_multi_project_capacity': requirement.min_multi_project_capacity,
        'min_standardization_score': requirement.min_standardization_score,
        'min_ai_skill_level': requirement.min_ai_skill_level,
    }
    
    service = RequirementExtractionService(db)
    recommendations = service.recommend_engineers(req_dict, limit)
    
    # 保存推荐结果
    saved_recs = service.save_recommendations(requirement_id, recommendations)
    
    return {
        'requirement_id': requirement_id,
        'recommendation_count': len(recommendations),
        'recommendations': recommendations,
    }


@router.post("/projects/{project_id}/auto-recommend", summary="项目自动推荐工程师")
def auto_recommend_for_project(
    project_id: int = Path(..., description="项目 ID"),
    limit: int = Query(5, ge=1, le=20, description="每个需求推荐人数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目自动推荐工程师
    
    流程：
    1. 从项目抽取需求
    2. 为每个需求推荐工程师
    3. 返回完整推荐方案
    """
    service = RequirementExtractionService(db)
    
    # 1. 抽取需求
    requirements = service.extract_requirements_from_project(project_id)
    
    if 'error' in requirements:
        raise HTTPException(status_code=404, detail=requirements['error'])
    
    # 2. 为每个需求推荐工程师
    all_recommendations = {}
    
    for req_type, req_list in requirements.get('requirements', {}).items():
        type_recommendations = []
        
        for req in req_list:
            recs = service.recommend_engineers(req, limit)
            
            # 保存推荐
            from app.models.project_requirements import ProjectRequirement
            # 这里应该先创建需求记录，简化处理直接返回
            
            type_recommendations.extend(recs)
        
        all_recommendations[req_type] = type_recommendations[:limit]
    
    return {
        'project_id': project_id,
        'project_name': requirements.get('project_name'),
        'total_requirements': requirements.get('total_requirements'),
        'recommendations': all_recommendations,
    }
