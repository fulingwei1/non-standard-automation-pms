#!/usr/bin/env python3
"""
SQLAlchemy Relationship Validator
扫描所有models，检测relationship配置问题
"""

import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict


class RelationshipValidator:
    def __init__(self, models_dir: str):
        self.models_dir = Path(models_dir)
        self.models = {}  # model_name -> {file, class_node, relationships}
        self.issues = []
        self.class_names = defaultdict(list)  # class_name -> [file_paths]

    def scan_models(self):
        """扫描所有model文件"""
        print(f"📂 扫描目录: {self.models_dir}")

        for py_file in self.models_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            self._parse_file(py_file)

        print(f"✅ 找到 {len(self.models)} 个模型类")

    def _parse_file(self, file_path: Path):
        """解析单个Python文件"""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # 检查是否是SQLAlchemy模型（继承Base或有__tablename__）
                    if self._is_model_class(node):
                        model_info = self._extract_model_info(node, file_path, content)
                        if model_info:
                            self.models[node.name] = model_info
                            self.class_names[node.name].append(str(file_path))
        except Exception as e:
            print(f"⚠️  解析 {file_path} 失败: {e}")

    def _is_model_class(self, node: ast.ClassDef) -> bool:
        """判断是否是SQLAlchemy模型类"""
        # 检查继承Base
        for base in node.bases:
            if isinstance(base, ast.Name) and hasattr(base, "id") and base.id == "Base":
                return True

        # 检查是否有__tablename__
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if (
                        isinstance(target, ast.Name)
                        and hasattr(target, "id")
                        and target.id == "__tablename__"
                    ):
                        return True
        return False

    def _extract_model_info(self, node: ast.ClassDef, file_path: Path, content: str) -> Dict:
        """提取模型信息"""
        relationships = []
        foreign_keys = []

        for item in node.body:
            # 提取relationship
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    # 只处理简单的变量赋值
                    if isinstance(target, ast.Name) and hasattr(target, "id"):
                        attr_name = target.id
                        rel_info = self._extract_relationship(item.value, attr_name)
                        if rel_info:
                            relationships.append(rel_info)

                        fk_info = self._extract_foreign_key(item.value)
                        if fk_info:
                            foreign_keys.append({"column": attr_name, "references": fk_info})

        return {
            "file": str(file_path),
            "class_node": node,
            "relationships": relationships,
            "foreign_keys": foreign_keys,
            "content": content,
        }

    def _extract_relationship(self, node, attr_name: str) -> Dict:
        """提取relationship信息"""
        if not isinstance(node, ast.Call):
            return None

        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name != "relationship":
            return None

        # 提取参数
        target_model = None
        back_populates = None
        foreign_keys_arg = None

        if node.args:
            if isinstance(node.args[0], ast.Constant):
                target_model = node.args[0].value
            elif isinstance(node.args[0], ast.Str):
                target_model = node.args[0].s

        for keyword in node.keywords:
            if keyword.arg == "back_populates":
                if isinstance(keyword.value, ast.Constant):
                    back_populates = keyword.value.value
                elif isinstance(keyword.value, ast.Str):
                    back_populates = keyword.value.s
            elif keyword.arg == "foreign_keys":
                foreign_keys_arg = (
                    ast.unparse(keyword.value) if hasattr(ast, "unparse") else "present"
                )

        return {
            "attr": attr_name,
            "target_model": target_model,
            "back_populates": back_populates,
            "foreign_keys": foreign_keys_arg,
        }

    def _extract_foreign_key(self, node) -> str:
        """提取ForeignKey信息"""
        if not isinstance(node, ast.Call):
            return None

        # 检查Column(... ForeignKey(...))
        if isinstance(node.func, ast.Name) and node.func.id == "Column":
            for arg in node.args:
                if isinstance(arg, ast.Call):
                    if isinstance(arg.func, ast.Name) and arg.func.id == "ForeignKey":
                        if arg.args:
                            if isinstance(arg.args[0], ast.Constant):
                                return arg.args[0].value
                            elif isinstance(arg.args[0], ast.Str):
                                return arg.args[0].s
        return None

    def validate(self):
        """执行所有验证"""
        print("\n🔍 开始验证...")

        self._check_class_name_conflicts()
        self._check_back_populates_symmetry()
        self._check_multiple_foreign_keys()
        self._check_missing_relationships()

        print(f"\n📊 验证完成，发现 {len(self.issues)} 个问题")

    def _check_class_name_conflicts(self):
        """检查类名冲突"""
        for class_name, files in self.class_names.items():
            if len(files) > 1:
                self.issues.append(
                    {
                        "severity": "P0",
                        "type": "class_name_conflict",
                        "class": class_name,
                        "files": files,
                        "message": f"类名冲突: {class_name} 在 {len(files)} 个文件中定义",
                    }
                )

    def _check_back_populates_symmetry(self):
        """检查back_populates对称性"""
        for model_name, model_info in self.models.items():
            for rel in model_info["relationships"]:
                if not rel["back_populates"]:
                    continue

                target_model = rel["target_model"]
                if target_model not in self.models:
                    continue

                target_info = self.models[target_model]
                # 查找对应的relationship
                found = False
                for target_rel in target_info["relationships"]:
                    if (
                        target_rel["attr"] == rel["back_populates"]
                        and target_rel["target_model"] == model_name
                        and target_rel["back_populates"] == rel["attr"]
                    ):
                        found = True
                        break

                if not found:
                    self.issues.append(
                        {
                            "severity": "P0",
                            "type": "back_populates_asymmetry",
                            "model": model_name,
                            "relationship": rel["attr"],
                            "target_model": target_model,
                            "expected_back_populates": rel["back_populates"],
                            "file": model_info["file"],
                            "message": f"{model_name}.{rel['attr']} 的 back_populates='{rel['back_populates']}' 在 {target_model} 中找不到对应关系",
                        }
                    )

    def _check_multiple_foreign_keys(self):
        """检查多外键路径是否指定foreign_keys参数"""
        for model_name, model_info in self.models.items():
            # 统计指向每个表的外键数量
            fk_targets = defaultdict(list)
            for fk in model_info["foreign_keys"]:
                # 提取表名（格式：table_name.column）
                if "." in fk["references"]:
                    table = fk["references"].split(".")[0]
                    fk_targets[table].append(fk["column"])

            # 检查有多个外键指向同一表的relationship
            for rel in model_info["relationships"]:
                target_model = rel["target_model"]
                if not target_model or target_model not in self.models:
                    continue

                # 获取目标表名
                target_info = self.models[target_model]
                target_tablename = self._get_tablename(target_info["class_node"])

                if target_tablename in fk_targets and len(fk_targets[target_tablename]) > 1:
                    if not rel["foreign_keys"]:
                        self.issues.append(
                            {
                                "severity": "P0",
                                "type": "missing_foreign_keys",
                                "model": model_name,
                                "relationship": rel["attr"],
                                "target_model": target_model,
                                "available_fks": fk_targets[target_tablename],
                                "file": model_info["file"],
                                "message": f"{model_name}.{rel['attr']} 有多个外键路径到 {target_model}，需要指定 foreign_keys 参数",
                            }
                        )

    def _check_missing_relationships(self):
        """检查缺失的relationship定义"""
        for model_name, model_info in self.models.items():
            for fk in model_info["foreign_keys"]:
                # 提取目标表名
                if "." not in fk["references"]:
                    continue

                target_table = fk["references"].split(".")[0]

                # 查找对应的relationship
                has_rel = any(
                    rel["target_model"]
                    and self._get_tablename_by_model(rel["target_model"]) == target_table
                    for rel in model_info["relationships"]
                )

                if not has_rel:
                    self.issues.append(
                        {
                            "severity": "P1",
                            "type": "missing_relationship",
                            "model": model_name,
                            "foreign_key": fk["column"],
                            "target_table": target_table,
                            "file": model_info["file"],
                            "message": f"{model_name} 有外键 {fk['column']} 指向 {target_table}，但没有对应的 relationship",
                        }
                    )

    def _get_tablename(self, class_node: ast.ClassDef) -> str:
        """提取__tablename__"""
        for item in class_node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if (
                        isinstance(target, ast.Name)
                        and hasattr(target, "id")
                        and target.id == "__tablename__"
                    ):
                        if isinstance(item.value, ast.Constant):
                            return item.value.value
                        elif isinstance(item.value, ast.Str):
                            return item.value.s
        return None

    def _get_tablename_by_model(self, model_name: str) -> str:
        """通过模型名获取表名"""
        if model_name in self.models:
            return self._get_tablename(self.models[model_name]["class_node"])
        return None

    def generate_reports(self, output_dir: Path):
        """生成报告"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # JSON报告
        json_path = output_dir / "sqlalchemy_relationship_issues.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "total_models": len(self.models),
                    "total_issues": len(self.issues),
                    "issues_by_severity": {
                        "P0": len([i for i in self.issues if i["severity"] == "P0"]),
                        "P1": len([i for i in self.issues if i["severity"] == "P1"]),
                        "P2": len([i for i in self.issues if i["severity"] == "P2"]),
                    },
                    "issues": self.issues,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"✅ JSON报告: {json_path}")

        # Markdown报告
        md_path = output_dir / "sqlalchemy_relationship_issues.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# SQLAlchemy Relationship 问题报告\n\n")
            f.write(f"生成时间: {__import__('datetime').datetime.now()}\n\n")
            f.write("## 统计\n\n")
            f.write(f"- 总计模型: {len(self.models)}\n")
            f.write(f"- 总计问题: {len(self.issues)}\n")

            p0 = [i for i in self.issues if i["severity"] == "P0"]
            p1 = [i for i in self.issues if i["severity"] == "P1"]
            p2 = [i for i in self.issues if i["severity"] == "P2"]

            f.write(f"  - P0 严重: {len(p0)} 个\n")
            f.write(f"  - P1 重要: {len(p1)} 个\n")
            f.write(f"  - P2 次要: {len(p2)} 个\n\n")

            # 按严重程度分组
            for severity, issues in [("P0", p0), ("P1", p1), ("P2", p2)]:
                if not issues:
                    continue

                f.write(f"## {severity} 问题\n\n")
                for i, issue in enumerate(issues, 1):
                    f.write(f"### {severity}-{i}: {issue['type']}\n\n")
                    f.write(f"**消息**: {issue['message']}\n\n")

                    for key, value in issue.items():
                        if key not in ["severity", "type", "message"]:
                            f.write(f"- **{key}**: `{value}`\n")
                    f.write("\n")

        print(f"✅ Markdown报告: {md_path}")

        # 控制台输出
        print("\n" + "=" * 60)
        print("📊 问题总结")
        print("=" * 60)
        print(f"总计models: {len(self.models)}")
        print(f"发现问题: {len(self.issues)}")
        print(f"  - P0严重: {len(p0)} (阻塞启动)")
        print(f"  - P1重要: {len(p1)} (潜在风险)")
        print(f"  - P2次要: {len(p2)} (优化建议)")
        print("=" * 60)


def main():
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "app" / "models"
    output_dir = project_root / "data"

    validator = RelationshipValidator(models_dir)
    validator.scan_models()
    validator.validate()
    validator.generate_reports(output_dir)


if __name__ == "__main__":
    main()
