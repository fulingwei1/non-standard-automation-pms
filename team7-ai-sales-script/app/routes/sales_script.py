from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.sales_script import (
    SalesScriptRequest,
    SalesScriptResponse,
    ObjectionHandlingRequest,
    ObjectionHandlingResponse,
    SalesProgressRequest,
    SalesProgressResponse,
    ScriptFeedbackRequest,
    ScriptTemplateRequest,
)
from app.services.sales_script_service import SalesScriptService

router = APIRouter()


@router.post("/recommend-sales-script", response_model=SalesScriptResponse, status_code=status.HTTP_201_CREATED)
async def recommend_sales_script(
    request: SalesScriptRequest,
    db: Session = Depends(get_db)
):
    """
    推荐销售话术
    
    - **presale_ticket_id**: 售前工单ID
    - **scenario**: 场景类型（first_contact, needs_discovery, solution_presentation, price_negotiation, objection_handling, closing）
    - **customer_profile_id**: 客户画像ID（可选）
    - **context**: 当前上下文（可选）
    """
    try:
        service = SalesScriptService(db)
        script = await service.recommend_script(
            presale_ticket_id=request.presale_ticket_id,
            scenario=request.scenario,
            customer_profile_id=request.customer_profile_id,
            context=request.context
        )
        return SalesScriptResponse(**script.to_dict())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recommend sales script: {str(e)}"
        )


@router.post("/handle-objection", response_model=ObjectionHandlingResponse, status_code=status.HTTP_201_CREATED)
async def handle_objection(
    request: ObjectionHandlingRequest,
    db: Session = Depends(get_db)
):
    """
    异议处理建议
    
    - **presale_ticket_id**: 售前工单ID
    - **objection_type**: 异议类型
    - **customer_profile_id**: 客户画像ID（可选）
    - **context**: 详细异议内容（可选）
    """
    try:
        service = SalesScriptService(db)
        script = await service.handle_objection(
            presale_ticket_id=request.presale_ticket_id,
            objection_type=request.objection_type,
            customer_profile_id=request.customer_profile_id,
            context=request.context
        )
        return ObjectionHandlingResponse(**script.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle objection: {str(e)}"
        )


@router.post("/sales-progress-guidance", response_model=SalesProgressResponse)
async def sales_progress_guidance(
    request: SalesProgressRequest,
    db: Session = Depends(get_db)
):
    """
    销售进程指导
    
    - **presale_ticket_id**: 售前工单ID
    - **customer_profile_id**: 客户画像ID（可选）
    - **current_situation**: 当前销售情况描述
    """
    try:
        service = SalesScriptService(db)
        guidance = await service.guide_sales_progress(
            presale_ticket_id=request.presale_ticket_id,
            current_situation=request.current_situation,
            customer_profile_id=request.customer_profile_id
        )
        return SalesProgressResponse(**guidance)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to provide sales progress guidance: {str(e)}"
        )


@router.get("/sales-scripts/{scenario}")
async def get_sales_scripts(
    scenario: str,
    customer_type: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    获取场景话术模板
    
    - **scenario**: 场景类型
    - **customer_type**: 客户类型（可选）
    - **limit**: 返回数量限制
    """
    try:
        service = SalesScriptService(db)
        templates = service.get_scripts_by_scenario(
            scenario=scenario,
            customer_type=customer_type,
            limit=limit
        )
        return [template.to_dict() for template in templates]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sales scripts: {str(e)}"
        )


@router.get("/script-library")
async def get_script_library(
    scenario: Optional[str] = Query(None),
    customer_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取话术库
    
    - **scenario**: 场景类型（可选）
    - **customer_type**: 客户类型（可选）
    - **limit**: 返回数量限制
    """
    try:
        service = SalesScriptService(db)
        templates = service.get_script_library(
            scenario=scenario,
            customer_type=customer_type,
            limit=limit
        )
        return {
            "total": len(templates),
            "scripts": [template.to_dict() for template in templates]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get script library: {str(e)}"
        )


@router.post("/add-script-template", status_code=status.HTTP_201_CREATED)
async def add_script_template(
    request: ScriptTemplateRequest,
    db: Session = Depends(get_db)
):
    """
    添加话术模板
    
    - **scenario**: 场景类型
    - **customer_type**: 客户类型（可选）
    - **script_content**: 话术内容
    - **tags**: 标签（可选）
    - **success_rate**: 成功率（可选）
    """
    try:
        service = SalesScriptService(db)
        template = service.add_script_template(
            scenario=request.scenario,
            script_content=request.script_content,
            customer_type=request.customer_type,
            tags=request.tags,
            success_rate=request.success_rate
        )
        return template.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add script template: {str(e)}"
        )


@router.post("/script-feedback", status_code=status.HTTP_200_OK)
async def script_feedback(
    request: ScriptFeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    话术反馈（用于优化）
    
    - **script_id**: 话术记录ID
    - **is_effective**: 是否有效
    - **feedback_notes**: 反馈备注（可选）
    """
    try:
        service = SalesScriptService(db)
        success = service.record_feedback(
            script_id=request.script_id,
            is_effective=request.is_effective,
            feedback_notes=request.feedback_notes
        )
        return {"success": success, "message": "Feedback recorded successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}"
        )
