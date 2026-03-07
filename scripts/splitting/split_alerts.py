#!/usr/bin/env python3
"""
拆分 alerts.py 为模块化结构
"""
from pathlib import Path


def read_file_lines(file_path):
    """读取文件所有行"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def find_router_bounds(lines, router_start_line):
    """找到路由函数的结束行"""
    # 从路由定义开始，找到下一个同级别或更高级别的路由/函数
    indent_level = None
    for i in range(router_start_line, len(lines)):
        line = lines[i]
        # 跳过空行和注释
        if not line.strip() or line.strip().startswith("#"):
            continue
        # 找到第一个有实际内容的行，确定缩进级别
        if indent_level is None:
            indent_level = len(line) - len(line.lstrip())
        # 检查是否回到相同或更小的缩进级别
        if line.strip() and not line.strip().startswith("#"):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent_level:
                # 检查是否是新的路由或函数定义
                if (
                    line.strip().startswith("@router")
                    or line.strip().startswith("def ")
                    or line.strip().startswith("async def ")
                ):
                    return i
    return len(lines)


def extract_imports(lines):
    """提取导入语句"""
    imports = []
    for i, line in enumerate(lines):
        if line.strip().startswith("from ") or line.strip().startswith("import "):
            imports.append((i, line))
        elif line.strip().startswith("#") and i > 0:
            # 文档字符串后的注释可能相关
            continue
        elif line.strip().startswith('"""') or line.strip().startswith("'''"):
            continue
        elif imports and i > imports[-1][0] + 5:  # 导入应该在文件开头
            break
    return [line for _, line in imports]


def extract_section(lines, start_line, end_line):
    """提取指定行范围的代码"""
    return "".join(lines[start_line:end_line])


def main():
    source_file = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/alerts.py")
    output_dir = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/alerts")

    print("📖 读取 alerts.py...")
    lines = read_file_lines(source_file)

    # 提取导入
    imports = extract_imports(lines)
    imports_str = "\n".join(imports)

    # 定义各个模块的范围（行号-1，因为列表从0开始）
    modules = {
        "rules.py": (39, 267),  # 预警规则管理
        "records.py": (299, 577),  # 预警记录管理
        "notifications.py": (579, 690),  # 预警通知管理
        "exceptions.py": (696, 1085),  # 异常事件管理
        "statistics.py": (1136, 1595),  # 统计分析
        "subscriptions.py": (1597, 1913),  # 订阅管理
        "exports.py": (1957, 2232),  # 导出功能
    }

    # 为每个模块创建文件
    for module_name, (start, end) in modules.items():
        print(f"📝 生成 {module_name}...")

        # 提取模块代码
        module_code = extract_section(lines, start, end)

        # 获取所有路由装饰器
        module_lines = module_code.split("\n")
        routes = [line for line in module_lines if line.strip().startswith("@router")]

        # 确定路由前缀
        prefix = ""
        if "rules" in module_name:
            prefix = "/alert-rules"
        elif "records" in module_name or module_name == "alerts.py":
            prefix = "/alerts"
        elif "notifications" in module_name:
            prefix = "/alert-notifications"
        elif "exceptions" in module_name:
            prefix = "/exceptions"
        elif "statistics" in module_name:
            prefix = "/alerts/statistics"
        elif "subscriptions" in module_name:
            prefix = "/alerts/subscriptions"
        elif "exports" in module_name:
            prefix = "/alerts/export"

        # 生成模块文件内容
        module_content = f'''# -*- coding: utf-8 -*-
"""
{module_name.replace('.py', '').upper()} - 自动生成
从 alerts.py 拆分
"""

{imports_str}

from fastapi import APIRouter

router = APIRouter(
    prefix="{prefix}",
    tags=["{module_name.replace('.py', '')}"]
)

# ==================== 路由定义 ====================
# 共 {len(routes)} 个路由

{module_code}
'''

        # 写入文件
        output_path = output_dir / module_name
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(module_content)

        print(f"  ✅ {module_name}: {len(routes)} 个路由")

    print("\n✅ 拆分完成！")


if __name__ == "__main__":
    main()
