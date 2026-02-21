# -*- coding: utf-8 -*-
"""
风险计算工具全面测试

测试 app/utils/risk_calculator.py 中的所有函数和类
"""
import pytest
from app.utils.risk_calculator import (
    calculate_risk_level,
    get_risk_score,
    compare_risk_levels,
    RiskCalculator,
)


class TestCalculateRiskLevel:
    """测试风险等级计算函数"""

    def test_critical_risk(self):
        """HIGH + HIGH = CRITICAL"""
        assert calculate_risk_level("HIGH", "HIGH") == "CRITICAL"
    
    def test_high_risk_high_probability(self):
        """HIGH + MEDIUM = HIGH"""
        assert calculate_risk_level("HIGH", "MEDIUM") == "HIGH"
    
    def test_high_risk_high_impact(self):
        """MEDIUM + HIGH = HIGH"""
        assert calculate_risk_level("MEDIUM", "HIGH") == "HIGH"
    
    def test_high_risk_high_probability_low_impact(self):
        """HIGH + LOW = HIGH"""
        assert calculate_risk_level("HIGH", "LOW") == "HIGH"
    
    def test_high_risk_low_probability_high_impact(self):
        """LOW + HIGH = HIGH"""
        assert calculate_risk_level("LOW", "HIGH") == "HIGH"
    
    def test_medium_risk_medium_probability(self):
        """MEDIUM + MEDIUM = MEDIUM"""
        assert calculate_risk_level("MEDIUM", "MEDIUM") == "MEDIUM"
    
    def test_medium_risk_medium_probability_low_impact(self):
        """MEDIUM + LOW = MEDIUM"""
        assert calculate_risk_level("MEDIUM", "LOW") == "MEDIUM"
    
    def test_medium_risk_low_probability_medium_impact(self):
        """LOW + MEDIUM = MEDIUM"""
        assert calculate_risk_level("LOW", "MEDIUM") == "MEDIUM"
    
    def test_low_risk(self):
        """LOW + LOW = LOW"""
        assert calculate_risk_level("LOW", "LOW") == "LOW"
    
    def test_case_insensitive(self):
        """大小写不敏感"""
        assert calculate_risk_level("high", "high") == "CRITICAL"
        assert calculate_risk_level("HiGh", "HiGh") == "CRITICAL"
        assert calculate_risk_level("low", "low") == "LOW"
    
    def test_none_probability_returns_none(self):
        """概率为None返回None"""
        assert calculate_risk_level(None, "HIGH") is None
    
    def test_none_impact_returns_none(self):
        """影响为None返回None"""
        assert calculate_risk_level("HIGH", None) is None
    
    def test_both_none_returns_none(self):
        """两者都为None返回None"""
        assert calculate_risk_level(None, None) is None
    
    def test_empty_string_probability(self):
        """空字符串概率"""
        assert calculate_risk_level("", "HIGH") is None
    
    def test_empty_string_impact(self):
        """空字符串影响"""
        assert calculate_risk_level("HIGH", "") is None
    
    def test_all_combinations(self):
        """测试所有组合"""
        # 风险矩阵
        expected = {
            ("HIGH", "HIGH"): "CRITICAL",
            ("HIGH", "MEDIUM"): "HIGH",
            ("HIGH", "LOW"): "HIGH",
            ("MEDIUM", "HIGH"): "HIGH",
            ("MEDIUM", "MEDIUM"): "MEDIUM",
            ("MEDIUM", "LOW"): "MEDIUM",
            ("LOW", "HIGH"): "HIGH",
            ("LOW", "MEDIUM"): "MEDIUM",
            ("LOW", "LOW"): "LOW",
        }
        
        for (prob, impact), expected_level in expected.items():
            assert calculate_risk_level(prob, impact) == expected_level, \
                f"Failed for ({prob}, {impact})"


