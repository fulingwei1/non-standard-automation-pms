#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kimi API 连接测试脚本
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from app.services.ai_service import AIService, chat_with_ai, analyze_project_with_ai


async def test_basic_connection():
    """测试基本连接"""
    print("=== 测试基本连接 ===")
    
    try:
        ai_service = AIService()
        
        if not ai_service.enabled:
            print("❌ AI 服务未启用")
            return False
            
        print("✅ AI 服务已启用")
        print(f"   模型: {ai_service.model}")
        print(f"   基础URL: {ai_service.base_url}")
        
        # 测试简单对话
        response = await ai_service.simple_chat("你好，请回复'连接成功'")
        print(f"   响应: {response}")
        
        await ai_service.close()
        return True
        
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False


async def test_chat_function():
    """测试聊天功能"""
    print("\n=== 测试聊天功能 ===")
    
    try:
        response = await chat_with_ai(
            "请用一句话介绍非标自动化项目管理的关键点",
            context="你是一个专业的项目管理专家"
        )
        print(f"✅ 聊天响应: {response}")
        return True
        
    except Exception as e:
        print(f"❌ 聊天测试失败: {e}")
        return False


async def test_project_analysis():
    """测试项目分析功能"""
    print("\n=== 测试项目分析功能 ===")
    
    try:
        project_data = {
            "project_code": "PJ250708001",
            "name": "ICT测试设备项目",
            "customer": "ABC科技有限公司",
            "budget": 500000,
            "start_date": "2025-07-08",
            "end_date": "2025-12-31",
            "stage": "S3",
            "description": "包括功能测试、耐压测试、视觉检测等多个工位的自动化测试设备"
        }
        
        analysis = await analyze_project_with_ai(project_data)
        print("✅ 项目分析结果:")
        print(json.dumps(analysis, ensure_ascii=False, indent=2))
        return True
        
    except Exception as e:
        print(f"❌ 项目分析测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("Kimi API 连接测试开始...")
    print("=" * 50)
    
    tests = [
        ("基本连接", test_basic_connection),
        ("聊天功能", test_chat_function),
        ("项目分析", test_project_analysis)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Kimi API 配置成功！")
        sys.exit(0)
    else:
        print("⚠️ 部分测试失败，请检查配置")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())