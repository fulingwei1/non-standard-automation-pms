#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成服务文件测试
自动分析服务文件结构，生成基础测试框架
"""

import ast
import json
from pathlib import Path
from typing import Dict, List


def load_zero_coverage_services() -> List[Dict]:
    """加载零覆盖率服务列表"""
    json_file = Path("reports/zero_coverage_services.json")
    if not json_file.exists():
        print("❌ 请先运行: python3 scripts/analyze_zero_coverage_services.py")
        return []

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("services", [])


def analyze_service_file(filepath: str) -> Dict:
    """分析服务文件结构"""
    service_path = Path(filepath)
    if not service_path.exists():
        return {}

    try:
        with open(service_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        analysis = {
            "classes": [],
            "functions": [],
            "imports": [],
            "has_init": False,
            "has_db_session": False,
            "dependencies": set(),
        }

        # 分析导入
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    analysis["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    analysis["imports"].append(full_name)
                    if "service" in full_name.lower():
                        analysis["dependencies"].add(full_name)

        # 分析类和函数（使用更安全的方式）
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)

                analysis["classes"].append(
                    {"name": node.name, "methods": methods, "is_service": "Service" in node.name}
                )

            elif isinstance(node, ast.FunctionDef):
                analysis["functions"].append(node.name)

        # 检查是否有 db_session 参数
        if "db" in content.lower() or "session" in content.lower():
            analysis["has_db_session"] = True

        # 检查是否有 __init__ 方法
        for cls in analysis["classes"]:
            if "__init__" in cls["methods"]:
                analysis["has_init"] = True
                break

        return analysis

    except Exception as e:
        print(f"⚠️  分析文件 {filepath} 时出错: {e}")
        return {}


def generate_test_file(service_info: Dict, analysis: Dict, batch_num: int = 1) -> str:
    """生成测试文件内容"""
    service_name = service_info["service_name"]
    filepath = service_info["filepath"]
    statements = service_info["statements"]

    # 确定服务类名
    service_class = None
    if analysis.get("classes"):
        # 找到 Service 类
        for cls in analysis["classes"]:
            if cls.get("is_service") or "Service" in cls["name"]:
                service_class = cls["name"]
                break
        if not service_class:
            service_class = analysis["classes"][0]["name"]

    # 生成导入语句
    imports = [
        "import pytest",
        "from unittest.mock import MagicMock, patch, Mock",
        "from datetime import datetime, date, timedelta",
        "from decimal import Decimal",
    ]

    if analysis.get("has_db_session"):
        imports.append("from sqlalchemy.orm import Session")

    # 添加服务导入
    module_path = filepath.replace("app/", "").replace(".py", "").replace("/", ".")
    if service_class:
        imports.append(f"from {module_path} import {service_class}")
    else:
        imports.append(f"import {module_path}")

    # 生成 fixture
    fixtures = []
    if service_class and analysis.get("has_db_session"):
        fixtures.append(
            f"""
@pytest.fixture
def {service_name}(db_session: Session):
    \"\"\"创建 {service_class} 实例\"\"\"
    return {service_class}(db_session)
"""
        )

    # 生成测试类
    test_class_name = (
        f"Test{service_class}"
        if service_class
        else f"Test{service_name.replace('_', ' ').title().replace(' ', '')}"
    )

    test_methods = []

    # 初始化测试
    if service_class:
        test_methods.append(
            f"""
    def test_init(self, db_session: Session):
        \"\"\"测试服务初始化\"\"\"
        service = {service_class}(db_session)
        assert service is not None
        if hasattr(service, 'db'):
            assert service.db == db_session
"""
        )

    # 为主要方法生成测试桩
    if analysis.get("classes") and service_class:
        for cls in analysis["classes"]:
            if cls["name"] == service_class:
                for method in cls["methods"]:
                    if method.startswith("_") or method == "__init__":
                        continue
                    test_methods.append(
                        f"""
    def test_{method}(self, {service_name if service_class else 'db_session'}):
        \"\"\"测试 {method} 方法\"\"\"
        # TODO: 实现测试逻辑
        # 1. 准备测试数据
        # 2. 调用方法
        # 3. 验证结果
        pass
