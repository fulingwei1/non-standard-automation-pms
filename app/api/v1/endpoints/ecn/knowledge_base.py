# -*- coding: utf-8 -*-
"""
ECN分析 - 知识库集成

包含解决方案提取、相似ECN查找、解决方案推荐和模板管理
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.ecn import Ecn, EcnSolutionTemplate
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.ecn_knowledge_service import EcnKnowledgeService
from app.common.query_filters import apply_pagination

router = APIRouter()


@router.post("/ecns/{ecn_id}/extract-solution", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def extract_solution(
    ecn_id: int,
    auto_extract: bool = Body(True, description="是否自动提取"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从ECN中提取解决方案
    """
    try:
        service = EcnKnowledgeService(db)
        result = service.extract_solution(ecn_id=ecn_id, auto_extract=auto_extract)

        # 如果自动提取，更新ECN的解决方案字段
        if auto_extract and result.get('solution'):
            ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
            if ecn:
                ecn.solution = result['solution']
                ecn.solution_source = 'AUTO_EXTRACT'
                db.commit()

        return ResponseModel(
            code=200,
            message="解决方案提取成功",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取失败: {str(e)}")


@router.get("/ecns/{ecn_id}/similar-ecns", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_similar_ecns(
    ecn_id: int,
    top_n: int = Query(5, description="返回数量"),
    min_similarity: float = Query(0.3, description="最小相似度阈值"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    查找相似的ECN
    """
    try:
        service = EcnKnowledgeService(db)
        similar_ecns = service.find_similar_ecns(
            ecn_id=ecn_id,
            top_n=top_n,
            min_similarity=min_similarity
        )

        return ResponseModel(
            code=200,
            message="查找相似ECN成功",
            data={
                "ecn_id": ecn_id,
                "similar_ecns": similar_ecns,
                "count": len(similar_ecns)
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找失败: {str(e)}")


@router.get("/ecns/{ecn_id}/recommend-solutions", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def recommend_solutions(
    ecn_id: int,
    top_n: int = Query(5, description="返回数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    推荐解决方案模板
    """
    try:
        service = EcnKnowledgeService(db)
        recommendations = service.recommend_solutions(ecn_id=ecn_id, top_n=top_n)

        return ResponseModel(
            code=200,
            message="推荐解决方案成功",
            data={
                "ecn_id": ecn_id,
                "recommendations": recommendations,
                "count": len(recommendations)
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")


@router.post("/ecns/{ecn_id}/create-solution-template", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def create_solution_template(
    ecn_id: int,
    template_data: Dict[str, Any] = Body(..., description="模板数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从ECN创建解决方案模板
    """
    try:
        service = EcnKnowledgeService(db)
        template = service.create_solution_template(
            ecn_id=ecn_id,
            template_data=template_data,
            created_by=current_user.id
        )

        return ResponseModel(
            code=200,
            message="创建解决方案模板成功",
            data={
                "template_id": template.id,
                "template_code": template.template_code,
                "template_name": template.template_name
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.post("/ecns/{ecn_id}/apply-solution-template", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def apply_solution_template(
    ecn_id: int,
    template_id: int = Body(..., description="模板ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应用解决方案模板到ECN
    """
    try:
        service = EcnKnowledgeService(db)
        result = service.apply_solution_template(ecn_id=ecn_id, template_id=template_id)

        return ResponseModel(
            code=200,
            message="应用解决方案模板成功",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"应用失败: {str(e)}")


@router.get("/ecn-solution-templates", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def list_solution_templates(
    ecn_type: Optional[str] = Query(None, description="ECN类型筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_active: bool = Query(True, description="是否启用"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取解决方案模板列表
    """
    query = db.query(EcnSolutionTemplate).filter(
        EcnSolutionTemplate.is_active == is_active
    )

    if ecn_type:
        query = query.filter(EcnSolutionTemplate.ecn_type == ecn_type)

    if category:
        query = query.filter(EcnSolutionTemplate.template_category == category)

    total = query.count()
    templates = apply_pagination(query.order_by(desc(EcnSolutionTemplate.usage_count)), pagination.offset, pagination.limit).all()

    return ResponseModel(
        code=200,
        message="获取解决方案模板列表成功",
        data={
            "templates": [
                {
                    "id": t.id,
                    "template_code": t.template_code,
                    "template_name": t.template_name,
                    "template_category": t.template_category,
                    "ecn_type": t.ecn_type,
                    "success_rate": float(t.success_rate or 0),
                    "usage_count": t.usage_count or 0,
                    "estimated_cost": float(t.estimated_cost or 0),
                    "estimated_days": t.estimated_days or 0,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in templates
            ],
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size
        }
    )


@router.get("/ecn-solution-templates/{template_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_solution_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取解决方案模板详情
    """
    template = db.query(EcnSolutionTemplate).filter(
        EcnSolutionTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail=f"解决方案模板 {template_id} 不存在")

    return ResponseModel(
        code=200,
        message="获取解决方案模板详情成功",
        data={
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
            "template_category": template.template_category,
            "ecn_type": template.ecn_type,
            "root_cause_category": template.root_cause_category,
            "keywords": template.keywords or [],
            "solution_description": template.solution_description,
            "solution_steps": template.solution_steps or [],
            "required_resources": template.required_resources or [],
            "estimated_cost": float(template.estimated_cost or 0),
            "estimated_days": template.estimated_days or 0,
            "success_rate": float(template.success_rate or 0),
            "usage_count": template.usage_count or 0,
            "source_ecn_id": template.source_ecn_id,
            "created_at": template.created_at.isoformat() if template.created_at else None
        }
    )
