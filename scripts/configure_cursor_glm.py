#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor GLM-4.7 模型自动配置脚本
注意：此脚本尝试通过修改配置文件来添加 GLM 模型配置
但 Cursor 可能需要在 UI 中完成配置才能生效
"""

import json
from pathlib import Path

# 配置信息
GLM_CONFIG = {
    "apiKey": "6f80249e3d434099a3fb8c898f9b65ef.OmqhpVVwiQaNLkDp",
    "baseUrl": "https://open.bigmodel.cn/api/coding/paas/v4",
    "modelName": "GLM-4.7",
    "provider": "openai"
}

# Cursor 配置文件路径
CURSOR_SETTINGS_PATH = Path.home() / "Library/Application Support/Cursor/User/settings.json"


def backup_settings():
    """备份当前设置文件"""
    if CURSOR_SETTINGS_PATH.exists():
        backup_path = CURSOR_SETTINGS_PATH.with_suffix('.json.backup')
        import shutil
        shutil.copy2(CURSOR_SETTINGS_PATH, backup_path)
        print(f"✅ 已备份设置文件到: {backup_path}")
        return True
    return False


def load_settings():
    """加载当前设置"""
    if CURSOR_SETTINGS_PATH.exists():
        with open(CURSOR_SETTINGS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_settings(settings):
    """保存设置"""
    CURSOR_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CURSOR_SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)
    print(f"✅ 已保存设置到: {CURSOR_SETTINGS_PATH}")


def configure_glm():
    """配置 GLM 模型"""
    print("=" * 60)
    print("Cursor GLM-4.7 模型配置工具")
    print("=" * 60)

    # 备份
    if not backup_settings():
        print("⚠️  未找到现有设置文件，将创建新文件")

    # 加载设置
    settings = load_settings()

    # 添加 GLM 配置
    # 注意：Cursor 的自定义模型配置可能不在这里，但我们可以尝试添加
    settings["cursor.glm.apiKey"] = GLM_CONFIG["apiKey"]
    settings["cursor.glm.baseUrl"] = GLM_CONFIG["baseUrl"]
    settings["cursor.glm.modelName"] = GLM_CONFIG["modelName"]

    # 保存
    save_settings(settings)

    print("\n" + "=" * 60)
    print("配置完成！")
    print("=" * 60)
    print("\n⚠️  重要提示：")
    print("1. Cursor 的自定义模型配置主要通过 UI 界面完成")
    print("2. 请按照以下步骤在 Cursor UI 中完成配置：")
    print("\n   步骤：")
    print("   1. 打开 Cursor (Cmd + , 打开设置)")
    print("   2. 搜索 'Models' 或进入 Cursor → Models")
    print("   3. 点击 'Add Custom Model'")
    print("   4. 选择 'OpenAI' 协议")
    print("   5. 填写以下信息：")
    print(f"      - API Key: {GLM_CONFIG['apiKey']}")
    print(f"      - Base URL: {GLM_CONFIG['baseUrl']}")
    print(f"      - Model Name: {GLM_CONFIG['modelName']}")
    print("   6. 保存并切换到 GLM-4.7 模型")
    print("\n3. 配置完成后，重启 Cursor 以确保生效")
    print("\n详细说明请查看: docs/CURSOR_GLM_QUICK_SETUP.md")
    print("=" * 60)


if __name__ == "__main__":
    try:
        configure_glm()
    except Exception as e:
        print(f"❌ 配置失败: {e}")
        import traceback
        traceback.print_exc()
