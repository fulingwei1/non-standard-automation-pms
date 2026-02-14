#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色层级可视化工具

功能：
1. 生成角色继承树的可视化图表
2. 展示权限继承关系
3. 导出为多种格式（文本、JSON、HTML）
"""

import argparse
import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import Role
from app.utils.role_inheritance_utils import RoleInheritanceUtils


class RoleHierarchyVisualizer:
    """角色层级可视化器"""

    def __init__(self, db: Session):
        self.db = db

    def visualize_tree_text(self, tenant_id: int = None) -> str:
        """
        生成文本格式的角色树

        Args:
            tenant_id: 租户ID

        Returns:
            文本格式的树形结构
        """
        tree_data = RoleInheritanceUtils.get_role_tree_data(self.db, tenant_id)

        lines = []
        lines.append("=" * 80)
        lines.append("角色继承层级树")
        lines.append("=" * 80)
        lines.append("")

        def render_node(node, prefix="", is_last=True):
            """递归渲染节点"""
            connector = "└── " if is_last else "├── "
            inherit_mark = "✓" if node["inherit_permissions"] else "✗"
            system_mark = "[系统]" if node["is_system"] else ""

            # 节点信息
            node_info = (
                f"{node['name']} ({node['code']}) "
                f"Level:{node['level']} "
                f"继承:{inherit_mark} "
                f"权限:{node['own_permissions']}/{node['total_permissions']} "
                f"{system_mark}"
            )

            lines.append(f"{prefix}{connector}{node_info}")

            # 描述
            if node.get("description"):
                desc_prefix = prefix + ("    " if is_last else "│   ")
                lines.append(f"{desc_prefix}📝 {node['description']}")

            # 递归渲染子节点
            children = node.get("children", [])
            for i, child in enumerate(children):
                child_prefix = prefix + ("    " if is_last else "│   ")
                render_node(child, child_prefix, i == len(children) - 1)

        for i, root in enumerate(tree_data):
            render_node(root, "", i == len(tree_data) - 1)
            lines.append("")

        # 添加统计信息
        stats = RoleInheritanceUtils.get_inheritance_statistics(self.db)
        lines.append("=" * 80)
        lines.append("统计信息")
        lines.append("=" * 80)
        lines.append(f"总角色数: {stats['total_roles']}")
        lines.append(f"根角色数: {stats['root_roles']}")
        lines.append(f"继承角色数: {stats['inherited_roles']}")
        lines.append(f"非继承角色数: {stats['non_inherited_roles']}")
        lines.append(f"最大继承深度: Level {stats['max_depth']}")
        lines.append(f"缓存状态: {stats['cache_size']}")

        return "\n".join(lines)

    def visualize_tree_json(self, tenant_id: int = None) -> str:
        """
        生成JSON格式的角色树

        Args:
            tenant_id: 租户ID

        Returns:
            JSON字符串
        """
        tree_data = RoleInheritanceUtils.get_role_tree_data(self.db, tenant_id)
        stats = RoleInheritanceUtils.get_inheritance_statistics(self.db)

        output = {"tree": tree_data, "statistics": stats}

        return json.dumps(output, indent=2, ensure_ascii=False)

    def visualize_tree_html(self, tenant_id: int = None) -> str:
        """
        生成HTML格式的角色树

        Args:
            tenant_id: 租户ID

        Returns:
            HTML字符串
        """
        tree_data = RoleInheritanceUtils.get_role_tree_data(self.db, tenant_id)
        stats = RoleInheritanceUtils.get_inheritance_statistics(self.db)

        html_parts = []
        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html><head><meta charset='utf-8'>")
        html_parts.append("<title>角色继承层级树</title>")
        html_parts.append("<style>")
        html_parts.append(
            """
            body { font-family: 'Microsoft YaHei', Arial, sans-serif; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }
            .tree { font-family: 'Courier New', monospace; }
            .role-node { margin: 5px 0; padding: 8px; background: #f9f9f9; border-left: 3px solid #4CAF50; }
            .role-name { font-weight: bold; color: #2196F3; }
            .role-code { color: #666; }
            .role-stats { color: #888; font-size: 0.9em; }
            .inherit-yes { color: #4CAF50; }
            .inherit-no { color: #FF5722; }
            .level-0 { margin-left: 0; }
            .level-1 { margin-left: 40px; }
            .level-2 { margin-left: 80px; }
            .level-3 { margin-left: 120px; }
            .stats-box { background: #E3F2FD; padding: 15px; border-radius: 5px; margin-top: 20px; }
            .stats-item { margin: 5px 0; }
            .badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.85em; }
            .badge-system { background: #FFC107; color: #333; }
            .badge-inherit { background: #4CAF50; color: white; }
            .badge-no-inherit { background: #FF5722; color: white; }
        """
        )
        html_parts.append("</style></head><body>")
        html_parts.append("<div class='container'>")
        html_parts.append("<h1>🌳 角色继承层级树</h1>")
        html_parts.append("<div class='tree'>")

        def render_html_node(node):
            """递归渲染HTML节点"""
            level_class = f"level-{min(node['level'], 3)}"
            inherit_class = "inherit-yes" if node["inherit_permissions"] else "inherit-no"
            inherit_text = "✓ 继承" if node["inherit_permissions"] else "✗ 不继承"
            system_badge = (
                "<span class='badge badge-system'>系统</span>"
                if node["is_system"]
                else ""
            )

            html = f"<div class='role-node {level_class}'>"
            html += f"<span class='role-name'>{node['name']}</span> "
            html += f"<span class='role-code'>({node['code']})</span> "
            html += system_badge
            html += f"<br><span class='role-stats'>"
            html += f"Level {node['level']} | "
            html += f"<span class='{inherit_class}'>{inherit_text}</span> | "
            html += f"自有权限: {node['own_permissions']} | "
            html += f"总权限: {node['total_permissions']}"
            html += "</span>"

            if node.get("description"):
                html += f"<br><span style='color: #666; font-size: 0.9em;'>📝 {node['description']}</span>"

            html += "</div>"

            # 递归子节点
            for child in node.get("children", []):
                html += render_html_node(child)

            return html

        for root in tree_data:
            html_parts.append(render_html_node(root))

        html_parts.append("</div>")

        # 统计信息
        html_parts.append("<div class='stats-box'>")
        html_parts.append("<h2>📊 统计信息</h2>")
        html_parts.append(f"<div class='stats-item'>总角色数: <strong>{stats['total_roles']}</strong></div>")
        html_parts.append(f"<div class='stats-item'>根角色数: <strong>{stats['root_roles']}</strong></div>")
        html_parts.append(f"<div class='stats-item'>继承角色数: <strong>{stats['inherited_roles']}</strong></div>")
        html_parts.append(f"<div class='stats-item'>非继承角色数: <strong>{stats['non_inherited_roles']}</strong></div>")
        html_parts.append(f"<div class='stats-item'>最大继承深度: <strong>Level {stats['max_depth']}</strong></div>")
        html_parts.append("</div>")

        html_parts.append("</div></body></html>")

        return "".join(html_parts)

    def visualize_role_detail(self, role_id: int) -> str:
        """
        显示单个角色的详细信息

        Args:
            role_id: 角色ID

        Returns:
            详细信息文本
        """
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return f"角色 ID {role_id} 不存在"

        lines = []
        lines.append("=" * 80)
        lines.append(f"角色详情: {role.role_name} ({role.role_code})")
        lines.append("=" * 80)
        lines.append("")

        # 基本信息
        lines.append(f"ID: {role.id}")
        lines.append(f"编码: {role.role_code}")
        lines.append(f"名称: {role.role_name}")
        lines.append(f"描述: {role.description or '无'}")
        lines.append(f"是否系统角色: {'是' if role.is_system else '否'}")
        lines.append(f"是否启用: {'是' if role.is_active else '否'}")
        lines.append(f"继承权限: {'是' if role.inherit_permissions else '否'}")
        lines.append("")

        # 继承链
        chain = RoleInheritanceUtils.get_role_chain(self.db, role_id)
        lines.append(f"继承链 (共 {len(chain)} 层):")
        for i, r in enumerate(chain):
            lines.append(f"  Level {i}: {r.role_name} ({r.role_code})")
        lines.append("")

        # 层级
        level = RoleInheritanceUtils.calculate_role_level(self.db, role_id)
        lines.append(f"继承层级: Level {level}")
        lines.append("")

        # 权限
        own_perms = (
            self.db.query(RoleInheritanceUtils)
            .filter(RoleInheritanceUtils.role_id == role_id)
            .count()
        )
        inherited_perms = RoleInheritanceUtils.get_inherited_permissions(
            self.db, role_id
        )
        lines.append(f"自有权限数: {own_perms}")
        lines.append(f"总权限数（含继承）: {len(inherited_perms)}")
        lines.append("")

        # 子角色
        children = self.db.query(Role).filter(Role.parent_id == role_id).all()
        lines.append(f"子角色数: {len(children)}")
        for child in children:
            lines.append(f"  - {child.role_name} ({child.role_code})")

        return "\n".join(lines)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="角色层级可视化工具")
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "html"],
        default="text",
        help="输出格式",
    )
    parser.add_argument("--output", "-o", help="输出文件路径（默认输出到控制台）")
    parser.add_argument("--tenant", "-t", type=int, help="租户ID")
    parser.add_argument("--role", "-r", type=int, help="显示单个角色的详细信息")
    parser.add_argument("--validate", "-v", action="store_true", help="验证角色层级")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        visualizer = RoleHierarchyVisualizer(db)

        # 验证模式
        if args.validate:
            print("🔍 验证角色层级完整性...")
            is_valid, errors = RoleInheritanceUtils.validate_role_hierarchy(db)
            if is_valid:
                print("✅ 角色层级验证通过！")
            else:
                print("❌ 发现以下问题：")
                for error in errors:
                    print(f"  - {error}")
            return

        # 单角色详情模式
        if args.role:
            output = visualizer.visualize_role_detail(args.role)
        else:
            # 树形可视化模式
            if args.format == "text":
                output = visualizer.visualize_tree_text(args.tenant)
            elif args.format == "json":
                output = visualizer.visualize_tree_json(args.tenant)
            elif args.format == "html":
                output = visualizer.visualize_tree_html(args.tenant)

        # 输出结果
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"✅ 已保存到: {args.output}")
        else:
            print(output)

    finally:
        db.close()


if __name__ == "__main__":
    main()
