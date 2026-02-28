#!/usr/bin/env python3
"""
代码质量分析工具 - 分析大文件和大函数
"""

import os
import ast
import json
from pathlib import Path
from typing import List
from collections import defaultdict


class CodeAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.results = {
            "large_files": [],
            "large_functions": [],
            "summary": defaultdict(int),
        }

    def analyze(self):
        """分析代码库"""
        print("🔍 开始分析代码质量...\n")

        # 分析 Python 后端代码
        self.analyze_python_files()

        # 分析 JavaScript/JSX 前端代码
        self.analyze_js_files()

        # 生成报告
        self.generate_report()

    def analyze_python_files(self):
        """分析Python文件"""
        print("📊 分析 Python 后端代码...")

        # 排除目录
        exclude_dirs = {
            "node_modules",
            "venv",
            ".venv",
            "__pycache__",
            ".git",
            "htmlcov",
            "migrations",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "tests",
            "archives",
        }

        py_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # 过滤排除目录
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith(".py"):
                    filepath = Path(root) / file
                    py_files.append(filepath)

        for filepath in py_files:
            try:
                self.analyze_python_file(filepath)
            except Exception as e:
                print(f"  ⚠️  无法分析 {filepath}: {e}")

        print(f"  ✅ 分析了 {len(py_files)} 个 Python 文件\n")

    def analyze_python_file(self, filepath: Path):
        """分析单个Python文件"""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")
            line_count = len(lines)

        # 统计文件大小
        file_size = len(content)

        # 大文件阈值：500行或100KB
        if line_count > 500 or file_size > 100 * 1024:
            relative_path = filepath.relative_to(self.root_dir)
            self.results["large_files"].append(
                {
                    "type": "Python",
                    "path": str(relative_path),
                    "lines": line_count,
                    "size_kb": round(file_size / 1024, 2),
                }
            )
            self.results["summary"]["large_py_files"] += 1

        # 分析函数大小
        try:
            tree = ast.parse(content, filename=str(filepath))
            self.analyze_ast(tree, filepath, lines)
        except SyntaxError:
            pass  # 跳过语法错误的文件

    def analyze_ast(self, tree: ast.AST, filepath: Path, lines: List[str]):
        """分析AST以查找大函数"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = self.get_function_lines(node, lines)

                # 大函数阈值：100行
                if func_lines > 100:
                    relative_path = filepath.relative_to(self.root_dir)

                    # 获取函数的复杂度（参数数量）
                    param_count = len(node.args.args)

                    self.results["large_functions"].append(
                        {
                            "type": "Python",
                            "path": str(relative_path),
                            "function": node.name,
                            "lines": func_lines,
                            "start_line": node.lineno,
                            "params": param_count,
                        }
                    )
                    self.results["summary"]["large_py_functions"] += 1

    def get_function_lines(self, node: ast.FunctionDef, lines: List[str]) -> int:
        """计算函数的行数"""
        if hasattr(node, "end_lineno") and node.end_lineno:
            return node.end_lineno - node.lineno + 1
        return 0

    def analyze_js_files(self):
        """分析JavaScript/JSX文件"""
        print("📊 分析 JavaScript/JSX 前端代码...")

        # 排除目录
        exclude_dirs = {
            "node_modules",
            "dist",
            "build",
            ".git",
            "htmlcov",
            "coverage",
            "e2e",
        }

        js_files = []
        frontend_dir = self.root_dir / "frontend"

        if not frontend_dir.exists():
            print("  ⚠️  未找到 frontend 目录\n")
            return

        for root, dirs, files in os.walk(frontend_dir):
            # 过滤排除目录
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith((".js", ".jsx", ".ts", ".tsx")):
                    filepath = Path(root) / file
                    js_files.append(filepath)

        for filepath in js_files:
            try:
                self.analyze_js_file(filepath)
            except Exception as e:
                print(f"  ⚠️  无法分析 {filepath}: {e}")

        print(f"  ✅ 分析了 {len(js_files)} 个 JavaScript/JSX/TS 文件\n")

    def analyze_js_file(self, filepath: Path):
        """分析单个JavaScript文件"""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            lines = content.split("\n")
            line_count = len(lines)

        file_size = len(content)

        # 大文件阈值：500行或100KB
        if line_count > 500 or file_size > 100 * 1024:
            relative_path = filepath.relative_to(self.root_dir)
            self.results["large_files"].append(
                {
                    "type": "JavaScript",
                    "path": str(relative_path),
                    "lines": line_count,
                    "size_kb": round(file_size / 1024, 2),
                }
            )
            self.results["summary"]["large_js_files"] += 1

        # 简单的函数检测（基于正则表达式）
        self.analyze_js_functions(filepath, lines)

    def analyze_js_functions(self, filepath: Path, lines: List[str]):
        """分析JavaScript函数"""
        current_function = None
        function_start = -1
        brace_count = 0
        in_function = False

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # 检测函数定义
            if not in_function:
                # function 声明
                if "function " in line and "(" in line:
                    func_name = self.extract_function_name(line, "function")
                    if func_name:
                        current_function = func_name
                        function_start = i
                        in_function = True
                        brace_count = 0
                # 箭头函数和方法
                elif "=>" in line or (
                    "(" in line
                    and "{" in line
                    and ("const " in line or "let " in line or "var " in line)
                ):
                    func_name = self.extract_function_name(line, "arrow")
                    if func_name:
                        current_function = func_name
                        function_start = i
                        in_function = True
                        brace_count = 0
                # React组件
                elif "export default function" in line or "export function" in line:
                    func_name = self.extract_function_name(line, "export")
                    if func_name:
                        current_function = func_name
                        function_start = i
                        in_function = True
                        brace_count = 0

            # 计算大括号层级
            if in_function:
                brace_count += line.count("{") - line.count("}")

                # 函数结束
                if brace_count == 0 and "{" in lines[function_start - 1 : i]:
                    func_lines = i - function_start + 1

                    # 大函数阈值：100行
                    if func_lines > 100:
                        relative_path = filepath.relative_to(self.root_dir)
                        self.results["large_functions"].append(
                            {
                                "type": "JavaScript",
                                "path": str(relative_path),
                                "function": current_function,
                                "lines": func_lines,
                                "start_line": function_start,
                                "params": None,  # JS函数参数较难精确统计
                            }
                        )
                        self.results["summary"]["large_js_functions"] += 1

                    in_function = False
                    current_function = None

    def extract_function_name(self, line: str, func_type: str) -> str:
        """提取函数名"""
        try:
            if func_type == "function":
                # function foo() 或 function* foo()
                parts = line.split("function")
                if len(parts) > 1:
                    name_part = parts[1].strip()
                    if name_part.startswith("*"):
                        name_part = name_part[1:].strip()
                    name = name_part.split("(")[0].strip()
                    return name if name else "anonymous"
            elif func_type == "arrow":
                # const foo = () => {} 或 const foo = async () => {}
                if "const " in line:
                    name = line.split("const ")[1].split("=")[0].strip()
                    return name
                elif "let " in line:
                    name = line.split("let ")[1].split("=")[0].strip()
                    return name
            elif func_type == "export":
                # export default function Foo() 或 export function foo()
                parts = line.split("function")
                if len(parts) > 1:
                    name = parts[1].strip().split("(")[0].strip()
                    return name if name else "default"
        except:
            pass
        return None

    def generate_report(self):
        """生成报告"""
        print("\n" + "=" * 80)
        print("📋 代码质量分析报告")
        print("=" * 80 + "\n")

        # 摘要
        print("📊 总体统计")
        print("-" * 80)
        print(f"大文件 (Python):     {self.results['summary']['large_py_files']} 个")
        print(f"大文件 (JavaScript): {self.results['summary']['large_js_files']} 个")
        print(
            f"大函数 (Python):     {self.results['summary']['large_py_functions']} 个"
        )
        print(
            f"大函数 (JavaScript): {self.results['summary']['large_js_functions']} 个"
        )
        print()

        # 大文件详情
        if self.results["large_files"]:
            print("\n📁 大文件列表 (>500行 或 >100KB)")
            print("-" * 80)

            # 按类型分组
            py_files = [f for f in self.results["large_files"] if f["type"] == "Python"]
            js_files = [
                f for f in self.results["large_files"] if f["type"] == "JavaScript"
            ]

            if py_files:
                print("\n🐍 Python 后端:")
                py_files.sort(key=lambda x: x["lines"], reverse=True)
                for f in py_files[:20]:  # 只显示前20个
                    print(f"  • {f['path']}")
                    print(f"    行数: {f['lines']} | 大小: {f['size_kb']} KB")

            if js_files:
                print("\n  JavaScript 前端:")
                js_files.sort(key=lambda x: x["lines"], reverse=True)
                for f in js_files[:20]:  # 只显示前20个
                    print(f"  • {f['path']}")
                    print(f"    行数: {f['lines']} | 大小: {f['size_kb']} KB")

        # 大函数详情
        if self.results["large_functions"]:
            print("\n\n🔧 大函数列表 (>100行)")
            print("-" * 80)

            # 按类型分组
            py_funcs = [
                f for f in self.results["large_functions"] if f["type"] == "Python"
            ]
            js_funcs = [
                f for f in self.results["large_functions"] if f["type"] == "JavaScript"
            ]

            if py_funcs:
                print("\n🐍 Python 后端:")
                py_funcs.sort(key=lambda x: x["lines"], reverse=True)
                for f in py_funcs[:30]:  # 只显示前30个
                    print(f"  • {f['function']}() in {f['path']}")
                    print(
                        f"    行数: {f['lines']} | 起始行: {f['start_line']} | 参数: {f['params']}"
                    )

            if js_funcs:
                print("\n⚛️  JavaScript 前端:")
                js_funcs.sort(key=lambda x: x["lines"], reverse=True)
                for f in js_funcs[:30]:  # 只显示前30个
                    print(f"  • {f['function']}() in {f['path']}")
                    print(f"    行数: {f['lines']} | 起始行: {f['start_line']}")

        # 建议
        print("\n\n💡 优化建议")
        print("-" * 80)
        print("1. 大文件拆分: 将超过500行的文件拆分为多个模块")
        print("2. 大函数重构: 将超过100行的函数拆分为更小的函数")
        print("3. 单一职责原则: 确保每个函数只做一件事")
        print("4. 提取公共逻辑: 将重复代码提取为独立函数")
        print("5. 代码复用: 使用继承、组合等方式提高代码复用率")
        print()

        # 保存JSON报告
        report_path = self.root_dir / "code_quality_analysis_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"📄 详细报告已保存至: {report_path}")
        print()


if __name__ == "__main__":
    analyzer = CodeAnalyzer("/Users/flw/non-standard-automation-pm")
    analyzer.analyze()
