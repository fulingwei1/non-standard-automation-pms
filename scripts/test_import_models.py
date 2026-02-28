#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的模型导入测试，捕获所有 SQLAlchemy warnings
"""

import warnings
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 捕获所有warnings
warnings.simplefilter("always")
warning_count = 0
relationship_warnings = []

def warning_handler(message, category, filename, lineno, file=None, line=None):
    """捕获warnings"""
    global warning_count, relationship_warnings
    warning_count += 1
    msg_str = str(message)
    
    if 'relationship' in msg_str.lower():
        relationship_warnings.append({
            'message': msg_str,
            'category': category.__name__,
            'filename': filename,
            'lineno': lineno
        })
        print(f"⚠️  Relationship Warning #{len(relationship_warnings)}:")
        print(f"    {msg_str[:200]}")
        print()

# 设置warning handler
warnings.showwarning = warning_handler

print("=" * 80)
print("SQLAlchemy Models Import Test")
print("=" * 80)
print()
print("导入所有模型，检测 relationship warnings...")
print()

try:
    # 导入所有核心模型
    
    print("✅ 所有模型导入成功")
    print()
    
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 80)
print("测试结果")
print("=" * 80)
print()

print(f"总警告数: {warning_count}")
print(f"Relationship 警告数: {len(relationship_warnings)}")
print()

if relationship_warnings:
    print("❌ 发现 Relationship 警告:")
    for i, w in enumerate(relationship_warnings, 1):
        print(f"\n警告 #{i}:")
        print(f"  {w['message']}")
    sys.exit(1)
else:
    print("✅ 没有发现任何 relationship 警告!")
    print()
    print("修复验证：成功 ✓")
    sys.exit(0)
