# -*- coding: utf-8 -*-
"""
审批模板管理 API
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.approval import (
    ApprovalFlowDefinition,
    ApprovalNodeDefinition,
    ApprovalRoutingRule,
    ApprovalTemplate,
)
from app.schemas.approval.flow import (
    ApprovalFlowCreate,
    ApprovalFlowResponse,
    ApprovalFlowUpdate,
    ApprovalNodeCreate,
    ApprovalNodeResponse,
    ApprovalNodeUpdate,
    ApprovalRoutingRuleCreate,
    ApprovalRoutingRuleResponse,
)
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.schemas.approval.template import (
    ApprovalTemplateCreate,
    ApprovalTemplateListResponse,
    ApprovalTemplateResponse,
    ApprovalTemplateUpdate,
)
from app.utils.db_helpers import get_or_404, save_obj

router = APIRouter()


# ==================== 模板 CRUD ====================

@router.get("", response_model=ApprovalTemplateListResponse)
def list_templates(
    pagination: PaginationParams = Depends(get_pagination_query),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(deps.get_db),
):
    """获取审批模板列表"""
    query = db.query(ApprovalTemplate)

    if category:
        query = query.filter(ApprovalTemplate.category == category)
    if is_active is not None:
        query = query.filter(ApprovalTemplate.is_active == is_active)
    query = apply_keyword_filter(query, ApprovalTemplate, keyword, ["template_name", "template_code"])

    total = query.count()
    items = apply_pagination(query.order_by(ApprovalTemplate.id.desc()), pagination.offset, pagination.limit).all()

    return ApprovalTemplateListResponse(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        items=[ApprovalTemplateResponse.model_validate(t) for t in items],
    )


@router.get("/{template_id}", response_model=ApprovalTemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
):
    """获取审批模板详情"""
    template = get_or_404(db, ApprovalTemplate, template_id, "模板不存在")
    return ApprovalTemplateResponse.model_validate(template)


@router.post("", response_model=ApprovalTemplateResponse)
def create_template(
    data: ApprovalTemplateCreate,
    db: Session = Depends(deps.get_db),
):
    """创建审批模板"""
    # 检查编码唯一性
    existing = db.query(ApprovalTemplate).filter(ApprovalTemplate.template_code == data.template_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"模板编码已存在: {data.template_code}")

    template = ApprovalTemplate(**data.model_dump())
    save_obj(db, template)

    return ApprovalTemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=ApprovalTemplateResponse)
def update_template(
    template_id: int,
    data: ApprovalTemplateUpdate,
    db: Session = Depends(deps.get_db),
):
    """更新审批模板"""
    template = get_or_404(db, ApprovalTemplate, template_id, "模板不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)

    db.commit()
    db.refresh(template)

    return ApprovalTemplateResponse.model_validate(template)


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
):
    """删除审批模板（软删除）"""
    template = get_or_404(db, ApprovalTemplate, template_id, "模板不存在")

    template.is_active = False
    db.commit()

    return {"message": "删除成功"}


@router.post("/{template_id}/publish")
def publish_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
):
    """发布审批模板"""
    template = get_or_404(db, ApprovalTemplate, template_id, "模板不存在")

    # 检查是否有默认流程
    default_flow = (
        db.query(ApprovalFlowDefinition)
        .filter(
            ApprovalFlowDefinition.template_id == template_id,
            ApprovalFlowDefinition.is_default,
            ApprovalFlowDefinition.is_active,
        )
        .first()
    )

    if not default_flow:
        raise HTTPException(status_code=400, detail="请先配置默认审批流程")

    template.is_published = True
    template.version += 1
    db.commit()

    return {"message": "发布成功", "version": template.version}


# ==================== 流程定义 ====================

@router.get("/{template_id}/flows", response_model=list[ApprovalFlowResponse])
def list_flows(
    template_id: int,
    db: Session = Depends(deps.get_db),
):
    """获取模板的流程列表"""
    flows = (
        db.query(ApprovalFlowDefinition)
        .filter(
            ApprovalFlowDefinition.template_id == template_id,
            ApprovalFlowDefinition.is_active,
        )
        .all()
    )

    result = []
    for flow in flows:
        flow_data = ApprovalFlowResponse.model_validate(flow)
        # 加载节点
        nodes = (
            db.query(ApprovalNodeDefinition)
            .filter(
                ApprovalNodeDefinition.flow_id == flow.id,
                ApprovalNodeDefinition.is_active,
            )
            .order_by(ApprovalNodeDefinition.node_order)
            .all()
        )
        flow_data.nodes = [ApprovalNodeResponse.model_validate(n) for n in nodes]
        result.append(flow_data)

    return result


@router.post("/{template_id}/flows", response_model=ApprovalFlowResponse)
def create_flow(
    template_id: int,
    data: ApprovalFlowCreate,
    db: Session = Depends(deps.get_db),
):
    """创建审批流程"""
    # 检查模板是否存在
    template = get_or_404(db, ApprovalTemplate, template_id, "模板不存在")

    # 如果设置为默认，取消其他默认
    if data.is_default:
        db.query(ApprovalFlowDefinition).filter(
            ApprovalFlowDefinition.template_id == template_id,
            ApprovalFlowDefinition.is_default,
        ).update({"is_default": False})

    flow = ApprovalFlowDefinition(
        template_id=template_id,
        flow_name=data.flow_name,
        flow_description=data.flow_description,
        is_default=data.is_default,
    )
    db.add(flow)
    db.flush()

    # 创建节点
    nodes = []
    if data.nodes:
        for idx, node_data in enumerate(data.nodes):
            node = ApprovalNodeDefinition(
                flow_id=flow.id,
                node_order=idx,
                **node_data.model_dump(exclude={"flow_id"}),
            )
            db.add(node)
            nodes.append(node)

    db.commit()
    db.refresh(flow)

    result = ApprovalFlowResponse.model_validate(flow)
    result.nodes = [ApprovalNodeResponse.model_validate(n) for n in nodes]

    return result


@router.put("/flows/{flow_id}", response_model=ApprovalFlowResponse)
def update_flow(
    flow_id: int,
    data: ApprovalFlowUpdate,
    db: Session = Depends(deps.get_db),
):
    """更新审批流程"""
    flow = get_or_404(db, ApprovalFlowDefinition, flow_id, "流程不存在")

    # 如果设置为默认，取消其他默认
    if data.is_default:
        db.query(ApprovalFlowDefinition).filter(
            ApprovalFlowDefinition.template_id == flow.template_id,
            ApprovalFlowDefinition.is_default,
            ApprovalFlowDefinition.id != flow_id,
        ).update({"is_default": False})

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(flow, key, value)

    db.commit()
    db.refresh(flow)

    return ApprovalFlowResponse.model_validate(flow)


@router.delete("/flows/{flow_id}")
def delete_flow(
    flow_id: int,
    db: Session = Depends(deps.get_db),
):
    """删除审批流程（软删除）"""
    flow = get_or_404(db, ApprovalFlowDefinition, flow_id, "流程不存在")

    flow.is_active = False
    db.commit()

    return {"message": "删除成功"}


# ==================== 节点定义 ====================

@router.post("/flows/{flow_id}/nodes", response_model=ApprovalNodeResponse)
def create_node(
    flow_id: int,
    data: ApprovalNodeCreate,
    db: Session = Depends(deps.get_db),
):
    """创建审批节点"""
    flow = get_or_404(db, ApprovalFlowDefinition, flow_id, "流程不存在")

    node = ApprovalNodeDefinition(
        flow_id=flow_id,
        **data.model_dump(exclude={"flow_id"}),
    )
    save_obj(db, node)

    return ApprovalNodeResponse.model_validate(node)


@router.put("/nodes/{node_id}", response_model=ApprovalNodeResponse)
def update_node(
    node_id: int,
    data: ApprovalNodeUpdate,
    db: Session = Depends(deps.get_db),
):
    """更新审批节点"""
    node = get_or_404(db, ApprovalNodeDefinition, node_id, "节点不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(node, key, value)

    db.commit()
    db.refresh(node)

    return ApprovalNodeResponse.model_validate(node)


@router.delete("/nodes/{node_id}")
def delete_node(
    node_id: int,
    db: Session = Depends(deps.get_db),
):
    """删除审批节点（软删除）"""
    node = get_or_404(db, ApprovalNodeDefinition, node_id, "节点不存在")

    node.is_active = False
    db.commit()

    return {"message": "删除成功"}


# ==================== 路由规则 ====================

@router.get("/{template_id}/rules", response_model=list[ApprovalRoutingRuleResponse])
def list_routing_rules(
    template_id: int,
    db: Session = Depends(deps.get_db),
):
    """获取模板的路由规则列表"""
    rules = (
        db.query(ApprovalRoutingRule)
        .filter(
            ApprovalRoutingRule.template_id == template_id,
            ApprovalRoutingRule.is_active,
        )
        .order_by(ApprovalRoutingRule.rule_order)
        .all()
    )

    return [ApprovalRoutingRuleResponse.model_validate(r) for r in rules]


@router.post("/{template_id}/rules", response_model=ApprovalRoutingRuleResponse)
def create_routing_rule(
    template_id: int,
    data: ApprovalRoutingRuleCreate,
    db: Session = Depends(deps.get_db),
):
    """创建路由规则"""
    rule = ApprovalRoutingRule(
        template_id=template_id,
        **data.model_dump(exclude={"template_id"}),
    )
    save_obj(db, rule)

    return ApprovalRoutingRuleResponse.model_validate(rule)


@router.delete("/rules/{rule_id}")
def delete_routing_rule(
    rule_id: int,
    db: Session = Depends(deps.get_db),
):
    """删除路由规则（软删除）"""
    rule = get_or_404(db, ApprovalRoutingRule, rule_id, "规则不存在")

    rule.is_active = False
    db.commit()

    return {"message": "删除成功"}
