import pytest
from pydantic import ValidationError

from app.schemas.presale_ai_emotion import BatchAnalysisRequest, EmotionAnalysisRequest


def test_emotion_analysis_request_strips_content():
    req = EmotionAnalysisRequest(
        presale_ticket_id=1,
        customer_id=2,
        communication_content="  客户反馈还不错  ",
    )

    assert req.communication_content == "客户反馈还不错"


def test_emotion_analysis_request_rejects_blank_content():
    with pytest.raises(ValidationError, match="沟通内容不能为空"):
        EmotionAnalysisRequest(
            presale_ticket_id=1,
            customer_id=2,
            communication_content="   ",
        )


def test_batch_analysis_request_accepts_allowed_type():
    req = BatchAnalysisRequest(customer_ids=[1, 2], analysis_type="emotion")

    assert req.analysis_type == "emotion"


def test_batch_analysis_request_rejects_invalid_type():
    with pytest.raises(ValidationError, match="分析类型必须是: full, emotion, churn"):
        BatchAnalysisRequest(customer_ids=[1], analysis_type="other")
