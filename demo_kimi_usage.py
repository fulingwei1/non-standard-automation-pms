#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kimi API 使用示例和配置验证
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.services.ai_service import AIService


def print_config():
    """打印当前配置信息"""
    print("=== 当前 Kimi AI 配置 ===")
    print(f"API Key: {'已配置' if settings.KIMI_API_KEY else '未配置'}")
    print(f"API Base: {settings.KIMI_API_BASE}")
    print(f"Model: {settings.KIMI_MODEL}")
    print(f"Max Tokens: {settings.KIMI_MAX_TOKENS}")
    print(f"Temperature: {settings.KIMI_TEMPERATURE}")
    print(f"Timeout: {settings.KIMI_TIMEOUT}")
    print(f"Enabled: {settings.KIMI_ENABLED}")
    print()


async def demo_usage():
    """演示如何使用 AI 服务（模拟）"""
    print("=== AI 服务使用演示 ===")
    
    # 初始化服务
    ai_service = AIService()
    
    if not ai_service.enabled:
        print("❌ AI 服务未启用")
        print("请检查：")
        print("1. .env.local 文件中是否设置了有效的 KIMI_API_KEY")
        print("2. KIMI_ENABLED 是否设置为 true")
        print("3. API Key 是否有效且未过期")
        await ai_service.close()
        return
    
    print("✅ AI 服务已启用，以下为使用示例：")
    print()
    
    # 示例1：简单对话
    print("1. 简单对话示例：")
    print("   await ai_service.simple_chat('你好，请介绍一下自己')")
    print()
    
    # 示例2：带上下文的对话
    print("2. 带上下文的对话示例：")
    print("   context = '你是一个专业的项目管理专家'")
    print("   await ai_service.simple_chat('分析这个项目的风险', context)")
    print()
    
    # 示例3：项目分析
    print("3. 项目分析示例：")
    print("   project_data = {'name': '测试项目', 'budget': 100000}")
    print("   await ai_service.project_analysis(project_data)")
    print()
    
    # 示例4：完整聊天完成
    print("4. 完整聊天完成示例：")
    print("   messages = [")
    print("       {'role': 'system', 'content': '你是 AI 助手'},")
    print("       {'role': 'user', 'content': '你好'}")
    print("   ]")
    print("   await ai_service.chat_completion(messages)")
    print()
    
    await ai_service.close()


def api_key_info():
    """API Key 获取指南"""
    print("=== API Key 获取指南 ===")
    print("1. 访问 Moonshot AI 开放平台: https://platform.moonshot.cn/")
    print("2. 注册/登录账号")
    print("3. 进入控制台 → API 密钥")
    print("4. 点击'创建新的 API Key'")
    print("5. 复制以 'sk-' 开头的 API Key")
    print("6. 将 API Key 填入 .env.local 文件中的 KIMI_API_KEY")
    print()
    print("⚠️  注意事项：")
    print("- API Key 是敏感信息，请妥善保管")
    print("- 不要将 API Key 提交到代码仓库")
    print("- 定期更换 API Key 以确保安全")
    print()


async def main():
    """主函数"""
    print("Kimi AI 配置和使用指南")
    print("=" * 50)
    
    # 显示当前配置
    print_config()
    
    # API Key 获取指南
    api_key_info()
    
    # 演示使用方法
    await demo_usage()


if __name__ == "__main__":
    asyncio.run(main())