# -*- coding: utf-8 -*-
"""
技术评估模板 API endpoints

提供评估模板的 CRUD、评估项管理、风险管理和版本控制接口。
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.sales.assessment_template_service import (
    AssessmentRiskService,
    AssessmentTemplateService,
    AssessmentVersionService,
)

router = APIRouter()


# ==================== 请求/响应模型 ====================


class TemplateCreateRequest(BaseModel):
    """创建模板请求"""

    model_config = ConfigDict(populate_by_name=True)

    template_code: str = Field(..., description="模板编码")
    template_name: str = Field(..., description="模板名称")
    category: str = Field(default="STANDARD", description="模板类型")
    description: Optional[str] = Field(None, description="模板描述")
    dimension_weights: Optional[Dict] = Field(None, description="维度权重配置")
    veto_rules: Optional[List[Dict]] = Field(None, description="一票否决规则")
    score_thresholds: Optional[Dict] = Field(None, description="评分阈值配置")


class TemplateUpdateRequest(BaseModel):
    """更新模板请求"""

    model_config = ConfigDict(populate_by_name=True)

    template_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    dimension_weights: Optional[Dict] = None
    veto_rules: Optional[List[Dict]] = None
    score_thresholds: Optional[Dict] = None
    is_active: Optional[bool] = None


class ItemCreateRequest(BaseModel):
    """创建评估项请求"""

    model_config = ConfigDict(populate_by_name=True)

    item_code: str = Field(..., description="评估项编码")
    item_name: str = Field(..., description="评估项名称")
    dimension: str = Field(..., description="所属维度")
    description: Optional[str] = None
    weight: float = Field(default=1.0, ge=0, le=10, description="权重")
    score_criteria: Optional[Dict] = Field(None, description="评分标准")
    is_veto_item: bool = Field(default=False, description="是否一票否决项")
    veto_threshold: Optional[float] = Field(None, description="否决阈值")
    is_required: bool = Field(default=True, description="是否必填")


class ItemBatchCreateRequest(BaseModel):
    """批量创建评估项请求"""

    model_config = ConfigDict(populate_by_name=True)

    items: List[ItemCreateRequest] = Field(..., description="评估项列表")


class RiskCreateRequest(BaseModel):
    """创建风险请求"""

    model_config = ConfigDict(populate_by_name=True)

    risk_type: str = Field(..., description="风险类型")
    risk_description: str = Field(..., description="风险描述")
    risk_level: str = Field(default="MEDIUM", description="风险等级")
    source_item_id: Optional[int] = Field(None, description="来源评估项ID")
    mitigation_plan: Optional[str] = Field(None, description="缓解措施")


class RiskStatusUpdateRequest(BaseModel):
    """更新风险状态请求"""

    model_config = ConfigDict(populate_by_name=True)

    status: str = Field(..., description="新状态")
    note: Optional[str] = Field(None, description="备注")


# ==================== 模板 API ====================


@router.get("/assessment-templates", response_model=ResponseModel)
def list_assessment_templates(
    *,
    db: Session = Depends(deps.get_db),
    category: Optional[str] = Query(None, description="模板类型"),
    is_active: Optional[bool] = Query(True, description="是否激活"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """列出评估模板"""
    service = AssessmentTemplateService(db)
    templates, total = service.list_templates(
        category=category, is_active=is_active, skip=skip, limit=limit
    )

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "items": [
                {
                    "id": t.id,
                    "template_code": t.template_code,
                    "template_name": t.template_name,
                    "category": t.category,
                    "is_default": t.is_default,
                    "is_active": t.is_active,
                    "version": t.version,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in templates
            ],
            "total": total,
        },
    )


@router.post("/assessment-templates", response_model=ResponseModel)
def create_assessment_template(
    *,
    db: Session = Depends(deps.get_db),
    request: TemplateCreateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建评估模板"""
    service = AssessmentTemplateService(db)

    # 检查编码是否重复
    existing = service.get_template_by_code(request.template_code)
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    template = service.create_template(
        template_code=request.template_code,
        template_name=request.template_name,
        category=request.category,
        description=request.description,
        dimension_weights=request.dimension_weights,
        veto_rules=request.veto_rules,
        score_thresholds=request.score_thresholds,
        created_by=current_user.id,
    )

    return ResponseModel(
        code=200,
        message="创建成功",
        data={"id": template.id, "template_code": template.template_code},
    )


@router.get("/assessment-templates/{template_id}", response_model=ResponseModel)
def get_assessment_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    include_items: bool = Query(True, description="是否包含评估项"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取评估模板详情"""
    service = AssessmentTemplateService(db)
    template = service.get_template(template_id, include_items=include_items)

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    data = {
        "id": template.id,
        "template_code": template.template_code,
        "template_name": template.template_name,
        "category": template.category,
        "description": template.description,
        "dimension_weights": template.dimension_weights,
        "veto_rules": template.veto_rules,
        "score_thresholds": template.score_thresholds,
        "is_default": template.is_default,
        "is_active": template.is_active,
        "version": template.version,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    }

    if include_items and template.items:
        data["items"] = [
            {
                "id": item.id,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "dimension": item.dimension,
                "weight": item.weight,
                "is_veto_item": item.is_veto_item,
                "is_required": item.is_required,
            }
            for item in template.items
        ]

    return ResponseModel(code=200, message="查询成功", data=data)


@router.put("/assessment-templates/{template_id}", response_model=ResponseModel)
def update_assessment_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    request: TemplateUpdateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新评估模板"""
    service = AssessmentTemplateService(db)
    update_data = request.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="无更新内容")

    template = service.update_template(template_id, **update_data)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    return ResponseModel(
        code=200,
        message="更新成功",
        data={"id": template.id, "template_code": template.template_code},
    )


