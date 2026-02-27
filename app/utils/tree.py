# -*- coding: utf-8 -*-
"""
树形结构构建工具

统一入口，实际实现在 app/common/tree_builder.py。
推荐使用此模块导入：
    from app.utils.tree import build_tree
"""

from app.common.tree_builder import build_tree  # noqa: F401

__all__ = ["build_tree"]
