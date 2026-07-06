# -*- coding: utf-8 -*-
"""
技术评估模板 API endpoints

提供评估模板的 CRUD、评估项管理、风险管理和版本控制接口。
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales.assessment_template import (
    AssessmentItem,
    AssessmentRisk,
    AssessmentTemplate,
    AssessmentVersion,
)
from app.models.sales.operation_log import SalesEntityType, SalesOperationType
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.sales.assessment_template_service import (
    AssessmentRiskService,
    AssessmentTemplateService,
    AssessmentVersionService,
)
from app.services.sales.operation_log_service import SalesOperationLogService

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
    risk_title: Optional[str] = Field(None, description="风险标题")
    risk_description: str = Field(..., description="风险描述")
    risk_level: str = Field(default="MEDIUM", description="风险等级")
    source_item_id: Optional[int] = Field(None, description="来源评估项ID")
    mitigation_plan: Optional[str] = Field(None, description="缓解措施")


class RiskStatusUpdateRequest(BaseModel):
    """更新风险状态请求"""

    model_config = ConfigDict(populate_by_name=True)

    status: str = Field(..., description="新状态")
    note: Optional[str] = Field(None, description="备注")


class VersionCreateRequest(BaseModel):
    """创建评估版本请求"""

    model_config = ConfigDict(populate_by_name=True)

    change_summary: str = Field(..., description="变更摘要")


def _probability_impact_for_level(risk_level: str) -> tuple[str, str]:
    """Map the legacy risk_level-only request onto the service probability/impact model."""
    level = (risk_level or "MEDIUM").upper()
    if level == "LOW":
        return "LOW", "LOW"
    if level == "HIGH":
        return "MEDIUM", "MEDIUM"
    if level == "CRITICAL":
        return "HIGH", "MEDIUM"
    return "LOW", "MEDIUM"


def _audit_scalar(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    return value


def _assessment_template_audit_value(template: AssessmentTemplate) -> dict[str, Any]:
    return {
        "id": template.id,
        "template_code": template.template_code,
        "template_name": template.template_name,
        "category": _audit_scalar(template.category),
        "description": template.description,
        "dimension_weights": template.dimension_weights,
        "veto_rules": template.veto_rules,
        "score_thresholds": template.score_thresholds,
        "version": template.version,
        "is_active": bool(template.is_active),
        "is_default": bool(template.is_default),
        "created_by": template.created_by,
    }


def _assessment_item_audit_value(item: AssessmentItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "template_id": item.template_id,
        "item_code": item.item_code,
        "item_name": item.item_name,
        "dimension": _audit_scalar(item.dimension),
        "description": item.description,
        "max_score": item.max_score,
        "weight": _audit_scalar(item.weight),
        "scoring_criteria": item.scoring_criteria,
        "is_veto_item": bool(item.is_veto_item),
        "veto_threshold": item.veto_threshold,
        "is_required": bool(item.is_required),
        "sort_order": item.sort_order,
    }


def _assessment_risk_audit_value(risk: AssessmentRisk) -> dict[str, Any]:
    return {
        "id": risk.id,
        "assessment_id": risk.assessment_id,
        "risk_code": risk.risk_code,
        "risk_title": risk.risk_title,
        "risk_category": risk.risk_category,
        "risk_description": risk.risk_description,
        "probability": _audit_scalar(risk.probability),
        "impact": _audit_scalar(risk.impact),
        "risk_level": _audit_scalar(risk.risk_level),
        "risk_score": risk.risk_score,
        "mitigation_plan": risk.mitigation_plan,
        "contingency_plan": risk.contingency_plan,
        "owner_id": risk.owner_id,
        "status": _audit_scalar(risk.status),
        "due_date": _audit_scalar(risk.due_date),
        "resolved_at": _audit_scalar(risk.resolved_at),
        "resolution_notes": risk.resolution_notes,
    }


def _assessment_version_audit_value(version: AssessmentVersion) -> dict[str, Any]:
    return {
        "id": version.id,
        "assessment_id": version.assessment_id,
        "version_no": version.version_no,
        "version_note": version.version_note,
        "snapshot_data": version.snapshot_data,
        "dimension_scores": version.dimension_scores,
        "total_score": version.total_score,
        "decision": version.decision,
        "evaluator_id": version.evaluator_id,
        "evaluated_at": _audit_scalar(version.evaluated_at),
    }


def _changed_fields(
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any] | None,
) -> list[str]:
    old_snapshot = old_value or {}
    new_snapshot = new_value or {}
    return [
        field
        for field, value in new_snapshot.items()
        if field in old_snapshot and old_snapshot.get(field) != value
    ]


def _log_assessment_operation(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    entity_code: str | None,
    operation_type: str,
    current_user: User,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any] | None,
    operation_desc: str,
    changed_fields: list[str] | None = None,
    remark: str | None = None,
) -> None:
    SalesOperationLogService.log_operation(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_code=entity_code,
        operation_type=operation_type,
        operator=current_user,
        operation_desc=operation_desc,
        old_value=old_value,
        new_value=new_value,
        changed_fields=changed_fields,
        remark=remark,
    )


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
    _log_assessment_operation(
        db,
        entity_type=SalesEntityType.ASSESSMENT_TEMPLATE,
        entity_id=template.id,
        entity_code=template.template_code,
        operation_type=SalesOperationType.CREATE,
        current_user=current_user,
        old_value={},
        new_value=_assessment_template_audit_value(template),
        changed_fields=[],
        operation_desc="创建技术评估模板",
        remark=template.description,
    )
    db.commit()

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

    old_template = service.get_template(template_id, include_items=False)
    if not old_template:
        raise HTTPException(status_code=404, detail="模板不存在")
    old_value = _assessment_template_audit_value(old_template)

    template = service.update_template(template_id, **update_data)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    new_value = _assessment_template_audit_value(template)
    _log_assessment_operation(
        db,
        entity_type=SalesEntityType.ASSESSMENT_TEMPLATE,
        entity_id=template.id,
        entity_code=template.template_code,
        operation_type=SalesOperationType.UPDATE,
        current_user=current_user,
        old_value=old_value,
        new_value=new_value,
        changed_fields=_changed_fields(old_value, new_value),
        operation_desc="更新技术评估模板",
        remark=template.description,
    )
    db.commit()

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
    old_template = service.get_template(template_id, include_items=False)
    old_value = _assessment_template_audit_value(old_template) if old_template else None
    template = service.set_default_template(template_id, category)

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    new_value = _assessment_template_audit_value(template)
    _log_assessment_operation(
        db,
        entity_type=SalesEntityType.ASSESSMENT_TEMPLATE,
        entity_id=template.id,
        entity_code=template.template_code,
        operation_type=SalesOperationType.STATUS_CHANGE,
        current_user=current_user,
        old_value=old_value,
        new_value=new_value,
        changed_fields=_changed_fields(old_value, new_value),
        operation_desc="设置默认技术评估模板",
        remark=category,
    )
    db.commit()

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
        scoring_criteria=request.score_criteria,
        is_veto_item=request.is_veto_item,
        veto_threshold=request.veto_threshold,
        is_required=request.is_required,
    )
    _log_assessment_operation(
        db,
        entity_type=SalesEntityType.ASSESSMENT_ITEM,
        entity_id=item.id,
        entity_code=item.item_code,
        operation_type=SalesOperationType.CREATE,
        current_user=current_user,
        old_value={},
        new_value=_assessment_item_audit_value(item),
        changed_fields=[],
        operation_desc="新增技术评估项",
        remark=f"template_id={template_id}",
    )
    db.commit()

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

    items_data = []
    for item in request.items:
        item_data = item.model_dump()
        item_data["scoring_criteria"] = item.score_criteria
        items_data.append(item_data)
    items = service.batch_add_items(template_id, items_data)
    for item in items:
        _log_assessment_operation(
            db,
            entity_type=SalesEntityType.ASSESSMENT_ITEM,
            entity_id=item.id,
            entity_code=item.item_code,
            operation_type=SalesOperationType.CREATE,
            current_user=current_user,
            old_value={},
            new_value=_assessment_item_audit_value(item),
            changed_fields=[],
            operation_desc="批量新增技术评估项",
            remark=f"template_id={template_id}",
        )
    db.commit()

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
    probability, impact = _probability_impact_for_level(request.risk_level)

    risk = service.create_risk(
        assessment_id=assessment_id,
        risk_title=request.risk_title or f"{request.risk_type}风险",
        risk_description=request.risk_description,
        risk_category=request.risk_type,
        probability=probability,
        impact=impact,
        mitigation_plan=request.mitigation_plan,
        owner_id=current_user.id,
    )

    if not risk:
        raise HTTPException(status_code=400, detail="创建风险失败")
    _log_assessment_operation(
        db,
        entity_type=SalesEntityType.ASSESSMENT_RISK,
        entity_id=risk.id,
        entity_code=risk.risk_code,
        operation_type=SalesOperationType.CREATE,
        current_user=current_user,
        old_value={},
        new_value=_assessment_risk_audit_value(risk),
        changed_fields=[],
        operation_desc="创建技术评估风险",
        remark=f"assessment_id={assessment_id}",
    )
    db.commit()

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
                    "risk_title": r.risk_title,
                    "risk_type": r.risk_category,
                    "risk_category": r.risk_category,
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
    old_risk = db.query(AssessmentRisk).filter(AssessmentRisk.id == risk_id).first()
    old_value = _assessment_risk_audit_value(old_risk) if old_risk else None
    risk = service.update_risk_status(
        risk_id,
        request.status,
        resolution_notes=request.note,
    )

    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")
    new_value = _assessment_risk_audit_value(risk)
    _log_assessment_operation(
        db,
        entity_type=SalesEntityType.ASSESSMENT_RISK,
        entity_id=risk.id,
        entity_code=risk.risk_code,
        operation_type=SalesOperationType.STATUS_CHANGE,
        current_user=current_user,
        old_value=old_value,
        new_value=new_value,
        changed_fields=_changed_fields(old_value, new_value),
        operation_desc="更新技术评估风险状态",
        remark=request.note,
    )
    db.commit()

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
    request: Optional[VersionCreateRequest] = Body(None),
    change_summary: Optional[str] = Query(None, description="变更摘要"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建评估版本快照"""
    service = AssessmentVersionService(db)
    summary = request.change_summary if request else change_summary
    if not summary:
        raise HTTPException(status_code=422, detail="变更摘要不能为空")

    version = service.create_version_snapshot(
        assessment_id=assessment_id,
        change_summary=summary,
        created_by=current_user.id,
    )

    if not version:
        raise HTTPException(status_code=400, detail="创建版本失败")
    _log_assessment_operation(
        db,
        entity_type=SalesEntityType.ASSESSMENT_VERSION,
        entity_id=version.id,
        entity_code=version.version_no,
        operation_type=SalesOperationType.CREATE,
        current_user=current_user,
        old_value={},
        new_value=_assessment_version_audit_value(version),
        changed_fields=[],
        operation_desc="创建技术评估版本快照",
        remark=summary,
    )
    db.commit()

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
                    "change_summary": v.version_note,
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
    diff = service.compare_version_records(version_id, compare_to_version_id)

    if not diff:
        raise HTTPException(status_code=404, detail="版本不存在")

    return ResponseModel(code=200, message="对比完成", data=diff)
