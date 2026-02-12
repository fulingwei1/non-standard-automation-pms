# -*- coding: utf-8 -*-
"""
模板管理通用工具函数

包含模板版本比较、序列化等辅助功能
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased

from app.models.sales import (
    ContractTemplate,
    CpqRuleSet,
    QuoteTemplate,
)
from app.models.user import User
from app.schemas.sales import (
    ContractTemplateResponse,
    ContractTemplateVersionResponse,
    CpqRuleSetResponse,
    QuoteTemplateResponse,
    QuoteTemplateVersionResponse,
    TemplateApprovalHistoryRecord,
    TemplateVersionDiff,
)


def _flatten_structure(data: Any, prefix: str = "") -> Dict[str, Any]:
    """将嵌套结构展开便于比较"""
    entries: Dict[str, Any] = {}
    if data is None:
        return entries
    if isinstance(data, dict):
        for key, value in data.items():
            sub_prefix = f"{prefix}.{key}" if prefix else str(key)
            entries.update(_flatten_structure(value, sub_prefix))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            sub_prefix = f"{prefix}[{index}]" if prefix else f"[{index}]"
            entries.update(_flatten_structure(value, sub_prefix))
    else:
        entries[prefix or "value"] = data
    return entries


def _build_diff_section(current: Any, previous: Any) -> Dict[str, Any]:
    current_flat = _flatten_structure(current)
    previous_flat = _flatten_structure(previous)

    added = sorted(list(set(current_flat.keys()) - set(previous_flat.keys())))
    removed = sorted(list(set(previous_flat.keys()) - set(current_flat.keys())))
    changed = []
    for key in current_flat.keys() & previous_flat.keys():
        if current_flat[key] != previous_flat[key]:
            changed.append(
                {
                    "path": key,
                    "old": previous_flat[key],
                    "new": current_flat[key],
                }
            )
    return {
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def _get_previous_version(template, current_version):
    """获取模板的上一版本"""
    if not template or not template.versions:
        return None
    versions = sorted(
        template.versions,
        key=lambda v: v.created_at or datetime.min,
        reverse=True,
    )
    for idx, version in enumerate(versions):
        if version.id == current_version.id and idx + 1 < len(versions):
            return versions[idx + 1]
    return None


def _build_template_version_diff(current_version, previous_version) -> TemplateVersionDiff:
    """构建模板版本差异"""
    sections_diff = _build_diff_section(
        getattr(current_version, "sections", None),
        getattr(previous_version, "sections", None) if previous_version else None,
    )
    pricing_diff = _build_diff_section(
        getattr(current_version, "pricing_rules", None),
        getattr(previous_version, "pricing_rules", None) if previous_version else None,
    )
    clause_diff = _build_diff_section(
        getattr(current_version, "clause_sections", None),
        getattr(previous_version, "clause_sections", None) if previous_version else None,
    )
    return TemplateVersionDiff(
        sections=sections_diff,
        pricing_rules=pricing_diff,
        clause_sections=clause_diff,
    )


def _build_template_history(template) -> List[TemplateApprovalHistoryRecord]:
    """构建模板审批历史"""
    if not template or not template.versions:
        return []
    versions = sorted(
        template.versions,
        key=lambda v: v.created_at or datetime.min,
        reverse=True,
    )
    history = []
    for version in versions[:10]:
        history.append(
            TemplateApprovalHistoryRecord(
                version_id=version.id,
                version_no=version.version_no,
                status=version.status,
                published_by=version.published_by,
                published_at=version.published_at,
                release_notes=version.release_notes,
            )
        )
    return history


def _filter_template_visibility(query, model, user: User):
    """根据可见范围过滤模板"""
    if user.is_superuser:
        return query
    owner_alias = aliased(User)
    query = query.outerjoin(owner_alias, model.owner)
    conditions = [
        model.visibility_scope == "ALL",
        model.owner_id == user.id,
    ]
    if user.department:
        conditions.append(
            and_(
                model.visibility_scope.in_(["TEAM", "DEPT"]),
                owner_alias.department == user.department,
            )
        )
    return query.filter(or_(*conditions))


def _serialize_quote_template(template: QuoteTemplate) -> QuoteTemplateResponse:
    """序列化报价模板"""
    versions = sorted(
        template.versions or [],
        key=lambda v: v.created_at or datetime.min,
        reverse=True,
    )
    version_responses = [
        QuoteTemplateVersionResponse(
            id=v.id,
            template_id=v.template_id,
            version_no=v.version_no,
            status=v.status,
            sections=v.sections,
            pricing_rules=v.pricing_rules,
            config_schema=v.config_schema,
            discount_rules=v.discount_rules,
            release_notes=v.release_notes,
            rule_set_id=v.rule_set_id,
            created_by=v.created_by,
            published_by=v.published_by,
            published_at=v.published_at,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
        for v in versions
    ]
    return QuoteTemplateResponse(
        id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        category=template.category,
        description=template.description,
        status=template.status,
        visibility_scope=template.visibility_scope,
        is_default=template.is_default,
        current_version_id=template.current_version_id,
        owner_id=template.owner_id,
        versions=version_responses,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def _serialize_contract_template(template: ContractTemplate) -> ContractTemplateResponse:
    """序列化合同模板"""
    versions = sorted(
        template.versions or [],
        key=lambda v: v.created_at or datetime.min,
        reverse=True,
    )
    version_responses = [
        ContractTemplateVersionResponse(
            id=v.id,
            template_id=v.template_id,
            version_no=v.version_no,
            status=v.status,
            clause_sections=v.clause_sections,
            clause_library=v.clause_library,
            attachment_refs=v.attachment_refs,
            approval_flow=v.approval_flow,
            release_notes=v.release_notes,
            created_by=v.created_by,
            published_by=v.published_by,
            published_at=v.published_at,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
        for v in versions
    ]
    return ContractTemplateResponse(
        id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        contract_type=template.contract_type,
        description=template.description,
        status=template.status,
        visibility_scope=template.visibility_scope,
        is_default=template.is_default,
        current_version_id=template.current_version_id,
        owner_id=template.owner_id,
        versions=version_responses,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def _serialize_rule_set(rule_set: CpqRuleSet) -> CpqRuleSetResponse:
    """序列化CPQ规则集"""
    return CpqRuleSetResponse(
        id=rule_set.id,
        rule_code=rule_set.rule_code,
        rule_name=rule_set.rule_name,
        description=rule_set.description,
        status=rule_set.status,
        base_price=rule_set.base_price or Decimal("0"),
        currency=rule_set.currency or "CNY",
        config_schema=rule_set.config_schema,
        pricing_matrix=rule_set.pricing_matrix,
        approval_threshold=rule_set.approval_threshold,
        visibility_scope=rule_set.visibility_scope or "ALL",
        is_default=rule_set.is_default or False,
        owner_role=rule_set.owner_role,
        created_at=rule_set.created_at,
        updated_at=rule_set.updated_at,
    )
