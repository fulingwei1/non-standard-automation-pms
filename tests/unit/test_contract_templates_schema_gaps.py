from app.schemas.sales.contract_templates import (
    ContractTemplateBase,
    ContractTemplateResponse,
    ContractTemplateVersionResponse,
    VersionHistoryItem,
)


def test_contract_template_version_response_normalizes_none_status():
    schema = ContractTemplateVersionResponse(
        id=1,
        template_id=2,
        version_no="v1",
        status=None,
    )

    assert schema.status == "DRAFT"


def test_contract_template_base_normalizes_none_visibility_and_default_flag():
    schema = ContractTemplateBase(
        template_code="CT-001",
        template_name="标准合同模板",
        visibility_scope=None,
        is_default=None,
    )

    assert schema.visibility_scope == "TEAM"
    assert schema.is_default is False


def test_contract_template_response_normalizes_none_status():
    schema = ContractTemplateResponse(
        id=1,
        template_code="CT-001",
        template_name="标准合同模板",
        status=None,
    )

    assert schema.status == "DRAFT"


def test_version_history_item_normalizes_none_status():
    schema = VersionHistoryItem(version_id=1, version_no="v1", status=None)

    assert schema.status == "DRAFT"
