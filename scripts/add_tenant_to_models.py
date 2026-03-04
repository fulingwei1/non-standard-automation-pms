#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动为所有模型文件添加 tenant_id 字段

功能:
1. 读取待处理表清单
2. 自动在模型类中添加 tenant_id 字段
3. 添加 tenant relationship
4. 更新 __table_args__ 添加索引
5. 添加 extend_existing=True
"""

import re
from pathlib import Path

# 工作目录
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "app" / "models"

# 租户字段模板
TENANT_ID_FIELD_TEMPLATE = """
    # 多租户隔离
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=True,
        comment="租户ID（多租户隔离）"
    )
    tenant = relationship("Tenant", back_populates="{relationship_name}")
"""


def add_tenant_to_model_file(file_path: Path, table_name: str, class_name: str) -> bool:
    """
    为单个模型文件添加 tenant_id 字段

    返回: 是否成功更新
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # 1. 确保导入了必要的模块
        if "from sqlalchemy import" in content and "ForeignKey" not in content:
            # 在 sqlalchemy import 中添加 ForeignKey
            content = re.sub(
                r"(from sqlalchemy import.*?)(\))",
                lambda m: (
                    f"{m.group(1)}, ForeignKey{m.group(2)}"
                    if "ForeignKey" not in m.group(1)
                    else m.group(0)
                ),
                content,
            )

        # 查找类定义
        class_pattern = rf"class {re.escape(class_name)}\([^)]*Base[^)]*\):"
        class_match = re.search(class_pattern, content)

        if not class_match:
            print(f"⚠️  未找到类定义: {class_name} in {file_path}")
            return False

        class_start = class_match.start()

        # 2. 检查是否已有 tenant_id
        if re.search(r"tenant_id\s*=\s*Column", content[class_start : class_start + 3000]):
            print(f"✓ 跳过 {class_name} (已包含 tenant_id)")
            return False

        # 3. 查找插入位置（在 __tablename__ 之后的第一个字段定义之前）
        tablename_match = re.search(r'__tablename__\s*=\s*["\'][^"\']+["\']', content[class_start:])
        if not tablename_match:
            print(f"⚠️  未找到 __tablename__ in {class_name}")
            return False

        # 查找 __table_args__ 或第一个 Column 定义
        search_start = class_start + tablename_match.end()
        next_field_match = re.search(
            r"(\n\s+)(__table_args__|id\s*=\s*Column|[a-z_]+\s*=\s*Column)",
            content[search_start : search_start + 2000],
        )

        if not next_field_match:
            print(f"⚠️  未找到字段定义位置 in {class_name}")
            return False

        insert_pos = search_start + next_field_match.start()
        indent = next_field_match.group(1)

        # 生成关系名称（复数形式）
        relationship_name = (
            table_name
            if not table_name.endswith("s")
            else table_name[:-1] + "es" if table_name.endswith("s") else table_name + "s"
        )

        # 生成 tenant_id 字段代码
        tenant_field = TENANT_ID_FIELD_TEMPLATE.format(relationship_name=relationship_name)
        tenant_field = tenant_field.replace("\n    ", f"\n{indent}")  # 调整缩进

        # 插入字段
        content = content[:insert_pos] + tenant_field + "\n" + content[insert_pos:]

        # 4. 更新 __table_args__ 添加索引和 extend_existing
        table_args_pattern = r"__table_args__\s*=\s*\("
        table_args_match = re.search(table_args_pattern, content[class_start:])

        if table_args_match:
            # 已有 __table_args__，需要添加索引
            args_start = class_start + table_args_match.start()
            args_end_match = re.search(r"\)\s*\n", content[args_start : args_start + 2000])

            if args_end_match:
                args_end = args_start + args_end_match.start() + 1

                # 检查是否有 extend_existing
                args_content = content[args_start:args_end]
                if "extend_existing" not in args_content:
                    # 在最后的 ) 前添加 extend_existing
                    if '{"' in args_content or "{'" in args_content:
                        # 已有字典，添加 extend_existing
                        content = re.sub(
                            r"(\{[^}]*)\}(\s*\))",
                            r'\1, "extend_existing": True}\2',
                            content[args_start:args_end],
                        )
                        content = content[:args_start] + content + content[args_end:]
                    else:
                        # 添加字典
                        content = (
                            content[:args_end]
                            + ',\n        {"extend_existing": True}\n    '
                            + content[args_end:]
                        )

                # 添加租户索引
                if f"idx_{table_name}_tenant" not in args_content:
                    # 在第一个 Index 之后插入租户索引
                    index_insert = content[args_start:args_end].rfind("Index(")
                    if index_insert > 0:
                        insert_at = args_start + index_insert
                        tenant_index = f'\n        Index("idx_{table_name}_tenant", "tenant_id"),'
                        content = (
                            content[:insert_at] + tenant_index + "\n        " + content[insert_at:]
                        )
                    else:
                        # 没有索引，直接添加
                        tenant_index = f'\n        Index("idx_{table_name}_tenant", "tenant_id"),'
                        content = content[:args_end] + tenant_index + content[args_end:]
        else:
            # 没有 __table_args__，创建一个
            # 查找类的最后一个字段定义后插入
            relationships_match = re.search(
                r"\n\s+# 关系", content[class_start : class_start + 5000]
            )
            if relationships_match:
                insert_at = class_start + relationships_match.start()
            else:
                # 查找 relationship 定义前
                rel_match = re.search(
                    r"\n\s+[a-z_]+\s*=\s*relationship", content[class_start : class_start + 5000]
                )
                if rel_match:
                    insert_at = class_start + rel_match.start()
                else:
                    # 查找类定义的结尾（通过下一个class或文件结束）
                    next_class = re.search(r"\n\nclass ", content[class_start + 100 :])
                    if next_class:
                        insert_at = class_start + 100 + next_class.start()
                    else:
                        insert_at = len(content)

            table_args = f"""
{indent}__table_args__ = (
{indent}    Index("idx_{table_name}_tenant", "tenant_id"),
{indent}    {{"extend_existing": True}}
{indent})
"""
            content = content[:insert_at] + table_args + "\n" + content[insert_at:]

        # 5. 保存文件
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            print(f"✅ 已更新 {class_name} in {file_path.name}")
            return True
        else:
            print(f"⚠️  {class_name} 未发生变化")
            return False

    except Exception as e:
        print(f"❌ 处理文件失败 {file_path}: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🚀 开始批量添加 tenant_id 字段...")

    # 读取扫描结果
    tables_file = PROJECT_ROOT / "data" / "tables_need_tenant_id.txt"
    if not tables_file.exists():
        print("❌ 请先运行 scan_models_for_tenant_v2.py 生成表清单")
        return

    tables = tables_file.read_text(encoding="utf-8").strip().split("\n")
    print(f"📋 待处理表数: {len(tables)}")

    # 读取扫描报告以获取文件路径
    report_file = PROJECT_ROOT / "data" / "tenant_scan_report.md"
    report_content = report_file.read_text(encoding="utf-8")

    # 解析报告获取表名 -> (class_name, file_path) 映射
    table_info = {}
    pattern = r"`([^`]+)`\s+\((\w+)\)\s+-\s+([^\n]+)"
    for match in re.finditer(pattern, report_content):
        table_name, class_name, file_path = match.groups()
        table_info[table_name] = (class_name, file_path.strip())

    # 处理每个表
    updated_count = 0
    failed_count = 0
    skipped_count = 0

    for table_name in tables:
        if table_name not in table_info:
            print(f"⚠️  未找到表信息: {table_name}")
            skipped_count += 1
            continue

        class_name, rel_file_path = table_info[table_name]
        file_path = PROJECT_ROOT / rel_file_path

        if not file_path.exists():
            print(f"⚠️  文件不存在: {file_path}")
            failed_count += 1
            continue

        result = add_tenant_to_model_file(file_path, table_name, class_name)
        if result:
            updated_count += 1
        elif result is False:
            skipped_count += 1
        else:
            failed_count += 1

    print("\n" + "=" * 80)
    print(f"✅ 处理完成!")
    print(f"   - 成功更新: {updated_count}")
    print(f"   - 跳过: {skipped_count}")
    print(f"   - 失败: {failed_count}")
    print("=" * 80)


if __name__ == "__main__":
    main()
