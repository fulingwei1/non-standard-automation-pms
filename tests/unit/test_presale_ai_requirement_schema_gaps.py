import pytest

from app.schemas.presale_ai_requirement import RequirementAnalysisRequest


def test_requirement_analysis_request_strips_content():
    req = RequirementAnalysisRequest(
        presale_ticket_id=1,
        raw_requirement="   需要一套自动化测试线方案   ",
    )

    assert req.raw_requirement == "需要一套自动化测试线方案"


def test_requirement_analysis_request_rejects_too_short_trimmed_content():
    with pytest.raises(ValueError, match="需求描述至少10个字符"):
        RequirementAnalysisRequest.validate_requirement_content("   太短了  ")
