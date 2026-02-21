# -*- coding: utf-8 -*-
"""
树结构构建工具全面测试

测试 app/common/tree_builder.py 中的所有函数
"""
import pytest
from app.common.tree_builder import build_tree, _default_to_dict


class TestDefaultToDict:
    """测试默认转换函数"""

    def test_dict_input(self):
        """测试字典输入"""
        input_dict = {"id": 1, "name": "Test"}
        result = _default_to_dict(input_dict)
        
        assert result == {"id": 1, "name": "Test"}
        assert result is not input_dict  # 应该是浅拷贝
    
    def test_orm_object(self):
        """测试ORM对象"""
        class FakeORM:
            def __init__(self):
                self.id = 1
                self.name = "Test"
                self._sa_instance_state = "should be filtered"
        
        obj = FakeORM()
        result = _default_to_dict(obj)
        
        assert result == {"id": 1, "name": "Test"}
        assert "_sa_instance_state" not in result
    
    def test_filters_private_attributes(self):
        """测试过滤私有属性"""
        class TestObj:
            def __init__(self):
                self.public = "visible"
                self._private = "hidden"
                self.__very_private = "hidden"
        
        obj = TestObj()
        result = _default_to_dict(obj)
        
        assert "public" in result
        assert "_private" not in result


class TestBuildTree:
    """测试构建树函数"""

    def test_simple_tree(self):
        """测试简单树结构"""
        items = [
            {"id": 1, "name": "Root", "parent_id": None},
            {"id": 2, "name": "Child1", "parent_id": 1},
            {"id": 3, "name": "Child2", "parent_id": 1},
        ]
        
        tree = build_tree(items)
        
        assert len(tree) == 1
        assert tree[0]["id"] == 1
        assert len(tree[0]["children"]) == 2
        assert tree[0]["children"][0]["id"] == 2
        assert tree[0]["children"][1]["id"] == 3
    
    def test_multi_level_tree(self):
        """测试多层树结构"""
        items = [
            {"id": 1, "name": "Root", "parent_id": None},
            {"id": 2, "name": "Level1-1", "parent_id": 1},
            {"id": 3, "name": "Level1-2", "parent_id": 1},
            {"id": 4, "name": "Level2-1", "parent_id": 2},
            {"id": 5, "name": "Level2-2", "parent_id": 3},
        ]
        
        tree = build_tree(items)
        
        assert len(tree) == 1
        assert len(tree[0]["children"]) == 2
        assert len(tree[0]["children"][0]["children"]) == 1
        assert len(tree[0]["children"][1]["children"]) == 1
        assert tree[0]["children"][0]["children"][0]["id"] == 4
    
    def test_multiple_roots(self):
        """测试多个根节点"""
        items = [
            {"id": 1, "name": "Root1", "parent_id": None},
            {"id": 2, "name": "Root2", "parent_id": None},
            {"id": 3, "name": "Child1", "parent_id": 1},
            {"id": 4, "name": "Child2", "parent_id": 2},
        ]
        
        tree = build_tree(items)
        
        assert len(tree) == 2
        assert tree[0]["id"] == 1
        assert tree[1]["id"] == 2
        assert len(tree[0]["children"]) == 1
        assert len(tree[1]["children"]) == 1
    
    def test_empty_list(self):
        """测试空列表"""
        tree = build_tree([])
        assert tree == []
    
    def test_single_item(self):
        """测试单个节点"""
        items = [{"id": 1, "name": "Only", "parent_id": None}]
        tree = build_tree(items)
        
        assert len(tree) == 1
        assert tree[0]["id"] == 1
        assert tree[0]["children"] == []
    
    def test_orphan_nodes(self):
        """测试孤儿节点（父节点不存在）"""
        items = [
            {"id": 1, "name": "Root", "parent_id": None},
            {"id": 2, "name": "Child", "parent_id": 1},
            {"id": 3, "name": "Orphan", "parent_id": 999},  # 父节点不存在
        ]
        
        tree = build_tree(items)
        
        # 孤儿节点应该被当作根节点
        assert len(tree) == 2
        root_ids = {node["id"] for node in tree}
        assert 1 in root_ids
        assert 3 in root_ids
    
    def test_custom_id_key(self):
        """测试自定义ID键"""
        items = [
            {"dept_id": 1, "name": "Root", "parent_dept_id": None},
            {"dept_id": 2, "name": "Child", "parent_dept_id": 1},
        ]
        
        tree = build_tree(
            items,
            id_key="dept_id",
            parent_key="parent_dept_id"
        )
        
        assert tree[0]["dept_id"] == 1
        assert tree[0]["children"][0]["dept_id"] == 2
    
    def test_custom_children_key(self):
        """测试自定义子节点键"""
        items = [
            {"id": 1, "name": "Root", "parent_id": None},
            {"id": 2, "name": "Child", "parent_id": 1},
        ]
        
        tree = build_tree(items, children_key="sub_nodes")
        
        assert "sub_nodes" in tree[0]
        assert len(tree[0]["sub_nodes"]) == 1
    
    def test_custom_to_dict(self):
        """测试自定义转换函数"""
        class Department:
            def __init__(self, dept_id, name, parent_id):
                self.dept_id = dept_id
                self.dept_name = name
                self.parent_id = parent_id
        
        items = [
            Department(1, "总公司", None),
            Department(2, "分公司A", 1),
            Department(3, "分公司B", 1),
        ]
        
        def to_dict(dept):
            return {
                "id": dept.dept_id,
                "name": dept.dept_name,
                "parent_id": dept.parent_id
            }
        
        tree = build_tree(items, to_dict=to_dict)
        
        assert tree[0]["id"] == 1
        assert tree[0]["name"] == "总公司"
        assert len(tree[0]["children"]) == 2
    
    def test_sort_by_key(self):
        """测试排序功能"""
        items = [
            {"id": 1, "name": "Root", "parent_id": None, "order": 1},
            {"id": 2, "name": "C", "parent_id": 1, "order": 3},
            {"id": 3, "name": "A", "parent_id": 1, "order": 1},
            {"id": 4, "name": "B", "parent_id": 1, "order": 2},
        ]
        
        tree = build_tree(items, sort_key=lambda n: n.get("order", 0))
        
        # 子节点应该按order排序
        children = tree[0]["children"]
        assert children[0]["name"] == "A"
        assert children[1]["name"] == "B"
        assert children[2]["name"] == "C"
    
    def test_sort_by_name(self):
        """测试按名称排序"""
        items = [
            {"id": 1, "name": "Root", "parent_id": None},
            {"id": 2, "name": "Charlie", "parent_id": 1},
            {"id": 3, "name": "Alice", "parent_id": 1},
            {"id": 4, "name": "Bob", "parent_id": 1},
        ]
        
        tree = build_tree(items, sort_key=lambda n: n.get("name", ""))
        
        children = tree[0]["children"]
        assert children[0]["name"] == "Alice"
        assert children[1]["name"] == "Bob"
        assert children[2]["name"] == "Charlie"
    
    def test_deep_nesting(self):
        """测试深层嵌套"""
        items = [
            {"id": 1, "name": "L1", "parent_id": None},
            {"id": 2, "name": "L2", "parent_id": 1},
            {"id": 3, "name": "L3", "parent_id": 2},
            {"id": 4, "name": "L4", "parent_id": 3},
            {"id": 5, "name": "L5", "parent_id": 4},
        ]
        
        tree = build_tree(items)
        
        # 验证深度
        node = tree[0]
        for i in range(4):
            assert len(node["children"]) == 1
            node = node["children"][0]
        assert len(node["children"]) == 0
    
    def test_root_parent_zero(self):
        """测试根节点parent_id为0的情况"""
        items = [
            {"id": 1, "name": "Root", "parent_id": 0},
            {"id": 2, "name": "Child", "parent_id": 1},
        ]
        
        tree = build_tree(items, root_parent=0)
        
        assert len(tree) == 1
        assert tree[0]["id"] == 1


