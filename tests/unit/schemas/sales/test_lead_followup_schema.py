# -*- coding: utf-8 -*-
"""Lead follow-up schema compatibility tests."""

import pytest
from pydantic import ValidationError

from app.schemas.sales.leads import LeadFollowUpCreate, LeadFollowUpResponse


def test_follow_up_create_accepts_new_fields():
    model = LeadFollowUpCreate(
        follow_up_type="CALL",
        content="已电话联系客户",
        next_action="发送方案",
    )

    assert model.follow_up_type == "CALL"
    assert model.content == "已电话联系客户"


def test_follow_up_create_accepts_legacy_fields_and_normalizes():
    model = LeadFollowUpCreate(
        action_type="EMAIL",
        action_summary="已邮件跟进",
    )

    assert model.follow_up_type == "EMAIL"
    assert model.content == "已邮件跟进"


def test_follow_up_create_requires_type_and_content():
    with pytest.raises(ValidationError):
        LeadFollowUpCreate(next_action="等待客户反馈")


def test_follow_up_response_fills_compat_alias_fields():
    model = LeadFollowUpResponse(
        id=1,
        lead_id=2,
        follow_up_type="VISIT",
        content="已现场拜访",
        creator_name="张三",
    )

    assert model.action_type == "VISIT"
    assert model.action_summary == "已现场拜访"
    assert model.created_by_name == "张三"
