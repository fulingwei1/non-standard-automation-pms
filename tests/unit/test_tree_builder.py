# -*- coding: utf-8 -*-
"""通用树结构构建工具单元测试"""
from dataclasses import dataclass

import pytest

from app.common.tree_builder import build_tree


class TestBuildTree:
    def test_empty_list(self):
        """测试空列表"""
        result = build_tree([])
        assert result == []

    def test_single_node(self):
        """测试单个节点"""
        items = [{"id": 1, "name": "Root", "parent_id": None}]
        result = build_tree(items)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Root"
        assert result[0]["children"] == []

    def test_flat_list_no_parent(self):
        """测试无父子关系的扁平列表"""
        items = [
            {"id": 1, "name": "A"},
            {"id": 2, "name": "B"},
            {"id": 3, "name": "C"},
        ]
        result = build_tree(items)
        
        assert len(result) == 3
        # 所有节点都是根节点
        assert all(node["children"] == [] for node in result)

    def test_simple_tree(self):
        """测试简单树结构"""
        items = [
            {"id": 1, "name": "Root", "parent_id": None},
            {"id": 2, "name": "Child1", "parent_id": 1},
            {"id": 3, "name": "Child2", "parent_id": 1},
        ]
        result = build_tree(items)
        
        assert len(result) == 1  # 1个根节点
        root = result[0]
        assert root["id"] == 1
        assert len(root["children"]) == 2
        
        children_ids = {c["id"] for c in root["children"]}
        assert children_ids == {2, 3}

    def test_multi_level_tree(self):
        """测试多层级树"""
        items = [
            {"id": 1, "name": "Root", "parent_id": None},
            {"id": 2, "name": "Child1", "parent_id": 1},
            {"id": 3, "name": "Child2", "parent_id": 1},
            {"id": 4, "name": "GrandChild1", "parent_id": 2},
            {"id": 5, "name": "GrandChild2", "parent_id": 2},
        ]
        result = build_tree(items)
        
        assert len(result) == 1
        root = result[0]
        assert root["id"] == 1
        
        child1 = next(c for c in root["children"] if c["id"] == 2)
        child2 = next(c for c in root["children"] if c["id"] == 3)
        
        assert len(child1["children"]) == 2
        assert len(child2["children"]) == 0

    def test_custom_id_key(self):
        """测试自定义ID字段名"""
        items = [
            {"dept_id": 1, "name": "Root", "parent_dept_id": None},
            {"dept_id": 2, "name": "Child", "parent_dept_id": 1},
        ]
        result = build_tree(items, id_key="dept_id", parent_key="parent_dept_id")
        
        assert len(result) == 1
        assert result[0]["dept_id"] == 1

    def test_custom_children_key(self):
        """测试自定义children字段名"""
        items = [
            {"id": 1, "name": "Root", "parent_id": None},
            {"id": 2, "name": "Child", "parent_id": 1},
        ]
        result = build_tree(items, children_key="sub_items")
        
        assert "sub_items" in result[0]
        assert len(result[0]["sub_items"]) == 1

    def test_custom_root_parent(self):
        """测试自定义根节点parent值"""
        items = [
            {"id": 1, "name": "Root", "parent_id": 0},
            {"id": 2, "name": "Child", "parent_id": 1},
        ]
        result = build_tree(items, root_parent=0)
        
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_sort_key(self):
        """测试排序"""
        items = [
            {"id": 1, "name": "B", "parent_id": None, "sort_order": 2},
            {"id": 2, "name": "A", "parent_id": None, "sort_order": 1},
            {"id": 3, "name": "C", "parent_id": None, "sort_order": 3},
        ]
        result = build_tree(items, sort_key=lambda x: x.get("sort_order", 0))
        
        names = [n["name"] for n in result]
        assert names == ["A", "B", "C"]

    def test_custom_to_dict(self):
        """测试自定义转换函数"""
        @dataclass
        class Department:
            dept_id: int
            dept_name: str
            parent_dept_id: int
        
        items = [
            Department(1, "Root", 0),
            Department(2, "Child", 1),
        ]
        
        result = build_tree(
            items,
            id_key="dept_id",
            parent_key="parent_dept_id",
            to_dict=lambda d: {
                "dept_id": d.dept_id,
                "dept_name": d.dept_name,
                "parent_dept_id": d.parent_dept_id,
            }
        )
        
        assert len(result) == 1
        assert result[0]["dept_name"] == "Root"

    def test_disconnected_nodes(self):
        """测试孤立节点（父节点不存在）"""
        items = [
            {"id": 1, "name": "Root", "parent_id": None},
            {"id": 2, "name": "Orphan", "parent_id": 999},  # 父节点不存在
        ]
        result = build_tree(items)
        
        # 孤立节点也作为根节点
        assert len(result) == 2

    def test_self_reference(self):
        """测试自引用节点（父节点是自己）- 这类节点不会作为根节点出现"""
        items = [
            {"id": 1, "name": "A", "parent_id": 1},
        ]
        result = build_tree(items)
        
        # 自引用的节点会被挂载到自己下，不会作为根节点
        assert len(result) == 0