# -*- coding: utf-8 -*-
"""
通用树结构构建工具

将扁平列表（带 parent_id）构建为嵌套树结构，替代各处手写
``children = []`` + 循环 ``parent["children"].append(child)`` 的重复代码。
"""

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    TypeVar,
)

T = TypeVar("T")


def build_tree(
    items: Sequence[T],
    *,
    id_key: str = "id",
    parent_key: str = "parent_id",
    children_key: str = "children",
    to_dict: Optional[Callable[[T], Dict[str, Any]]] = None,
    sort_key: Optional[Callable[[Dict[str, Any]], Any]] = None,
    root_parent: Any = None,
) -> List[Dict[str, Any]]:
    """
    将扁平列表构建为嵌套树结构。

    使用 O(n) 的 map-based 算法，适用于任何带 parent_id 的数据。

    Args:
        items: 扁平数据列表（可以是 ORM 对象、dict 或任意对象）。
        id_key: 节点 ID 字段名，默认 "id"。
        parent_key: 父节点 ID 字段名，默认 "parent_id"。
        children_key: 子节点列表字段名，默认 "children"。
        to_dict: 将单个 item 转为 dict 的函数；未传时自动处理 dict 和 ORM 对象。
        sort_key: 对同层节点排序的 key 函数；未传时保持原始顺序。
        root_parent: 根节点的 parent_id 值，默认 None。

    Returns:
        嵌套树结构的 list[dict]。

    示例::

        departments = db.query(Department).all()
        tree = build_tree(
            departments,
            to_dict=lambda d: {"id": d.id, "name": d.dept_name, "parent_id": d.parent_id},
            sort_key=lambda n: n.get("sort_order", 0),
        )
    """
    converter = to_dict or _default_to_dict

    # Step 1: 将所有 item 转为 dict，并建立 id -> node 映射
    node_map: Dict[Any, Dict[str, Any]] = {}
    nodes: List[Dict[str, Any]] = []
    for item in items:
        node = converter(item)
        node[children_key] = []
        node_id = node.get(id_key)
        node_map[node_id] = node
        nodes.append(node)

    # Step 2: 遍历所有节点，将每个节点挂到父节点下
    tree: List[Dict[str, Any]] = []
    for node in nodes:
        pid = node.get(parent_key)
        if pid == root_parent or pid not in node_map:
            tree.append(node)
        else:
            node_map[pid][children_key].append(node)

    # Step 3: 可选排序
    if sort_key is not None:
        _sort_tree(tree, children_key, sort_key)

    return tree


def _sort_tree(
    nodes: List[Dict[str, Any]],
    children_key: str,
    sort_key: Callable[[Dict[str, Any]], Any],
) -> None:
    """递归地对树的每一层按 sort_key 排序。"""
    nodes.sort(key=sort_key)
    for node in nodes:
        children = node.get(children_key)
        if children:
            _sort_tree(children, children_key, sort_key)


def _default_to_dict(item: Any) -> Dict[str, Any]:
    """
    默认的 item -> dict 转换器。

    - dict: 返回浅拷贝。
    - ORM 对象: 使用 __dict__ 并过滤 SQLAlchemy 内部属性。
    """
    if isinstance(item, dict):
        return dict(item)
    # ORM 对象
    result = {}
    for k, v in vars(item).items():
        if not k.startswith("_"):
            result[k] = v
    return result
