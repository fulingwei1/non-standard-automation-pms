#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLM API 测试脚本
测试智谱AI GLM模型的调用
"""

import os
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

API_KEY = os.getenv("GLM_API_KEY")
API_BASE = os.getenv("GLM_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
MODEL = os.getenv("GLM_MODEL", "glm-4")


def test_basic_chat():
    """测试基础对话"""
    print("=" * 60)
    print("测试1：基础对话")
    print("=" * 60)
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "你好，请简单介绍一下自己"
            }
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✅ API调用成功！")
        print(f"\n模型: {result['model']}")
        print(f"回复: {result['choices'][0]['message']['content']}")
        print(f"\nToken使用:")
        print(f"  - 输入: {result['usage']['prompt_tokens']}")
        print(f"  - 输出: {result['usage']['completion_tokens']}")
        print(f"  - 总计: {result['usage']['total_tokens']}")
        
        # 估算费用（按GLM-4: 0.1元/千tokens）
        cost = result['usage']['total_tokens'] / 1000 * 0.1
        print(f"\n预估费用: ¥{cost:.4f}")
        
    except Exception as e:
        print(f"❌ 调用失败: {e}")


def test_marketing_slogan():
    """测试营销口号生成"""
    print("\n" + "=" * 60)
    print("测试2：为金凯博生成营销口号")
    print("=" * 60)
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一名专业的营销专家，擅长创作吸引人的品牌口号"
            },
            {
                "role": "user",
                "content": """
                请为金凯博自动化测试设备公司创作3个吸引人的营销口号。
                
                公司背景：
                - 主营：ICT测试设备、FCT测试系统、AOI视觉检测设备
                - 行业：非标自动化测试设备
                - 客户：电子制造企业
                - 特点：定制化、高精度、智能化
                
                要求：
                1. 简洁有力（10字以内）
                2. 突出技术特色
                3. 易于传播
                """
            }
        ],
        "max_tokens": 500,
        "temperature": 0.9  # 创意类任务使用较高温度
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✅ 生成成功！")
        print(f"\n{result['choices'][0]['message']['content']}")
        
        cost = result['usage']['total_tokens'] / 1000 * 0.1
        print(f"\n预估费用: ¥{cost:.4f}")
        
    except Exception as e:
        print(f"❌ 调用失败: {e}")


def test_technical_doc():
    """测试技术文档改进"""
    print("\n" + "=" * 60)
    print("测试3：改进技术文档")
    print("=" * 60)
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    original_doc = """
    测试设备操作步骤：
    1. 开机
    2. 放板子
    3. 点开始
    4. 等结果
    5. 拿板子
    """
    
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": f"""
                请帮我改进这份技术文档，使其更专业、规范：
                
                原文：
                {original_doc}
                
                改进要求：
                1. 使用专业术语
                2. 补充必要的注意事项
                3. 添加安全提示
                4. 优化排版
                """
            }
        ],
        "max_tokens": 800,
        "temperature": 0.5  # 技术类任务使用较低温度
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✅ 改进成功！")
        print(f"\n原文:")
        print(original_doc)
        print(f"\n改进后:")
        print(result['choices'][0]['message']['content'])
        
        cost = result['usage']['total_tokens'] / 1000 * 0.1
        print(f"\n预估费用: ¥{cost:.4f}")
        
    except Exception as e:
        print(f"❌ 调用失败: {e}")


def test_glm5_thinking():
    """测试GLM-5的Thinking模式（如果支持）"""
    print("\n" + "=" * 60)
    print("测试4：GLM-5 Thinking模式")
    print("=" * 60)
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": "glm-5",  # 尝试GLM-5
        "messages": [
            {
                "role": "user",
                "content": "分析一下：如何提高自动化测试设备的生产效率？"
            }
        ],
        "thinking": {
            "type": "enabled"  # 启用思考链
        },
        "max_tokens": 2000,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✅ GLM-5调用成功！")
        print(f"\n模型: {result['model']}")
        
        # GLM-5可能返回thinking过程
        message = result['choices'][0]['message']
        if 'thinking' in message:
            print(f"\n思考过程:")
            print(message['thinking'])
        
        print(f"\n回复:")
        print(message['content'])
        
        cost = result['usage']['total_tokens'] / 1000 * 0.15  # GLM-5费用可能更高
        print(f"\n预估费用: ¥{cost:.4f}")
        
    except Exception as e:
        print(f"❌ GLM-5调用失败: {e}")
        print(f"提示: 你的账户可能不支持GLM-5，建议使用GLM-4")


if __name__ == "__main__":
    print("\n" + "🧪 GLM API 测试脚本")
    print("=" * 60)
    print(f"API Key: {API_KEY[:20]}...{API_KEY[-10:]}")
    print(f"API Base: {API_BASE}")
    print(f"默认模型: {MODEL}")
    print("=" * 60)
    
    # 运行测试
    test_basic_chat()
    test_marketing_slogan()
    test_technical_doc()
    
    # 可选：测试GLM-5
    # test_glm5_thinking()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