class TestIntegrationScenarios:
    """集成测试场景"""

    def test_department_tree(self):
        """测试部门树场景"""
        departments = [
            {"id": 1, "name": "公司", "parent_id": None, "sort": 1},
            {"id": 2, "name": "技术部", "parent_id": 1, "sort": 1},
            {"id": 3, "name": "销售部", "parent_id": 1, "sort": 2},
            {"id": 4, "name": "前端组", "parent_id": 2, "sort": 1},
            {"id": 5, "name": "后端组", "parent_id": 2, "sort": 2},
            {"id": 6, "name": "华东区", "parent_id": 3, "sort": 1},
            {"id": 7, "name": "华南区", "parent_id": 3, "sort": 2},
        ]
        
        tree = build_tree(
            departments,
            sort_key=lambda n: n.get("sort", 0)
        )
        
        assert len(tree) == 1  # 一个根节点
        assert tree[0]["name"] == "公司"
        assert len(tree[0]["children"]) == 2  # 技术部、销售部
        assert tree[0]["children"][0]["name"] == "技术部"
        assert tree[0]["children"][1]["name"] == "销售部"
        assert len(tree[0]["children"][0]["children"]) == 2  # 前端组、后端组
    
    def test_menu_tree(self):
        """测试菜单树场景"""
        menus = [
            {"id": 1, "name": "系统管理", "parent_id": None, "order": 1},
            {"id": 2, "name": "项目管理", "parent_id": None, "order": 2},
            {"id": 3, "name": "用户管理", "parent_id": 1, "order": 1},
            {"id": 4, "name": "角色管理", "parent_id": 1, "order": 2},
            {"id": 5, "name": "项目列表", "parent_id": 2, "order": 1},
            {"id": 6, "name": "项目统计", "parent_id": 2, "order": 2},
        ]
        
        tree = build_tree(
            menus,
            sort_key=lambda n: n.get("order", 0)
        )
        
        assert len(tree) == 2
        assert tree[0]["name"] == "系统管理"
        assert tree[1]["name"] == "项目管理"
    
    def test_category_tree(self):
        """测试分类树场景"""
        categories = [
            {"id": 1, "name": "电子产品", "parent_id": None},
            {"id": 2, "name": "手机", "parent_id": 1},
            {"id": 3, "name": "电脑", "parent_id": 1},
            {"id": 4, "name": "苹果手机", "parent_id": 2},
            {"id": 5, "name": "安卓手机", "parent_id": 2},
            {"id": 6, "name": "笔记本", "parent_id": 3},
            {"id": 7, "name": "台式机", "parent_id": 3},
        ]
        
        tree = build_tree(categories)
        
        # 验证树结构
        assert tree[0]["name"] == "电子产品"
        assert len(tree[0]["children"]) == 2
        
        phone_category = tree[0]["children"][0]
        assert phone_category["name"] == "手机"
        assert len(phone_category["children"]) == 2