class TestGetRiskScore:
    """测试风险分数转换函数"""

    def test_critical_score(self):
        """CRITICAL = 4"""
        assert get_risk_score("CRITICAL") == 4
    
    def test_high_score(self):
        """HIGH = 3"""
        assert get_risk_score("HIGH") == 3
    
    def test_medium_score(self):
        """MEDIUM = 2"""
        assert get_risk_score("MEDIUM") == 2
    
    def test_low_score(self):
        """LOW = 1"""
        assert get_risk_score("LOW") == 1
    
    def test_case_insensitive(self):
        """大小写不敏感"""
        assert get_risk_score("critical") == 4
        assert get_risk_score("CrItIcAl") == 4
    
    def test_unknown_level_returns_zero(self):
        """未知等级返回0"""
        assert get_risk_score("UNKNOWN") == 0
        assert get_risk_score("INVALID") == 0
        assert get_risk_score("") == 0
    
    def test_ordering(self):
        """验证分数顺序"""
        assert get_risk_score("LOW") < get_risk_score("MEDIUM")
        assert get_risk_score("MEDIUM") < get_risk_score("HIGH")
        assert get_risk_score("HIGH") < get_risk_score("CRITICAL")


class TestCompareRiskLevels:
    """测试风险等级比较函数"""

    def test_upgrade_low_to_medium(self):
        """LOW -> MEDIUM = UPGRADE"""
        assert compare_risk_levels("LOW", "MEDIUM") == "UPGRADE"
    
    def test_upgrade_medium_to_high(self):
        """MEDIUM -> HIGH = UPGRADE"""
        assert compare_risk_levels("MEDIUM", "HIGH") == "UPGRADE"
    
    def test_upgrade_high_to_critical(self):
        """HIGH -> CRITICAL = UPGRADE"""
        assert compare_risk_levels("HIGH", "CRITICAL") == "UPGRADE"
    
    def test_upgrade_low_to_critical(self):
        """LOW -> CRITICAL = UPGRADE（跨级）"""
        assert compare_risk_levels("LOW", "CRITICAL") == "UPGRADE"
    
    def test_downgrade_critical_to_high(self):
        """CRITICAL -> HIGH = DOWNGRADE"""
        assert compare_risk_levels("CRITICAL", "HIGH") == "DOWNGRADE"
    
    def test_downgrade_high_to_medium(self):
        """HIGH -> MEDIUM = DOWNGRADE"""
        assert compare_risk_levels("HIGH", "MEDIUM") == "DOWNGRADE"
    
    def test_downgrade_medium_to_low(self):
        """MEDIUM -> LOW = DOWNGRADE"""
        assert compare_risk_levels("MEDIUM", "LOW") == "DOWNGRADE"
    
    def test_downgrade_critical_to_low(self):
        """CRITICAL -> LOW = DOWNGRADE（跨级）"""
        assert compare_risk_levels("CRITICAL", "LOW") == "DOWNGRADE"
    
    def test_unchanged_low(self):
        """LOW -> LOW = UNCHANGED"""
        assert compare_risk_levels("LOW", "LOW") == "UNCHANGED"
    
    def test_unchanged_medium(self):
        """MEDIUM -> MEDIUM = UNCHANGED"""
        assert compare_risk_levels("MEDIUM", "MEDIUM") == "UNCHANGED"
    
    def test_unchanged_high(self):
        """HIGH -> HIGH = UNCHANGED"""
        assert compare_risk_levels("HIGH", "HIGH") == "UNCHANGED"
    
    def test_unchanged_critical(self):
        """CRITICAL -> CRITICAL = UNCHANGED"""
        assert compare_risk_levels("CRITICAL", "CRITICAL") == "UNCHANGED"
    
    def test_case_insensitive(self):
        """大小写不敏感"""
        assert compare_risk_levels("low", "high") == "UPGRADE"
        assert compare_risk_levels("HIGH", "low") == "DOWNGRADE"


class TestRiskCalculatorClass:
    """测试RiskCalculator类（OOP封装）"""

    def test_calculate_risk_level(self):
        """测试类方法：calculate_risk_level"""
        calculator = RiskCalculator()
        assert calculator.calculate_risk_level("HIGH", "HIGH") == "CRITICAL"
        assert calculator.calculate_risk_level("LOW", "LOW") == "LOW"
    
    def test_calculate_risk_level_static(self):
        """测试静态方法调用"""
        assert RiskCalculator.calculate_risk_level("HIGH", "HIGH") == "CRITICAL"
    
    def test_compare_risk_levels(self):
        """测试类方法：compare_risk_levels"""
        calculator = RiskCalculator()
        assert calculator.compare_risk_levels("LOW", "HIGH") == "UPGRADE"
    
    def test_get_risk_score(self):
        """测试类方法：get_risk_score"""
        calculator = RiskCalculator()
        assert calculator.get_risk_score("CRITICAL") == 4
    
    def test_integration_scenario(self):
        """集成测试场景：风险评估流程"""
        calculator = RiskCalculator()
        
        # 初始风险评估
        old_level = calculator.calculate_risk_level("MEDIUM", "MEDIUM")
        assert old_level == "MEDIUM"
        
        # 风险升级
        new_level = calculator.calculate_risk_level("HIGH", "HIGH")
        assert new_level == "CRITICAL"
        
        # 比较变化
        change = calculator.compare_risk_levels(old_level, new_level)
        assert change == "UPGRADE"
        
        # 获取分数用于排序
        score = calculator.get_risk_score(new_level)
        assert score == 4


