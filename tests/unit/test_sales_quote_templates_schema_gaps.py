from app.schemas.sales.quote_templates import (
    CpqRuleSetResponse,
    QuoteTemplateBase,
    QuoteTemplateResponse,
    QuoteTemplateVersionResponse,
    TemplateApprovalHistoryRecord,
)


def test_cpq_rule_set_response_normalizes_none_status():
    schema = CpqRuleSetResponse(id=1, rule_code="R001", rule_name="标准规则", status=None)

    assert schema.status == "ACTIVE"


def test_quote_template_version_response_normalizes_none_status():
    schema = QuoteTemplateVersionResponse(id=1, template_id=1, version_no="v1", status=None)

    assert schema.status == "DRAFT"


def test_quote_template_base_normalizes_none_fields():
    schema = QuoteTemplateBase(template_code="QT-001", template_name="标准模板", visibility_scope=None, is_default=None)

    assert schema.visibility_scope == "TEAM"
    assert schema.is_default is False


def test_quote_template_response_and_history_normalize_none_status():
    response = QuoteTemplateResponse(id=1, template_code="QT-001", template_name="标准模板", status=None)
    history = TemplateApprovalHistoryRecord(version_id=1, version_no="v1", status=None)

    assert response.status == "DRAFT"
    assert history.status == "DRAFT"