class TestEdgeCases:
    """边界情况测试"""

    def test_circular_reference_protection(self):
        """测试循环引用（实际上算法不会陷入循环）"""
        items = [
            {"id": 1, "name": "A", "parent_id": 2},  # A的父是B
            {"id": 2, "name": "B", "parent_id": 1},  # B的父是A（循环）
        ]
        
        # 两个都会成为根节点，因为找不到有效的父节点
        tree = build_tree(items)
        assert len(tree) == 2
    
    def test_duplicate_ids(self):
        """测试重复ID（后面的会覆盖前面的）"""
        items = [
            {"id": 1, "name": "First", "parent_id": None},
            {"id": 1, "name": "Second", "parent_id": None},
        ]
        
        tree = build_tree(items)
        # 由于dict映射，后面的会覆盖前面的
        assert len(tree) == 2
    
    def test_none_id(self):
        """测试None作为ID"""
        items = [
            {"id": None, "name": "None ID", "parent_id": None},
            {"id": 1, "name": "Normal", "parent_id": None},
        ]
        
        tree = build_tree(items)
        # None ID的节点也会被处理
        assert len(tree) == 2
    
    def test_mixed_id_types(self):
        """测试混合ID类型"""
        items = [
            {"id": 1, "name": "Int ID", "parent_id": None},
            {"id": "2", "name": "String ID", "parent_id": None},
            {"id": 3, "name": "Child of Int", "parent_id": 1},
            {"id": 4, "name": "Child of String", "parent_id": "2"},
        ]
        
        tree = build_tree(items)
        assert len(tree) == 2
        
        # 找到对应的根节点
        int_root = next(n for n in tree if n["id"] == 1)
        str_root = next(n for n in tree if n["id"] == "2")
        
        assert len(int_root["children"]) == 1
        assert len(str_root["children"]) == 1
