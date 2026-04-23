import pytest

from app.schemas.sales.leads import LeadFollowUpCreate


def test_lead_follow_up_create_requires_content_or_action_summary():
    with pytest.raises(ValueError, match="content/action_summary 至少提供一个"):
        LeadFollowUpCreate(follow_up_type="CALL")
