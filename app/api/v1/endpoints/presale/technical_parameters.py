# -*- coding: utf-8 -*-
"""
技术参数模板 API

提供技术参数模板的CRUD、匹配和成本估算接口
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.presale_technical_parameter import (
    BatchCostEstimateRequest,
    CostEstimateRequest,
    CostEstimateResponse,
    IndustryStatistics,
    TechnicalParameterTemplateCreate,
    TechnicalParameterTemplateListItem,
    TechnicalParameterTemplateResponse,
    TechnicalParameterTemplateUpdate,
    TestTypeStatistics,
)
from app.services.presale import TechnicalParameterService

router = APIRouter()


# ==================== 模板 CRUD ====================


@router.get(
    "/templates",
    response_model=PaginatedResponse[TechnicalParameterTemplateListItem],
    summary="获取技术参数模板列表",
    description="支持行业、测试类型、关键词筛选，分页返回模板列表",
)
def list_templates(
    industry: Optional[str] = Query(None, description="行业筛选"),
    test_type: Optional[str] = Query(None, description="测试类型筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    is_active: Optional[bool] = Query(True, description="是否只查询启用的模板"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取技术参数模板列表"""
    service = TechnicalParameterService(db)
    templates, total = service.list_templates(
        industry=industry,
        test_type=test_type,
        keyword=keyword,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

    items = [
        TechnicalParameterTemplateListItem(
            id=t.id,
            name=t.name,
            code=t.code,
            industry=t.industry,
            test_type=t.test_type,
            description=t.description,
            use_count=t.use_count or 0,
            is_active=t.is_active,
            created_at=t.created_at,
        )
        for t in templates
    ]

    pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post(
    "/templates",
    response_model=TechnicalParameterTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建技术参数模板",
)
def create_template(
    data: TechnicalParameterTemplateCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """创建新的技术参数模板"""
    service = TechnicalParameterService(db)

    # 检查编码是否已存在
    existing = service.get_template_by_code(data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"模板编码已存在: {data.code}",
        )

    template = service.create_template(
        name=data.name,
        code=data.code,
        industry=data.industry,
        test_type=data.test_type,
        created_by=current_user.id,
        description=data.description,
        parameters=data.parameters,
        cost_factors=data.cost_factors,
        typical_labor_hours=data.typical_labor_hours,
        reference_docs=data.reference_docs,
        sample_images=data.sample_images,
    )

    return TechnicalParameterTemplateResponse(
        id=template.id,
        name=template.name,
        code=template.code,
        industry=template.industry,
        test_type=template.test_type,
        description=template.description,
        parameters=template.parameters or {},
        cost_factors=template.cost_factors or {},
        typical_labor_hours=template.typical_labor_hours or {},
        reference_docs=template.reference_docs or [],
        sample_images=template.sample_images or [],
        use_count=template.use_count or 0,
        is_active=template.is_active,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get(
    "/templates/{template_id}",
    response_model=TechnicalParameterTemplateResponse,
    summary="获取技术参数模板详情",
)
def get_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取指定技术参数模板的详细信息"""
    service = TechnicalParameterService(db)
    template = service.get_template_by_id(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板不存在: {template_id}",
        )

    return TechnicalParameterTemplateResponse(
        id=template.id,
        name=template.name,
        code=template.code,
        industry=template.industry,
        test_type=template.test_type,
        description=template.description,
        parameters=template.parameters or {},
        cost_factors=template.cost_factors or {},
        typical_labor_hours=template.typical_labor_hours or {},
        reference_docs=template.reference_docs or [],
        sample_images=template.sample_images or [],
        use_count=template.use_count or 0,
        is_active=template.is_active,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.put(
    "/templates/{template_id}",
    response_model=TechnicalParameterTemplateResponse,
    summary="更新技术参数模板",
)
def update_template(
    template_id: int,
    data: TechnicalParameterTemplateUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """更新技术参数模板"""
    service = TechnicalParameterService(db)

    # 过滤掉 None 值
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    template = service.update_template(template_id, **update_data)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板不存在: {template_id}",
        )

    return TechnicalParameterTemplateResponse(
        id=template.id,
        name=template.name,
        code=template.code,
        industry=template.industry,
        test_type=template.test_type,
        description=template.description,
        parameters=template.parameters or {},
        cost_factors=template.cost_factors or {},
        typical_labor_hours=template.typical_labor_hours or {},
        reference_docs=template.reference_docs or [],
        sample_images=template.sample_images or [],
        use_count=template.use_count or 0,
        is_active=template.is_active,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除技术参数模板",
)
def delete_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """删除技术参数模板（软删除）"""
    service = TechnicalParameterService(db)
    success = service.delete_template(template_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板不存在: {template_id}",
        )


# ==================== 模板匹配 ====================


@router.get(
    "/templates/match",
    response_model=List[TechnicalParameterTemplateListItem],
    summary="匹配技术参数模板",
    description="根据行业和测试类型智能匹配推荐模板",
)
def match_templates(
    industry: str = Query(..., description="行业"),
    test_type: str = Query(..., description="测试类型"),
    top_k: int = Query(5, ge=1, le=20, description="返回数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """根据行业和测试类型匹配推荐模板"""
    service = TechnicalParameterService(db)
    templates = service.match_templates(
        industry=industry,
        test_type=test_type,
        top_k=top_k,
    )

    return [
        TechnicalParameterTemplateListItem(
            id=t.id,
            name=t.name,
            code=t.code,
            industry=t.industry,
            test_type=t.test_type,
            description=t.description,
            use_count=t.use_count or 0,
            is_active=t.is_active,
            created_at=t.created_at,
        )
        for t in templates
    ]


# ==================== 成本估算 ====================


@router.post(
    "/estimate-cost",
    response_model=CostEstimateResponse,
    summary="估算成本",
    description="基于模板和技术参数估算项目成本",
)
def estimate_cost(
    data: CostEstimateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """基于模板和技术参数估算项目成本"""
    service = TechnicalParameterService(db)

    try:
        result = service.estimate_cost(
            template_id=data.template_id,
            parameters=data.parameters,
        )
        return CostEstimateResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/batch-estimate-cost",
    response_model=List[CostEstimateResponse],
    summary="批量估算成本",
    description="对多个匹配的模板进行成本估算对比",
)
def batch_estimate_cost(
    data: BatchCostEstimateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """批量估算多个模板的成本"""
    service = TechnicalParameterService(db)
    results = service.batch_estimate_costs(
        industry=data.industry,
        test_type=data.test_type,
        parameters=data.parameters,
    )
    return [CostEstimateResponse(**r) for r in results]


# ==================== 统计分析 ====================


@router.get(
    "/statistics/industries",
    response_model=List[IndustryStatistics],
    summary="获取行业统计",
)
def get_industry_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取各行业的模板统计数据"""
    service = TechnicalParameterService(db)
    return [IndustryStatistics(**s) for s in service.get_industry_statistics()]


@router.get(
    "/statistics/test-types",
    response_model=List[TestTypeStatistics],
    summary="获取测试类型统计",
)
def get_test_type_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取各测试类型的模板统计数据"""
    service = TechnicalParameterService(db)
    return [TestTypeStatistics(**s) for s in service.get_test_type_statistics()]