@router.post("/assessment-templates/{template_id}/set-default", response_model=ResponseModel)
def set_default_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    category: str = Query(..., description="类型"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """设置默认模板"""
    service = AssessmentTemplateService(db)
    template = service.set_default_template(template_id, category)

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    return ResponseModel(
        code=200,
        message="设置成功",
        data={"id": template.id, "is_default": template.is_default},
    )


# ==================== 评估项 API ====================


@router.post("/assessment-templates/{template_id}/items", response_model=ResponseModel)
def add_assessment_item(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    request: ItemCreateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """添加评估项"""
    service = AssessmentTemplateService(db)

    # 验证模板存在
    template = service.get_template(template_id, include_items=False)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    item = service.add_assessment_item(
        template_id=template_id,
        item_code=request.item_code,
        item_name=request.item_name,
        dimension=request.dimension,
        description=request.description,
        weight=request.weight,
        score_criteria=request.score_criteria,
        is_veto_item=request.is_veto_item,
        veto_threshold=request.veto_threshold,
        is_required=request.is_required,
    )

    return ResponseModel(
        code=200,
        message="添加成功",
        data={"id": item.id, "item_code": item.item_code},
    )


@router.post("/assessment-templates/{template_id}/items/batch", response_model=ResponseModel)
def batch_add_assessment_items(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    request: ItemBatchCreateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """批量添加评估项"""
    service = AssessmentTemplateService(db)

    # 验证模板存在
    template = service.get_template(template_id, include_items=False)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    items_data = [item.model_dump() for item in request.items]
    items = service.batch_add_items(template_id, items_data)

    return ResponseModel(
        code=200,
        message=f"批量添加成功，共添加 {len(items)} 项",
        data={"count": len(items), "item_ids": [item.id for item in items]},
    )


# ==================== 风险 API ====================


@router.post("/assessments/{assessment_id}/risks", response_model=ResponseModel)
def create_assessment_risk(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    request: RiskCreateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建评估风险"""
    service = AssessmentRiskService(db)

    risk = service.create_risk(
        assessment_id=assessment_id,
        risk_type=request.risk_type,
        risk_description=request.risk_description,
        risk_level=request.risk_level,
        source_item_id=request.source_item_id,
        mitigation_plan=request.mitigation_plan,
        identified_by=current_user.id,
    )

    if not risk:
        raise HTTPException(status_code=400, detail="创建风险失败")

    return ResponseModel(
        code=200,
        message="创建成功",
        data={"id": risk.id, "risk_code": risk.risk_code},
    )


@router.get("/assessments/{assessment_id}/risks", response_model=ResponseModel)
def list_assessment_risks(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    status: Optional[str] = Query(None, description="风险状态"),
    level: Optional[str] = Query(None, description="风险等级"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取评估风险列表"""
    service = AssessmentRiskService(db)
    risks = service.get_risks_by_assessment(assessment_id, status=status, level=level)

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "items": [
                {
                    "id": r.id,
                    "risk_code": r.risk_code,
                    "risk_type": r.risk_type,
                    "risk_description": r.risk_description,
                    "risk_level": r.risk_level,
                    "status": r.status,
                    "mitigation_plan": r.mitigation_plan,
                }
                for r in risks
            ],
            "total": len(risks),
        },
    )


@router.put("/assessments/risks/{risk_id}/status", response_model=ResponseModel)
def update_risk_status(
    *,
    db: Session = Depends(deps.get_db),
    risk_id: int,
    request: RiskStatusUpdateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新风险状态"""
    service = AssessmentRiskService(db)
    risk = service.update_risk_status(risk_id, request.status, note=request.note)

    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")

    return ResponseModel(
        code=200,
        message="状态更新成功",
        data={"id": risk.id, "status": risk.status},
    )


# ==================== 版本 API ====================


@router.post("/assessments/{assessment_id}/versions", response_model=ResponseModel)
def create_assessment_version(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    change_summary: str = Query(..., description="变更摘要"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建评估版本快照"""
    service = AssessmentVersionService(db)
    version = service.create_version_snapshot(
        assessment_id=assessment_id,
        change_summary=change_summary,
        created_by=current_user.id,
    )

    if not version:
        raise HTTPException(status_code=400, detail="创建版本失败")

    return ResponseModel(
        code=200,
        message="版本创建成功",
        data={"id": version.id, "version_no": version.version_no},
    )


@router.get("/assessments/{assessment_id}/versions", response_model=ResponseModel)
def list_assessment_versions(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取评估版本历史"""
    service = AssessmentVersionService(db)
    versions = service.get_version_history(assessment_id)

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "items": [
                {
                    "id": v.id,
                    "version_no": v.version_no,
                    "change_summary": v.change_summary,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in versions
            ],
            "total": len(versions),
        },
    )


@router.get("/assessments/versions/{version_id}/compare", response_model=ResponseModel)
def compare_assessment_versions(
    *,
    db: Session = Depends(deps.get_db),
    version_id: int,
    compare_to_version_id: int = Query(..., description="对比版本ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """对比两个版本"""
    service = AssessmentVersionService(db)
    diff = service.compare_versions(version_id, compare_to_version_id)

    if not diff:
        raise HTTPException(status_code=404, detail="版本不存在")

    return ResponseModel(code=200, message="对比完成", data=diff)
