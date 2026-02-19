# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/pm_involvement_service.py
"""
import pytest

pytest.importorskip("app.services.pm_involvement_service")

from app.services.pm_involvement_service import PMInvolvementService


# ── 1. 高风险项目：≥2个风险因素，建议提前介入 ──────────────────────────────────
def test_high_risk_project_early_involvement():
    data = {
        "项目金额": 150,       # >=100万 → +1
        "是否首次做": True,    # +1
        "失败项目数": 1,       # +1
        "历史相似项目数": 2,   # <3 → +1
        "是否有标准方案": False,  # +1
        "技术创新点": ["算法A"]   # +1
    }
    result = PMInvolvementService.judge_pm_involvement_timing(data)
    assert result["建议"] == "PM提前介入"
    assert result["风险等级"] == "高"
    assert result["需要PM审核"] is True
    assert result["风险因素数"] >= 2


# ── 2. 低风险项目：<2个风险因素，签约后介入 ──────────────────────────────────
def test_low_risk_project_post_signing():
    data = {
        "项目金额": 50,
        "是否首次做": False,
        "失败项目数": 0,
        "历史相似项目数": 5,
        "是否有标准方案": True,
        "技术创新点": []
    }
    result = PMInvolvementService.judge_pm_involvement_timing(data)
    assert result["建议"] == "PM签约后介入"
    assert result["风险等级"] == "低"
    assert result["需要PM审核"] is False


# ── 3. 大项目金额触发一个风险因素 ────────────────────────────────────────────
def test_large_project_amount_triggers_factor():
    data = {
        "项目金额": 200,
        "是否首次做": False,
        "失败项目数": 0,
        "历史相似项目数": 10,
        "是否有标准方案": True,
        "技术创新点": []
    }
    result = PMInvolvementService.judge_pm_involvement_timing(data)
    # Only 1 factor: amount; below threshold
    assert result["风险因素数"] == 1
    assert result["建议"] == "PM签约后介入"


# ── 4. 阈值边界：恰好2个风险因素时应提前介入 ─────────────────────────────────
def test_exactly_two_risk_factors():
    data = {
        "项目金额": 100,       # >=100 → +1
        "是否首次做": True,    # +1
        "失败项目数": 0,
        "历史相似项目数": 5,
        "是否有标准方案": True,
        "技术创新点": []
    }
    result = PMInvolvementService.judge_pm_involvement_timing(data)
    assert result["风险因素数"] == 2
    assert result["建议"] == "PM提前介入"


# ── 5. 紧急程度：≥4个因素时为"高" ─────────────────────────────────────────
def test_urgency_high_when_many_factors():
    data = {
        "项目金额": 200,       # +1
        "是否首次做": True,    # +1
        "失败项目数": 2,       # +1
        "历史相似项目数": 0,   # +1
        "是否有标准方案": False,  # +1
        "技术创新点": ["A", "B"]  # +1
    }
    result = PMInvolvementService.judge_pm_involvement_timing(data)
    assert result["紧急程度"] == "高"


# ── 6. get_similar_project_count 返回正确结构 ─────────────────────────────────
def test_get_similar_project_count():
    result = PMInvolvementService.get_similar_project_count("SMT", "汽车电子")
    assert "总数" in result
    assert "成功率" in result
    assert result["成功率"] == 0.0


# ── 7. check_has_standard_solution 返回 bool ─────────────────────────────────
def test_check_has_standard_solution():
    result = PMInvolvementService.check_has_standard_solution("视觉检测系统")
    assert isinstance(result, bool)


# ── 8. generate_notification_message: 高风险项目生成含⚠️的消息 ───────────────
def test_generate_notification_high_risk():
    result = {
        "需要PM审核": True,
        "风险因素数": 4,
        "原因": ["大项目", "首次做"],
        "下一步行动": ["1. 安排PM"],
        "紧急程度": "高"
    }
    ticket = {"项目名称": "测试项目", "客户名称": "客户A", "预估金额": 150}
    msg = PMInvolvementService.generate_notification_message(result, ticket)
    assert "⚠️" in msg
    assert "测试项目" in msg
    assert "高风险" in msg


# ── 9. generate_notification_message: 低风险项目生成含✅的消息 ───────────────
def test_generate_notification_low_risk():
    result = {
        "需要PM审核": False,
        "风险因素数": 0,
        "原因": ["成熟项目"],
        "下一步行动": ["1. 正常推进"],
        "风险等级": "低"
    }
    ticket = {"项目名称": "标准项目", "客户名称": "客户B", "预估金额": 50}
    msg = PMInvolvementService.generate_notification_message(result, ticket)
    assert "✅" in msg
    assert "标准项目" in msg
