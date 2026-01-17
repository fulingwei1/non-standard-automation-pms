# -*- coding: utf-8 -*-
"""
ECN分析相关 API endpoints

包含：BOM影响分析、呆滞料风险、责任分摊、RCA分析、知识库集成
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.ecn import (
    Ecn,
    EcnAffectedMaterial,
    EcnBomImpact,
    EcnResponsibility,
    EcnSolutionTemplate,
)
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.ecn_bom_analysis_service import EcnBomAnalysisService
from app.services.ecn_knowledge_service import EcnKnowledgeService

router = APIRouter()


# ==================== BOM影响分析 ====================

@router.post("/ecns/{ecn_id}/analyze-bom-impact", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def analyze_bom_impact(
    ecn_id: int,
    machine_id: Optional[int] = Query(None, description="设备ID（可选，如果ECN已关联设备则自动获取）"),
    include_cascade: bool = Query(True, description="是否包含级联影响分析"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    BOM影响分析
    分析ECN对BOM的级联影响，包括直接影响和级联影响
    """
    try:
        service = EcnBomAnalysisService(db)
        result = service.analyze_bom_impact(
            ecn_id=ecn_id,
            machine_id=machine_id,
            include_cascade=include_cascade
        )

        return ResponseModel(
            code=200,
            message="BOM影响分析完成",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/ecns/{ecn_id}/bom-impact-summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_bom_impact_summary(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取BOM影响汇总
    """
    bom_impacts = db.query(EcnBomImpact).filter(
        EcnBomImpact.ecn_id == ecn_id
    ).all()

    if not bom_impacts:
        return ResponseModel(
            code=200,
            message="暂无BOM影响分析结果",
            data={
                "ecn_id": ecn_id,
                "has_impact": False
            }
        )

    total_cost = sum(float(impact.total_cost_impact or 0) for impact in bom_impacts)
    total_items = sum(impact.affected_item_count or 0 for impact in bom_impacts)
    max_schedule = max((impact.schedule_impact_days or 0 for impact in bom_impacts), default=0)

    return ResponseModel(
        code=200,
        message="获取BOM影响汇总成功",
        data={
            "ecn_id": ecn_id,
            "has_impact": True,
            "total_cost_impact": total_cost,
            "total_affected_items": total_items,
            "max_schedule_impact_days": max_schedule,
            "bom_impacts": [
                {
                    "bom_id": impact.bom_version_id,
                    "machine_id": impact.machine_id,
                    "affected_item_count": impact.affected_item_count,
                    "cost_impact": float(impact.total_cost_impact or 0),
                    "schedule_impact_days": impact.schedule_impact_days,
                    "analysis_status": impact.analysis_status,
                    "analyzed_at": impact.analyzed_at.isoformat() if impact.analyzed_at else None
                }
                for impact in bom_impacts
            ]
        }
    )


@router.post("/ecns/{ecn_id}/check-obsolete-risk", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def check_obsolete_material_risk(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    检查呆滞料风险
    分析ECN变更可能导致呆滞的物料
    """
    try:
        service = EcnBomAnalysisService(db)
        result = service.check_obsolete_material_risk(ecn_id=ecn_id)

        return ResponseModel(
            code=200,
            message="呆滞料风险检查完成",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")


@router.get("/ecns/{ecn_id}/obsolete-material-alerts", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_obsolete_material_alerts(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取呆滞料预警列表
    """
    affected_materials = db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.ecn_id == ecn_id,
        EcnAffectedMaterial.is_obsolete_risk == True
    ).all()

    alerts = []
    for mat in affected_materials:
        alerts.append({
            "material_id": mat.material_id,
            "material_code": mat.material_code,
            "material_name": mat.material_name,
            "change_type": mat.change_type,
            "obsolete_quantity": float(mat.obsolete_quantity or 0),
            "obsolete_cost": float(mat.obsolete_cost or 0),
            "risk_level": mat.obsolete_risk_level,
            "analysis": mat.obsolete_analysis
        })

    return ResponseModel(
        code=200,
        message="获取呆滞料预警成功",
        data={
            "ecn_id": ecn_id,
            "alerts": alerts,
            "total_count": len(alerts),
            "total_cost": sum(float(mat.obsolete_cost or 0) for mat in affected_materials)
        }
    )


# ==================== 责任分摊 ====================

@router.post("/ecns/{ecn_id}/responsibility-analysis", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def create_responsibility_analysis(
    ecn_id: int,
    responsibilities: List[Dict[str, Any]] = Body(..., description="责任分摊列表"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建责任分摊分析
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail=f"ECN {ecn_id} 不存在")

    # 验证责任比例总和
    total_ratio = sum(float(r.get('responsibility_ratio', 0)) for r in responsibilities)
    if abs(total_ratio - 100) > 0.01:
        raise HTTPException(status_code=400, detail=f"责任比例总和必须为100%，当前为{total_ratio}%")

    # 删除旧的责任分摊
    db.query(EcnResponsibility).filter(EcnResponsibility.ecn_id == ecn_id).delete()

    # 创建新的责任分摊
    created_responsibilities = []
    total_cost = float(ecn.cost_impact or 0)

    for resp_data in responsibilities:
        ratio = float(resp_data.get('responsibility_ratio', 0))
        cost_allocation = total_cost * ratio / 100

        responsibility = EcnResponsibility(
            ecn_id=ecn_id,
            dept=resp_data.get('dept'),
            responsibility_ratio=ratio,
            responsibility_type=resp_data.get('responsibility_type', 'PRIMARY'),
            cost_allocation=cost_allocation,
            impact_description=resp_data.get('impact_description'),
            responsibility_scope=resp_data.get('responsibility_scope'),
            confirmed=False
        )
        db.add(responsibility)
        created_responsibilities.append(responsibility)

    db.commit()

    return ResponseModel(
        code=200,
        message="责任分摊分析创建成功",
        data={
            "ecn_id": ecn_id,
            "created_count": len(created_responsibilities),
            "responsibilities": [
                {
                    "id": r.id,
                    "dept": r.dept,
                    "responsibility_ratio": float(r.responsibility_ratio),
                    "cost_allocation": float(r.cost_allocation),
                    "responsibility_type": r.responsibility_type
                }
                for r in created_responsibilities
            ]
        }
    )


@router.get("/ecns/{ecn_id}/responsibility-summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_responsibility_summary(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取责任分摊汇总
    """
    responsibilities = db.query(EcnResponsibility).filter(
        EcnResponsibility.ecn_id == ecn_id
    ).all()

    if not responsibilities:
        return ResponseModel(
            code=200,
            message="暂无责任分摊信息",
            data={
                "ecn_id": ecn_id,
                "has_responsibility": False
            }
        )

    total_cost = sum(float(r.cost_allocation or 0) for r in responsibilities)

    return ResponseModel(
        code=200,
        message="获取责任分摊汇总成功",
        data={
            "ecn_id": ecn_id,
            "has_responsibility": True,
            "total_cost_allocation": total_cost,
            "responsibilities": [
                {
                    "id": r.id,
                    "dept": r.dept,
                    "responsibility_ratio": float(r.responsibility_ratio),
                    "responsibility_type": r.responsibility_type,
                    "cost_allocation": float(r.cost_allocation),
                    "impact_description": r.impact_description,
                    "confirmed": r.confirmed,
                    "confirmed_at": r.confirmed_at.isoformat() if r.confirmed_at else None
                }
                for r in responsibilities
            ]
        }
    )


# ==================== RCA分析 ====================

@router.put("/ecns/{ecn_id}/rca-analysis", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_rca_analysis(
    ecn_id: int,
    root_cause: Optional[str] = Body(None, description="根本原因类型"),
    root_cause_analysis: Optional[str] = Body(None, description="RCA分析内容"),
    root_cause_category: Optional[str] = Body(None, description="原因分类"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新RCA分析
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail=f"ECN {ecn_id} 不存在")

    if root_cause is not None:
        ecn.root_cause = root_cause
    if root_cause_analysis is not None:
        ecn.root_cause_analysis = root_cause_analysis
    if root_cause_category is not None:
        ecn.root_cause_category = root_cause_category

    db.commit()

    return ResponseModel(
        code=200,
        message="RCA分析更新成功",
        data={
            "ecn_id": ecn_id,
            "root_cause": ecn.root_cause,
            "root_cause_analysis": ecn.root_cause_analysis,
            "root_cause_category": ecn.root_cause_category
        }
    )


@router.get("/ecns/{ecn_id}/rca-analysis", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_rca_analysis(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取RCA分析
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail=f"ECN {ecn_id} 不存在")

    return ResponseModel(
        code=200,
        message="获取RCA分析成功",
        data={
            "ecn_id": ecn_id,
            "root_cause": ecn.root_cause,
            "root_cause_analysis": ecn.root_cause_analysis,
            "root_cause_category": ecn.root_cause_category
        }
    )


# ==================== 知识库集成 ====================

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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
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
    templates = query.order_by(desc(EcnSolutionTemplate.usage_count)).offset((page - 1) * page_size).limit(page_size).all()

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
            "page": page,
            "page_size": page_size
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
