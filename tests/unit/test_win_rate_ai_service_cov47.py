# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - win_rate_prediction_service/ai_service.py
"""
import pytest

pytest.importorskip("app.services.win_rate_prediction_service.ai_service")

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.win_rate_prediction_service.ai_service import AIWinRatePredictionService


# ---------- 辅助函数 ----------

def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def make_service(**env):
    with patch.dict("os.environ", env):
        return AIWinRatePredictionService()


# ---------- 测试 ----------

def test_fallback_prediction_repeat_customer():
    svc = AIWinRatePredictionService()
    result = svc._fallback_prediction({"is_repeat_customer": True, "competitor_count": 2})
    assert result["win_rate_score"] > 50
    assert "influencing_factors" in result
    assert "improvement_suggestions" in result


def test_fallback_prediction_many_competitors():
    svc = AIWinRatePredictionService()
    result = svc._fallback_prediction({"is_repeat_customer": False, "competitor_count": 6})
    assert result["win_rate_score"] < 50


def test_fallback_prediction_score_bounds():
    svc = AIWinRatePredictionService()
    result = svc._fallback_prediction({"salesperson_win_rate": 0.0, "competitor_count": 10})
    assert 0.0 <= result["win_rate_score"] <= 100.0


def test_build_prediction_prompt_contains_ticket_info():
    svc = AIWinRatePredictionService()
    ticket = {"ticket_no": "T001", "customer_name": "ACME", "estimated_amount": 100000}
    prompt = svc._build_prediction_prompt(ticket)
    assert "T001" in prompt
    assert "ACME" in prompt


def test_parse_ai_response_valid_json():
    svc = AIWinRatePredictionService()
    data = {
        "win_rate_score": 72,
        "confidence_interval": "68-76%",
        "influencing_factors": [],
        "competitor_analysis": {},
        "improvement_suggestions": {},
        "analysis_summary": "看起来不错"
    }
    ai_text = f"分析结果如下：\n{json.dumps(data)}"
    result = svc._parse_ai_response(ai_text, {})
    assert result["win_rate_score"] == 72.0
    assert result["confidence_interval"] == "68-76%"


def test_parse_ai_response_no_json_uses_fallback():
    svc = AIWinRatePredictionService()
    result = svc._parse_ai_response("没有JSON内容", {"is_repeat_customer": True})
    assert "win_rate_score" in result


def test_predict_with_ai_no_keys_uses_fallback():
    svc = AIWinRatePredictionService()
    # 没有配置任何API Key时走 fallback
    result = run(svc.predict_with_ai({"is_repeat_customer": False}))
    assert "win_rate_score" in result


def test_predict_with_ai_openai_error_falls_back():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "fake-key"}):
        svc = AIWinRatePredictionService()
    with patch.object(svc, "_predict_with_openai", side_effect=Exception("api error")):
        result = run(svc.predict_with_ai({"is_repeat_customer": True}))
    assert "win_rate_score" in result
