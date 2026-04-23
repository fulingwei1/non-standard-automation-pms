from app.schemas.sales.assessments import OpenItemResponse, ScoringRuleResponse


def test_scoring_rule_response_normalizes_none_is_active():
    schema = ScoringRuleResponse(id=1, version="v1", is_active=None)

    assert schema.is_active is True


def test_open_item_response_normalizes_none_fields():
    schema = OpenItemResponse(
        id=1,
        source_type="QUOTE",
        source_id=1,
        item_code="OI-001",
        item_type="TECH",
        description="待确认接口",
        responsible_party="客户",
        status=None,
        blocks_quotation=None,
    )

    assert schema.status == "OPEN"
    assert schema.blocks_quotation is False
