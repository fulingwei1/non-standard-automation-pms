#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非标自动化项目管理系统 - 完整PPT生成脚本（重构版本）

此文件已重构，原来1647行的代码已拆分为多个模块：
- app/services/ppt_generator/config.py - 配置文件
- app/services/ppt_generator/base_builder.py - 基础幻灯片构建器
- app/services/ppt_generator/content_builder.py - 内容幻灯片构建器
- app/services/ppt_generator/table_builder.py - 表格幻灯片构建器
- app/services/ppt_generator/generator.py - 主生成器

本文件仅保留简单的调用逻辑。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ppt_generator import PresentationGenerator


def create_full_presentation(output_path: str = "完整PPT.pptx"):
    """
    创建完整的PPT

    Args:
        output_path: 输出文件路径

    Returns:
        输出文件路径
    """
    generator = PresentationGenerator()
    return generator.generate(output_path)


if __name__ == "__main__":
    create_full_presentation()
