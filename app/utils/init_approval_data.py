# -*- coding: utf-8 -*-
"""Seed unified approval templates, flows, nodes, and routing rules."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.approval import (
    ApprovalFlowDefinition,
    ApprovalNodeDefinition,
    ApprovalRoutingRule,
    ApprovalTemplate,
)
from app.models.user import User


def _node(node_code: str, node_name: str, node_order: int, approval_mode: str = "SINGLE") -> dict:
    return {
        "node_code": node_code,
        "node_name": node_name,
        "node_order": node_order,
        "approval_mode": approval_mode,
    }


APPROVAL_WORKFLOW_SEEDS: list[dict[str, Any]] = [
    {
        "template_code": "SALES_QUOTE_APPROVAL",
        "template_name": "销售报价审批",
        "category": "BUSINESS",
        "entity_type": "QUOTE",
        "description": "销售报价审批流程，按金额和毛利率路由。",
        "flows": [
            {
                "flow_name": "标准报价审批",
                "is_default": True,
                "nodes": [_node("QUOTE_SALES_MANAGER", "销售经理审批", 1)],
            },
            {
                "flow_name": "低毛利报价审批",
                "nodes": [
                    _node("QUOTE_LOW_MARGIN_SALES", "销售经理审批", 1),
                    _node("QUOTE_LOW_MARGIN_FINANCE", "财务复核", 2),
                    _node("QUOTE_LOW_MARGIN_GM", "总经理审批", 3),
                    _node("QUOTE_LOW_MARGIN_RISK", "风险复核", 4),
                    _node("QUOTE_LOW_MARGIN_LEGAL", "法务复核", 5),
                    _node("QUOTE_LOW_MARGIN_FINAL", "最终审批", 6),
                    _node("QUOTE_LOW_MARGIN_CC_REVIEW", "抄送确认", 7),
                ],
            },
        ],
        "routing_rules": [
            {
                "rule_name": "低毛利报价",
                "flow_name": "低毛利报价审批",
                "rule_order": 10,
                "conditions": {
                    "operator": "OR",
                    "items": [
                        {"field": "form_data.gross_margin", "op": "<", "value": 0.1},
                        {"field": "form_data.entity.gross_margin", "op": "<", "value": 0.1},
                    ],
                },
            },
            {
                "rule_name": "大额报价",
                "flow_name": "低毛利报价审批",
                "rule_order": 20,
                "conditions": {
                    "operator": "OR",
                    "items": [
                        {"field": "form_data.total_price", "op": ">=", "value": 500000},
                        {"field": "form_data.entity.total_price", "op": ">=", "value": 500000},
                    ],
                },
            },
        ],
    },
    {
        "template_code": "SALES_CONTRACT_APPROVAL",
        "template_name": "销售合同审批",
        "category": "BUSINESS",
        "entity_type": "CONTRACT",
        "description": "销售合同审批流程。",
        "flows": [
            {
                "flow_name": "默认销售合同审批",
                "is_default": True,
                "nodes": [_node("CONTRACT_SALES_MANAGER", "销售经理审批", 1)],
            }
        ],
    },
    {
        "template_code": "TPL_INVOICE",
        "template_name": "销售发票审批",
        "category": "FINANCE",
        "entity_type": "INVOICE",
        "description": "销售发票开票审批流程。",
        "flows": [
            {
                "flow_name": "默认销售发票审批",
                "is_default": True,
                "nodes": [_node("INVOICE_FINANCE_REVIEW", "财务复核", 1)],
            }
        ],
    },
    {
        "template_code": "ECN_STANDARD",
        "template_name": "ECN 标准审批",
        "category": "ENGINEERING",
        "entity_type": "ECN",
        "description": "工程变更审批流程，重大影响走强化审批。",
        "flows": [
            {
                "flow_name": "ECN 标准审批",
                "is_default": True,
                "nodes": [_node("ECN_ENGINEERING_REVIEW", "工程评审", 1)],
            },
            {
                "flow_name": "ECN 重大影响审批",
                "nodes": [
                    _node("ECN_MAJOR_ENGINEERING", "工程会签", 1, "AND_SIGN"),
                    _node("ECN_MAJOR_PURCHASE", "采购评估", 2),
                    _node("ECN_MAJOR_FINANCE", "财务评估", 3),
                    _node("ECN_MAJOR_GM", "总经理审批", 4),
                    _node("ECN_MAJOR_QUALITY", "质量评估", 5),
                    _node("ECN_MAJOR_SUPPLY", "供应链评估", 6),
                    _node("ECN_MAJOR_FINAL", "最终确认", 7),
                ],
            },
        ],
        "routing_rules": [
            {
                "rule_name": "重大 ECN 影响",
                "flow_name": "ECN 重大影响审批",
                "rule_order": 10,
                "conditions": {
                    "operator": "OR",
                    "items": [
                        {"field": "form_data.cost_impact", "op": ">=", "value": 1000000},
                        {"field": "form_data.schedule_impact_days", "op": ">=", "value": 30},
                    ],
                },
            }
        ],
    },
    {
        "template_code": "TIMESHEET_APPROVAL",
        "template_name": "工时审批",
        "category": "HR",
        "entity_type": "TIMESHEET",
        "description": "员工工时审批流程。",
        "flows": [
            {
                "flow_name": "默认工时审批",
                "is_default": True,
                "nodes": [_node("TIMESHEET_MANAGER_APPROVAL", "直属主管审批", 1)],
            }
        ],
    },
    {
        "template_code": "TPL_PURCHASE",
        "template_name": "采购订单审批",
        "category": "PURCHASE",
        "entity_type": "PURCHASE_ORDER",
        "description": "采购订单审批流程。",
        "flows": [
            {
                "flow_name": "标准采购订单审批",
                "is_default": True,
                "nodes": [_node("PURCHASE_MANAGER_REVIEW", "采购经理审批", 1)],
            },
            {
                "flow_name": "大额采购订单审批",
                "nodes": [
                    _node("PURCHASE_HIGH_MANAGER", "采购经理审批", 1),
                    _node("PURCHASE_HIGH_FINANCE", "财务复核", 2),
                    _node("PURCHASE_HIGH_GM", "总经理审批", 3),
                    _node("PURCHASE_HIGH_RISK", "风险复核", 4),
                    _node("PURCHASE_HIGH_LEGAL", "法务复核", 5),
                    _node("PURCHASE_HIGH_FINAL", "最终确认", 6),
                ],
            },
        ],
    },
    {
        "template_code": "TPL_OUTSOURCING",
        "template_name": "外协订单审批",
        "category": "OUTSOURCING",
        "entity_type": "OUTSOURCING_ORDER",
        "description": "外协订单审批流程。",
        "flows": [
            {
                "flow_name": "默认外协订单审批",
                "is_default": True,
                "nodes": [_node("OUTSOURCING_MANAGER_REVIEW", "外协负责人审批", 1)],
            }
        ],
    },
    {
        "template_code": "TPL_ACCEPTANCE",
        "template_name": "验收单审批",
        "category": "QUALITY",
        "entity_type": "ACCEPTANCE_ORDER",
        "description": "验收单审批流程。",
        "flows": [
            {
                "flow_name": "默认验收单审批",
                "is_default": True,
                "nodes": [_node("ACCEPTANCE_QA_REVIEW", "质量负责人审批", 1)],
            }
        ],
    },
    {
        "template_code": "TPL_DELIVERY_ORDER",
        "template_name": "发货单审批",
        "category": "BUSINESS",
        "entity_type": "DELIVERY_ORDER",
        "description": "商务支持发货单审批流程。",
        "flows": [
            {
                "flow_name": "默认发货单审批",
                "is_default": True,
                "nodes": [_node("DELIVERY_ORDER_MANAGER_REVIEW", "发货负责人审批", 1)],
            }
        ],
    },
    {
        "template_code": "TPL_PROJECT_BUDGET",
        "template_name": "项目预算审批",
        "category": "FINANCE",
        "entity_type": "PROJECT_BUDGET",
        "description": "项目预算提交与审批流程。",
        "flows": [
            {
                "flow_name": "默认项目预算审批",
                "is_default": True,
                "nodes": [_node("PROJECT_BUDGET_FINANCE_REVIEW", "财务负责人审批", 1)],
            }
        ],
    },
    {
        "template_code": "TPL_PROJECT",
        "template_name": "项目立项审批",
        "category": "PROJECT",
        "entity_type": "PROJECT",
        "description": "项目立项审批流程。",
        "flows": [
            {
                "flow_name": "默认项目立项审批",
                "is_default": True,
                "nodes": [_node("PROJECT_PM_APPROVAL", "项目经理审批", 1)],
            }
        ],
    },
    {
        "template_code": "PROJECT_STAGE_OVERRIDE",
        "template_name": "项目阶段门特批",
        "category": "PROJECT",
        "entity_type": "PROJECT",
        "description": "项目阶段门未满足时的特批审批流程。",
        "flows": [
            {
                "flow_name": "默认项目阶段门特批",
                "is_default": True,
                "nodes": [_node("STAGE_OVERRIDE_PM_REVIEW", "项目经理复核", 1)],
            }
        ],
    },
]


def _admin_user_id(db: Session) -> int | None:
    admin = db.query(User).filter(User.username == "admin").first()
    return admin.id if admin else None


def _approver_fields(admin_id: int | None) -> tuple[str, dict[str, Any]]:
    if admin_id:
        return "FIXED_USER", {"user_ids": [admin_id]}
    return "ROLE", {"role_codes": ["ADMIN"]}


def _upsert_template(db: Session, seed: dict[str, Any], admin_id: int | None) -> ApprovalTemplate:
    template = (
        db.query(ApprovalTemplate)
        .filter(ApprovalTemplate.template_code == seed["template_code"])
        .first()
    )
    if not template:
        template = ApprovalTemplate(template_code=seed["template_code"])
        db.add(template)

    template.template_name = seed["template_name"]
    template.category = seed["category"]
    template.entity_type = seed["entity_type"]
    template.description = seed.get("description")
    template.form_schema = seed.get("form_schema")
    template.version = 1
    template.is_active = True
    template.is_published = True
    template.published_at = template.published_at or datetime.now()
    template.published_by = template.published_by or admin_id
    template.created_by = template.created_by or admin_id
    db.flush()
    return template


def _upsert_flow(
    db: Session,
    template: ApprovalTemplate,
    flow_seed: dict[str, Any],
    admin_id: int | None,
) -> ApprovalFlowDefinition:
    flow = (
        db.query(ApprovalFlowDefinition)
        .filter(
            ApprovalFlowDefinition.template_id == template.id,
            ApprovalFlowDefinition.flow_name == flow_seed["flow_name"],
        )
        .first()
    )
    if not flow:
        flow = ApprovalFlowDefinition(template_id=template.id, flow_name=flow_seed["flow_name"])
        db.add(flow)

    flow.description = flow_seed.get("description")
    flow.is_default = bool(flow_seed.get("is_default", False))
    flow.version = 1
    flow.is_active = True
    flow.created_by = flow.created_by or admin_id
    db.flush()
    return flow


def _upsert_node(
    db: Session,
    flow: ApprovalFlowDefinition,
    node_seed: dict[str, Any],
    admin_id: int | None,
) -> ApprovalNodeDefinition:
    node = (
        db.query(ApprovalNodeDefinition)
        .filter(
            ApprovalNodeDefinition.flow_id == flow.id,
            ApprovalNodeDefinition.node_code == node_seed["node_code"],
        )
        .first()
    )
    if not node:
        node = ApprovalNodeDefinition(flow_id=flow.id, node_code=node_seed["node_code"])
        db.add(node)

    approver_type, approver_config = _approver_fields(admin_id)
    node.node_name = node_seed["node_name"]
    node.node_order = node_seed["node_order"]
    node.node_type = node_seed.get("node_type", "APPROVAL")
    node.approval_mode = node_seed.get("approval_mode", "SINGLE")
    node.is_active = True
    node.approver_type = approver_type
    node.approver_config = approver_config
    node.notify_config = node.notify_config or {}
    db.flush()
    return node


def _upsert_routing_rule(
    db: Session,
    template: ApprovalTemplate,
    flow_by_name: dict[str, ApprovalFlowDefinition],
    rule_seed: dict[str, Any],
    admin_id: int | None,
) -> ApprovalRoutingRule:
    rule = (
        db.query(ApprovalRoutingRule)
        .filter(
            ApprovalRoutingRule.template_id == template.id,
            ApprovalRoutingRule.rule_name == rule_seed["rule_name"],
        )
        .first()
    )
    if not rule:
        rule = ApprovalRoutingRule(template_id=template.id, rule_name=rule_seed["rule_name"])
        db.add(rule)

    rule.flow_id = flow_by_name[rule_seed["flow_name"]].id
    rule.rule_order = rule_seed["rule_order"]
    rule.description = rule_seed.get("description")
    rule.conditions = rule_seed["conditions"]
    rule.is_active = True
    rule.created_by = rule.created_by or admin_id
    db.flush()
    return rule


def init_approval_workflow_seeds(db: Session) -> dict[str, int]:
    """Create or repair default approval workflow seeds.

    The seed is intentionally idempotent: it updates known seed rows in place and
    creates only missing templates, flows, nodes, and routing rules.
    """
    admin_id = _admin_user_id(db)
    created_or_updated = {"templates": 0, "flows": 0, "nodes": 0, "routing_rules": 0}

    for seed in APPROVAL_WORKFLOW_SEEDS:
        template = _upsert_template(db, seed, admin_id)
        created_or_updated["templates"] += 1

        flow_by_name: dict[str, ApprovalFlowDefinition] = {}
        for flow_seed in seed["flows"]:
            flow = _upsert_flow(db, template, flow_seed, admin_id)
            flow_by_name[flow.flow_name] = flow
            created_or_updated["flows"] += 1

            for node_seed in flow_seed["nodes"]:
                _upsert_node(db, flow, node_seed, admin_id)
                created_or_updated["nodes"] += 1

        for rule_seed in seed.get("routing_rules", []):
            _upsert_routing_rule(db, template, flow_by_name, rule_seed, admin_id)
            created_or_updated["routing_rules"] += 1

    return created_or_updated
