#!/usr/bin/env python3
"""
GLM-5 集成测试脚本

测试项目:
1. zai-sdk 导入测试
2. Mock 模式测试（无API Key）
3. 真实API测试（需要配置 ZHIPU_API_KEY）
4. 思考模式测试
5. 性能对比测试（GLM-5 vs Kimi vs GPT-4）
"""

import os
import sys
import time
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_client_service import AIClientService


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_test_header(title: str):
    """打印测试标题"""
    print(f"\n{'='*60}")
    print(f"{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{'='*60}\n")


def print_success(message: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_error(message: str):
    """打印错误消息"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")


def print_warning(message: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def test_sdk_import():
    """测试 zai-sdk 导入"""
    print_test_header("测试 1: zai-sdk 导入测试")
    
    try:
        from zai import ZhipuAiClient
        print_success("zai-sdk 导入成功")
        print(f"   ZhipuAiClient: {ZhipuAiClient}")
        return True
    except ImportError as e:
        print_error(f"zai-sdk 导入失败: {e}")
        print_warning("请运行: pip3 install zai-sdk")
        return False


def test_mock_mode():
    """测试 Mock 模式"""
    print_test_header("测试 2: Mock 模式测试（无API Key）")
    
    # 临时清空API Keys
    original_zhipu = os.environ.get("ZHIPU_API_KEY", "")
    original_openai = os.environ.get("OPENAI_API_KEY", "")
    original_kimi = os.environ.get("KIMI_API_KEY", "")
    
    os.environ["ZHIPU_API_KEY"] = ""
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["KIMI_API_KEY"] = ""
    
    try:
        client = AIClientService()
        
        # 测试方案生成
        response = client.generate_solution(
            prompt="设计一套汽车零部件装配线",
            model="glm-5"
        )
        
        print(f"模型: {response['model']}")
        print(f"Token使用: {response['usage']['total_tokens']}")
        print(f"内容预览: {response['content'][:100]}...")
        
        if response['model'] == 'glm-5-mock':
            print_success("Mock 模式工作正常")
            return True
        else:
            print_error(f"预期 'glm-5-mock'，实际: {response['model']}")
            return False
            
    except Exception as e:
        print_error(f"Mock 模式测试失败: {e}")
        return False
    finally:
        # 恢复原始API Keys
        os.environ["ZHIPU_API_KEY"] = original_zhipu
        os.environ["OPENAI_API_KEY"] = original_openai
        os.environ["KIMI_API_KEY"] = original_kimi


def test_real_api():
    """测试真实 API 调用"""
    print_test_header("测试 3: 真实 GLM-5 API 测试")
    
    zhipu_key = os.environ.get("ZHIPU_API_KEY", "")
    
    if not zhipu_key or zhipu_key == "your_zhipu_api_key_here":
        print_warning("未配置 ZHIPU_API_KEY，跳过真实API测试")
        print_warning("配置方式: export ZHIPU_API_KEY=your_actual_key")
        return None
    
    try:
        client = AIClientService()
        
        print("正在调用 GLM-5 API...")
        start_time = time.time()
        
        response = client.generate_solution(
            prompt="请用一句话介绍非标自动化行业",
            model="glm-5",
            temperature=0.7,
            max_tokens=100
        )
        
        elapsed = time.time() - start_time
        
        print(f"模型: {response['model']}")
        print(f"响应时间: {elapsed:.2f}秒")
        print(f"Token使用: {response['usage']}")
        print(f"回复内容:\n{response['content']}")
        
        if 'reasoning' in response:
            print(f"\n思考过程:\n{response['reasoning']}")
        
        print_success(f"GLM-5 API 调用成功 (耗时 {elapsed:.2f}s)")
        return True
        
    except Exception as e:
        print_error(f"GLM-5 API 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_thinking_mode():
    """测试思考模式"""
    print_test_header("测试 4: 思考模式测试")
    
    zhipu_key = os.environ.get("ZHIPU_API_KEY", "")
    
    if not zhipu_key or zhipu_key == "your_zhipu_api_key_here":
        print_warning("未配置 ZHIPU_API_KEY，跳过思考模式测试")
        return None
    
    try:
        client = AIClientService()
        
        # 复杂任务应该自动启用思考模式
        complex_prompt = """
        设计一套智能化汽车零部件装配线，要求：
        1. 生产节拍: 60秒/件
        2. 自动化程度: 95%以上
        3. 包含视觉检测和机器人装配
        4. 需要考虑成本优化
        """
        
        print("正在调用 GLM-5（复杂任务，应启用思考模式）...")
        start_time = time.time()
        
        response = client.generate_solution(
            prompt=complex_prompt,
            model="glm-5",
            temperature=0.7,
            max_tokens=500
        )
        
        elapsed = time.time() - start_time
        
        print(f"响应时间: {elapsed:.2f}秒")
        print(f"Token使用: {response['usage']}")
        
        if 'reasoning' in response:
            print_success("✨ 思考模式已启用")
            print(f"思考过程长度: {len(response['reasoning'])} 字符")
        else:
            print_warning("思考模式未启用（可能是简单任务）")
        
        print(f"\n方案内容:\n{response['content'][:200]}...")
        
        return True
        
    except Exception as e:
        print_error(f"思考模式测试失败: {e}")
        return False


def test_model_comparison():
    """测试多模型对比"""
    print_test_header("测试 5: 模型性能对比")
    
    models = []
    
    # 检查可用模型
    if os.environ.get("ZHIPU_API_KEY", "") and os.environ.get("ZHIPU_API_KEY") != "your_zhipu_api_key_here":
        models.append("glm-5")
    if os.environ.get("OPENAI_API_KEY", ""):
        models.append("gpt-4")
    if os.environ.get("KIMI_API_KEY", ""):
        models.append("kimi")
    
    if not models:
        print_warning("未配置任何 API Key，跳过模型对比测试")
        return None
    
    print(f"可用模型: {', '.join(models)}\n")
    
    test_prompt = "请用一句话介绍非标自动化行业的核心价值"
    
    results = {}
    
    for model in models:
        try:
            client = AIClientService()
            
            print(f"测试 {model}...")
            start_time = time.time()
            
            response = client.generate_solution(
                prompt=test_prompt,
                model=model,
                temperature=0.7,
                max_tokens=100
            )
            
            elapsed = time.time() - start_time
            
            results[model] = {
                "time": elapsed,
                "tokens": response['usage']['total_tokens'],
                "content": response['content']
            }
            
            print(f"  ⏱️  响应时间: {elapsed:.2f}秒")
            print(f"  📊 Token使用: {response['usage']['total_tokens']}")
            print()
            
        except Exception as e:
            print_error(f"  {model} 测试失败: {e}")
    
    # 打印对比结果
    if results:
        print("\n" + "="*60)
        print("性能对比总结:")
        print("="*60)
        
        for model, result in results.items():
            print(f"\n{model}:")
            print(f"  响应时间: {result['time']:.2f}秒")
            print(f"  Token使用: {result['tokens']}")
            print(f"  回复: {result['content'][:80]}...")
        
        # 找出最快的模型
        fastest = min(results.items(), key=lambda x: x[1]['time'])
        print(f"\n🏆 最快模型: {fastest[0]} ({fastest[1]['time']:.2f}秒)")
        
        return True
    
    return False


def main():
    """主测试流程"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("GLM-5 集成测试")
    print(f"{'='*60}{Colors.RESET}\n")
    
    results = {
        "SDK导入": test_sdk_import(),
        "Mock模式": test_mock_mode(),
        "真实API": test_real_api(),
        "思考模式": test_thinking_mode(),
        "模型对比": test_model_comparison()
    }
    
    # 打印测试总结
    print(f"\n{Colors.BLUE}{'='*60}")
    print("测试总结")
    print(f"{'='*60}{Colors.RESET}\n")
    
    for test_name, result in results.items():
        if result is True:
            print_success(f"{test_name}: 通过")
        elif result is False:
            print_error(f"{test_name}: 失败")
        else:
            print_warning(f"{test_name}: 跳过")
    
    # 统计
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过")
    
    # 返回状态码
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
