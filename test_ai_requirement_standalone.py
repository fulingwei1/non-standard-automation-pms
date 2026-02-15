"""
AI需求理解模块独立测试脚本
验证核心功能是否正常工作
"""
import sys
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# 测试AI分析器
async def test_analyzer():
    """测试AI分析器基本功能"""
    from app.services.presale_ai_requirement_service import AIRequirementAnalyzer
    
    analyzer = AIRequirementAnalyzer(api_key="test_key")
    
    print("✓ AIRequirementAnalyzer 初始化成功")
    
    # 测试置信度计算
    sample_result = {
        'structured_requirement': {
            'project_type': '自动化',
            'core_objectives': ['目标1', '目标2'],
            'functional_requirements': ['需求1', '需求2']
        },
        'equipment_list': [{'name': '设备1'}],
        'technical_parameters': [{'name': '参数1'}],
        'process_flow': [{'step': 1}]
    }
    
    score = analyzer._calculate_confidence_score("测试需求描述，包含多个关键信息", sample_result)
    assert 0.0 <= score <= 1.0, f"置信度评分异常: {score}"
    print(f"✓ 置信度计算功能正常: {score}")
    
    # 测试JSON提取
    json_text = '```json\n{"key": "value"}\n```'
    result = analyzer._extract_json_from_response(json_text)
    assert result == {"key": "value"}
    print("✓ JSON提取功能正常")
    
    # 测试降级规则分析
    fallback_result = analyzer._fallback_rule_based_analysis("需要机器人和传送带")
    assert 'structured_requirement' in fallback_result
    assert 'confidence_score' in fallback_result
    print(f"✓ 降级规则引擎正常: 置信度={fallback_result.get('confidence_score')}")
    
    # 测试默认问题生成
    default_questions = analyzer._fallback_generate_questions("测试需求")
    assert len(default_questions) >= 5
    print(f"✓ 默认问题生成正常: {len(default_questions)}个问题")
    
    return True


def test_schemas():
    """测试Schema定义"""
    from app.schemas.presale_ai_requirement import (
        EquipmentItem,
        ProcessStep,
        TechnicalParameter,
        ClarificationQuestion,
        StructuredRequirement
    )
    
    # 测试设备项
    eq = EquipmentItem(
        name="工业机器人",
        type="六轴机器人",
        quantity=2,
        priority="high"
    )
    assert eq.quantity == 2
    print("✓ EquipmentItem Schema 验证正常")
    
    # 测试工艺步骤
    step = ProcessStep(
        step_number=1,
        name="上料",
        description="自动上料"
    )
    assert step.step_number == 1
    print("✓ ProcessStep Schema 验证正常")
    
    # 测试技术参数
    param = TechnicalParameter(
        parameter_name="精度",
        value="±0.05mm",
        unit="mm",
        is_critical=True
    )
    assert param.is_critical is True
    print("✓ TechnicalParameter Schema 验证正常")
    
    # 测试澄清问题
    question = ClarificationQuestion(
        question_id=1,
        category="技术参数",
        question="请明确设备参数",
        importance="critical"
    )
    assert question.importance == "critical"
    print("✓ ClarificationQuestion Schema 验证正常")
    
    # 测试结构化需求
    sr = StructuredRequirement(
        project_type="自动化",
        core_objectives=["目标1"],
        functional_requirements=["功能1"],
        non_functional_requirements=["性能1"]
    )
    assert sr.project_type == "自动化"
    print("✓ StructuredRequirement Schema 验证正常")
    
    return True


def test_model():
    """测试数据库模型定义"""
    from app.models.presale_ai_requirement_analysis import PresaleAIRequirementAnalysis
    
    # 测试模型创建
    model = PresaleAIRequirementAnalysis(
        presale_ticket_id=1,
        raw_requirement="测试需求",
        confidence_score=0.85
    )
    
    assert model.presale_ticket_id == 1
    assert model.confidence_score == 0.85
    print("✓ PresaleAIRequirementAnalysis Model 定义正常")
    
    return True


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("AI智能需求理解引擎 - 独立功能测试")
    print("=" * 60)
    print()
    
    try:
        print("[1/3] 测试Schema定义...")
        test_schemas()
        print()
        
        print("[2/3] 测试数据库模型...")
        test_model()
        print()
        
        print("[3/3] 测试AI分析器...")
        await test_analyzer()
        print()
        
        print("=" * 60)
        print("✅ 所有核心功能测试通过！")
        print("=" * 60)
        print()
        print("总结:")
        print("  - Schema验证: 5/5 通过")
        print("  - 数据库模型: 1/1 通过")
        print("  - AI分析器: 4/4 通过")
        print()
        print("下一步:")
        print("  1. 运行数据库迁移: alembic upgrade head")
        print("  2. 配置OpenAI API Key")
        print("  3. 运行完整单元测试: pytest tests/test_presale_ai_requirement.py")
        print("  4. 启动服务并测试API端点")
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 测试失败: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