"""
                    )

    # 为独立函数生成测试
    if analysis.get("functions"):
        for func in analysis["functions"]:
            if not func.startswith("_"):
                test_methods.append(
                    f"""
    def test_{func}(self):
        \"\"\"测试 {func} 函数\"\"\"
        # TODO: 实现测试逻辑
        from {module_path} import {func}
        pass
"""
                )

    # 组合测试文件内容
    test_content = f'''# -*- coding: utf-8 -*-
"""
Tests for {service_name} service
Covers: {filepath}
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: {statements} lines
Batch: {batch_num}
"""

{chr(10).join(imports)}


{chr(10).join(fixtures)}

class {test_class_name}:
    """Test suite for {service_class or service_name}."""
{chr(10).join(test_methods)}

    # TODO: 添加更多测试用例
    # - 正常流程测试 (Happy Path)
    # - 边界条件测试 (Edge Cases)
    # - 异常处理测试 (Error Handling)
    # - 数据验证测试 (Data Validation)
'''

    return test_content


def generate_tests_batch(batch_size: int = 10, start_index: int = 0):
    """批量生成测试文件"""
    services = load_zero_coverage_services()

    if not services:
        print("❌ 没有找到零覆盖率服务文件")
        return

    total = len(services)
    end_index = min(start_index + batch_size, total)
    batch_services = services[start_index:end_index]

    print(f"📝 生成第 {start_index + 1}-{end_index} 个服务的测试文件 (共 {total} 个)")

    output_dir = Path("tests/unit")
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = []
    skipped = []

    for i, service_info in enumerate(batch_services, start=start_index + 1):
        service_name = service_info["service_name"]
        filepath = service_info["filepath"]

        # 处理子目录结构（如 alert_rule_engine/condition_evaluator）
        if "/" in service_name:
            # 创建子目录
            subdir = output_dir / f"test_{service_name.split('/')[0]}"
            subdir.mkdir(parents=True, exist_ok=True)
            test_file = subdir / f"test_{service_name.split('/')[-1]}.py"
        else:
            test_file = output_dir / f"test_{service_name}.py"

        if test_file.exists():
            print(f"  ⏭️  {i:3d}. {service_name:50s} - 测试文件已存在")
            skipped.append(service_name)
            continue

        # 分析服务文件
        analysis = analyze_service_file(filepath)

        if not analysis:
            print(f"  ⚠️  {i:3d}. {service_name:50s} - 无法分析文件结构")
            skipped.append(service_name)
            continue

        # 生成测试文件
        try:
            test_content = generate_test_file(
                service_info, analysis, batch_num=(i // batch_size) + 1
            )

            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            print(f"  ✅ {i:3d}. {service_name:50s} - 已生成")
            generated.append(service_name)

        except Exception as e:
            print(f"  ❌ {i:3d}. {service_name:50s} - 生成失败: {e}")
            skipped.append(service_name)

    # 输出统计
    print(f"\n📊 生成统计:")
    print(f"  ✅ 成功生成: {len(generated)} 个")
    print(f"  ⏭️  跳过: {len(skipped)} 个")
    print(f"  📁 输出目录: {output_dir}")

    if generated:
        print(f"\n📝 下一步:")
        print(f"  1. 检查生成的测试文件")
        print(f"  2. 实现 TODO 标记的测试方法")
        print(f"  3. 运行测试: pytest tests/unit/test_{generated[0]}.py -v")
        print(
            f"  4. 检查覆盖率: pytest --cov=app/services/{generated[0]}.py --cov-report=term-missing"
        )


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="批量生成服务文件测试")
    parser.add_argument("--batch-size", type=int, default=10, help="每批生成的数量 (默认: 10)")
    parser.add_argument("--start", type=int, default=0, help="起始索引 (默认: 0)")
    parser.add_argument("--all", action="store_true", help="生成所有服务的测试文件")

    args = parser.parse_args()

    if args.all:
        services = load_zero_coverage_services()
        total = len(services)
        batch_size = args.batch_size

        for start in range(0, total, batch_size):
            generate_tests_batch(batch_size, start)
            print(f"\n{'='*60}\n")
    else:
        generate_tests_batch(args.batch_size, args.start)


if __name__ == "__main__":
    main()
