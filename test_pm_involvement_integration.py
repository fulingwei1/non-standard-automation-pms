#!/usr/bin/env python3
"""
PM介入策略集成测试脚本

测试售前工单创建时的PM介入判断功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from app.services.pm_involvement_service import PMInvolvementService


def test_high_risk_project():
    """测试高风险项目判断"""
    print("=" * 60)
    print("测试1: 高风险项目（应该需要PM提前介入）")
    print("=" * 60)
    
    project_data = {
        "项目金额": 150,
        "项目类型": "SMT贴片生产线",
        "行业": "汽车电子",
        "是否首次做": False,
        "历史相似项目数": 2,
        "失败项目数": 1,
        "是否有标准方案": False,
        "技术创新点": ["视觉检测新算法", "多工位协同"]
    }
    
    result = PMInvolvementService.judge_pm_involvement_timing(project_data)
    
    print(f"建议: {result['建议']}")
    print(f"介入阶段: {result['介入阶段']}")
    print(f"风险等级: {result['风险等级']}")
    print(f"风险因素数: {result['风险因素数']}")
    print(f"需要PM审核: {result['需要PM审核']}")
    print(f"紧急程度: {result['紧急程度']}")
    print(f"\n风险因素:")
    for i, reason in enumerate(result['原因'], 1):
        print(f"  {i}. {reason}")
    print(f"\n下一步行动:")
    for i, action in enumerate(result['下一步行动'], 1):
        print(f"  {action}")
    
    assert result['需要PM审核'] == True, "高风险项目应该需要PM审核"
    assert result['风险等级'] == '高', "风险等级应该为'高'"
    assert result['风险因素数'] >= 2, "风险因素数应该≥2"
    
    print("\n✅ 测试1通过")
    return result


def test_low_risk_project():
    """测试低风险项目判断"""
    print("\n" + "=" * 60)
    print("测试2: 低风险项目（不需要PM提前介入）")
    print("=" * 60)
    
    project_data = {
        "项目金额": 50,
        "项目类型": "视觉检测系统",
        "行业": "消费电子",
        "是否首次做": False,
        "历史相似项目数": 5,
        "失败项目数": 0,
        "是否有标准方案": True,
        "技术创新点": []
    }
    
    result = PMInvolvementService.judge_pm_involvement_timing(project_data)
    
    print(f"建议: {result['建议']}")
    print(f"介入阶段: {result['介入阶段']}")
    print(f"风险等级: {result['风险等级']}")
    print(f"风险因素数: {result['风险因素数']}")
    print(f"需要PM审核: {result['需要PM审核']}")
    print(f"\n原因:")
    for i, reason in enumerate(result['原因'], 1):
        print(f"  {i}. {reason}")
    
    assert result['需要PM审核'] == False, "低风险项目不应该需要PM审核"
    assert result['风险等级'] == '低', "风险等级应该为'低'"
    assert result['风险因素数'] < 2, "风险因素数应该<2"
    
    print("\n✅ 测试2通过")
    return result


def test_notification_message():
    """测试通知消息生成"""
    print("\n" + "=" * 60)
    print("测试3: 通知消息生成")
    print("=" * 60)
    
    pm_result = {
        "建议": "PM提前介入",
        "介入阶段": "技术评审/需求调研阶段",
        "风险等级": "高",
        "风险因素数": 5,
        "原因": [
            "大型项目（150万）",
            "相似项目有失败经验（1次）",
            "相似项目经验不足（仅2个）",
            "无标准化方案模板",
            "涉及技术创新（2项）"
        ],
        "下一步行动": [
            "1. 立即通知PMO负责人安排PM",
            "2. 组织技术评审会（邀请PM参加）",
            "3. PM参与客户需求调研",
            "4. PM审核成本和工期估算"
        ],
        "需要PM审核": True,
        "紧急程度": "高"
    }
    
    ticket_info = {
        "项目名称": "SMT贴片生产线自动化改造",
        "客户名称": "某汽车电子公司",
        "预估金额": 150
    }
    
    message = PMInvolvementService.generate_notification_message(pm_result, ticket_info)
    
    print("生成的通知消息:")
    print("-" * 60)
    print(message)
    print("-" * 60)
    
    assert "需PM提前介入" in message, "通知消息应包含'需PM提前介入'"
    assert "150万" in message, "通知消息应包含金额"
    assert "某汽车电子公司" in message, "通知消息应包含客户名称"
    assert "紧急程度：高" in message, "通知消息应包含紧急程度"
    
    print("\n✅ 测试3通过")
    return message


def test_boundary_case():
    """测试边界情况（正好2个风险因素）"""
    print("\n" + "=" * 60)
    print("测试4: 边界情况（正好2个风险因素）")
    print("=" * 60)
    
    project_data = {
        "项目金额": 100,  # 正好100万
        "项目类型": "测试系统",
        "行业": "电子",
        "是否首次做": False,
        "历史相似项目数": 2,  # 正好2个（不足3个）
        "失败项目数": 0,
        "是否有标准方案": True,
        "技术创新点": []
    }
    
    result = PMInvolvementService.judge_pm_involvement_timing(project_data)
    
    print(f"建议: {result['建议']}")
    print(f"风险因素数: {result['风险因素数']}")
    print(f"需要PM审核: {result['需要PM审核']}")
    print(f"\n风险因素:")
    for i, reason in enumerate(result['原因'], 1):
        print(f"  {i}. {reason}")
    
    # 边界情况：≥2个风险因素就需要PM介入
    assert result['需要PM审核'] == True, "边界情况（2个风险因素）应该需要PM审核"
    assert result['风险因素数'] == 2, "风险因素数应该为2"
    
    print("\n✅ 测试4通过")
    return result


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("PM介入策略集成测试")
    print("=" * 60 + "\n")
    
    try:
        # 运行测试
        test_high_risk_project()
        test_low_risk_project()
        test_notification_message()
        test_boundary_case()
        
        # 总结
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！PM介入策略集成正常工作！")
        print("=" * 60)
        print("\n下一步:")
        print("1. 运行数据库迁移: alembic upgrade head")
        print("2. 重启应用服务")
        print("3. 测试API端点: POST /api/v1/presale/tickets")
        print("4. 前端集成（参考 PM介入策略-售前集成文档.md）")
        print()
        
        return 0
    
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
