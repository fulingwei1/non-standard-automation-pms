"""
售前AI方案生成 - API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.dependencies import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.presale_ai_solution import (
    TemplateMatchRequest,
    TemplateMatchResponse,
    SolutionGenerationRequest,
    SolutionGenerationResponse,
    ArchitectureGenerationRequest,
    ArchitectureGenerationResponse,
    BOMGenerationRequest,
    BOMGenerationResponse,
    SolutionResponse,
    SolutionUpdateRequest,
    SolutionReviewRequest,
    PDFExportRequest,
    SolutionTemplateCreate,
    SolutionTemplateUpdate,
    SolutionTemplateResponse
)
from app.services.presale_ai_service import PresaleAIService
from app.services.presale_ai_template_service import PresaleAITemplateService
from app.services.presale_ai_export_service import PresaleAIExportService


router = APIRouter(prefix="/api/v1/presale/ai", tags=["Presale AI Solution"])


# ==================== 模板匹配 ====================

@router.post("/match-templates", response_model=TemplateMatchResponse)
async def match_templates(
    request: TemplateMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    智能模板匹配
    - 基于需求自动匹配历史方案模板
    - 相似度评分（语义搜索）
    - 推荐TOP K最佳模板
    """
    service = PresaleAIService(db)
    
    matched_templates, search_time_ms = service.match_templates(
        request=request,
        user_id=current_user.id
    )
    
    return TemplateMatchResponse(
        matched_templates=matched_templates,
        total_templates=len(matched_templates),
        search_time_ms=search_time_ms
    )


# ==================== 方案生成 ====================

@router.post("/generate-solution", response_model=SolutionGenerationResponse)
async def generate_solution(
    request: SolutionGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI智能方案生成
    - 自动生成技术方案
    - 可选生成系统架构图
    - 可选生成BOM清单
    """
    service = PresaleAIService(db)
    
    try:
        result = service.generate_solution(
            request=request,
            user_id=current_user.id
        )
        
        # 获取完整方案对象
        solution = service.get_solution(result["solution_id"])
        
        return SolutionGenerationResponse(
            solution=SolutionResponse.model_validate(solution),
            generation_time_seconds=result["generation_time_seconds"],
            ai_model_used=result["ai_model_used"],
            tokens_used=result["tokens_used"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"方案生成失败: {str(e)}"
        )


# ==================== 架构图生成 ====================

@router.post("/generate-architecture", response_model=ArchitectureGenerationResponse)
async def generate_architecture(
    request: ArchitectureGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成系统架构图
    - 自动生成Mermaid/PlantUML架构图代码
    - 支持设备拓扑图、信号流程图
    """
    service = PresaleAIService(db)
    
    try:
        result = service.generate_architecture(
            requirements=request.requirements,
            diagram_type=request.diagram_type,
            solution_id=request.solution_id
        )
        
        return ArchitectureGenerationResponse(
            diagram_code=result["diagram_code"],
            diagram_type=result["diagram_type"],
            format=result["format"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"架构图生成失败: {str(e)}"
        )


# ==================== BOM清单生成 ====================

@router.post("/generate-bom", response_model=BOMGenerationResponse)
async def generate_bom(
    request: BOMGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成BOM清单
    - 自动匹配设备型号
    - 数量智能计算
    - 成本预估
    - 供应商推荐
    """
    service = PresaleAIService(db)
    
    try:
        result = service.generate_bom(
            equipment_list=request.equipment_list,
            include_cost=request.include_cost,
            include_suppliers=request.include_suppliers,
            solution_id=request.solution_id
        )
        
        return BOMGenerationResponse(
            bom_items=result["bom_items"],
            total_cost=result["total_cost"],
            item_count=result["item_count"],
            generation_time_seconds=result["generation_time_seconds"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BOM生成失败: {str(e)}"
        )


# ==================== 方案查询和更新 ====================

@router.get("/solution/{solution_id}", response_model=SolutionResponse)
async def get_solution(
    solution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取方案详情
    """
    service = PresaleAIService(db)
    solution = service.get_solution(solution_id)
    
    if not solution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="方案不存在"
        )
    
    return SolutionResponse.model_validate(solution)


@router.put("/solution/{solution_id}", response_model=SolutionResponse)
async def update_solution(
    solution_id: int,
    request: SolutionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新方案
    """
    service = PresaleAIService(db)
    
    try:
        updated_solution = service.update_solution(
            solution_id=solution_id,
            update_data=request.model_dump(exclude_unset=True)
        )
        
        return SolutionResponse.model_validate(updated_solution)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.post("/solution/{solution_id}/review", response_model=SolutionResponse)
async def review_solution(
    solution_id: int,
    request: SolutionReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    审核方案
    """
    service = PresaleAIService(db)
    
    try:
        reviewed_solution = service.review_solution(
            solution_id=solution_id,
            reviewer_id=current_user.id,
            status=request.status,
            comments=request.review_comments
        )
        
        return SolutionResponse.model_validate(reviewed_solution)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== PDF导出 ====================

@router.post("/export-solution-pdf")
async def export_solution_pdf(
    request: PDFExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出方案为PDF
    """
    export_service = PresaleAIExportService(db)
    
    try:
        pdf_path = export_service.export_to_pdf(
            solution_id=request.solution_id,
            include_diagrams=request.include_diagrams,
            include_bom=request.include_bom,
            template_style=request.template_style
        )
        
        return {
            "success": True,
            "pdf_path": pdf_path,
            "message": "PDF导出成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF导出失败: {str(e)}"
        )


# ==================== 模板库管理 ====================

@router.get("/template-library", response_model=List[SolutionTemplateResponse])
async def get_template_library(
    industry: Optional[str] = None,
    equipment_type: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取模板库
    """
    service = PresaleAIService(db)
    templates = service.get_template_library(
        industry=industry,
        equipment_type=equipment_type,
        is_active=is_active
    )
    
    return [SolutionTemplateResponse.model_validate(t) for t in templates]


@router.post("/template", response_model=SolutionTemplateResponse)
async def create_template(
    request: SolutionTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建方案模板
    """
    template_service = PresaleAITemplateService(db)
    
    try:
        template = template_service.create_template(
            data=request.model_dump(),
            user_id=current_user.id
        )
        
        return SolutionTemplateResponse.model_validate(template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模板创建失败: {str(e)}"
        )


@router.put("/template/{template_id}", response_model=SolutionTemplateResponse)
async def update_template(
    template_id: int,
    request: SolutionTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新方案模板
    """
    template_service = PresaleAITemplateService(db)
    
    try:
        template = template_service.update_template(
            template_id=template_id,
            data=request.model_dump(exclude_unset=True)
        )
        
        return SolutionTemplateResponse.model_validate(template)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模板更新失败: {str(e)}"
        )