class TestEdgeCases:
    """边界情况和异常测试"""

    def test_whitespace_handling(self):
        """空白字符处理"""
        # 空白字符会被转换为空字符串，返回None
        assert calculate_risk_level("  ", "HIGH") is None
        assert calculate_risk_level("HIGH", "  ") is None
    
    def test_partial_data(self):
        """部分数据缺失"""
        assert calculate_risk_level("HIGH", None) is None
        assert calculate_risk_level(None, "HIGH") is None
    
    def test_unknown_level_score(self):
        """未知风险等级的分数"""
        assert get_risk_score("ULTRA") == 0
        assert get_risk_score("NONE") == 0
    
    def test_compare_unknown_levels(self):
        """比较未知等级"""
        # 未知等级分数为0，都为0时UNCHANGED
        assert compare_risk_levels("UNKNOWN1", "UNKNOWN2") == "UNCHANGED"


class TestRealWorldScenarios:
    """真实业务场景测试"""

    def test_risk_assessment_workflow(self):
        """风险评估工作流"""
        # 场景：项目风险评估
        
        # 1. 初始评估
        probability = "MEDIUM"
        impact = "HIGH"
        risk_level = calculate_risk_level(probability, impact)
        assert risk_level == "HIGH"
        
        # 2. 获取风险分数用于排序
        score = get_risk_score(risk_level)
        assert score == 3
        
        # 3. 风险缓解后重新评估
        new_probability = "LOW"
        new_impact = "MEDIUM"
        new_risk_level = calculate_risk_level(new_probability, new_impact)
        assert new_risk_level == "MEDIUM"
        
        # 4. 确认风险降低
        change = compare_risk_levels(risk_level, new_risk_level)
        assert change == "DOWNGRADE"
    
    def test_risk_escalation_scenario(self):
        """风险升级场景"""
        # 场景：技术风险升级
        
        # 初始：低概率、低影响
        old_level = calculate_risk_level("LOW", "LOW")
        assert old_level == "LOW"
        
        # 发现问题：高概率、高影响
        new_level = calculate_risk_level("HIGH", "HIGH")
        assert new_level == "CRITICAL"
        
        # 确认需要升级处理
        change = compare_risk_levels(old_level, new_level)
        assert change == "UPGRADE"
        
        # 风险分数差距
        score_diff = get_risk_score(new_level) - get_risk_score(old_level)
        assert score_diff == 3  # 从1跳到4
    
    def test_risk_matrix_validation(self):
        """验证完整的风险矩阵"""
        # 验证3x3风险矩阵的所有9种组合
        levels = ["LOW", "MEDIUM", "HIGH"]
        
        for prob in levels:
            for impact in levels:
                result = calculate_risk_level(prob, impact)
                assert result in ["LOW", "MEDIUM", "HIGH", "CRITICAL"], \
                    f"Invalid result for ({prob}, {impact}): {result}"
    
    def test_sorting_by_risk_score(self):
        """按风险分数排序"""
        risks = [
            {"id": 1, "level": "MEDIUM"},
            {"id": 2, "level": "CRITICAL"},
            {"id": 3, "level": "LOW"},
            {"id": 4, "level": "HIGH"},
        ]
        
        # 按风险分数排序
        sorted_risks = sorted(
            risks,
            key=lambda x: get_risk_score(x["level"]),
            reverse=True
        )
        
        assert [r["id"] for r in sorted_risks] == [2, 4, 1, 3]
        assert [r["level"] for r in sorted_risks] == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
