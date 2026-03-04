#!/usr/bin/env python3
"""
SQLAlchemy Relationship 自动修复脚本
根据验证报告自动修复P0级别问题
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict


class RelationshipFixer:
    def __init__(self, issues_file: str, dry_run: bool = False):
        self.issues_file = Path(issues_file)
        self.dry_run = dry_run
        self.issues = []
        self.fixes_applied = []
        self.load_issues()

    def load_issues(self):
        """加载问题报告"""
        with open(self.issues_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 只处理P0问题
            self.issues = [i for i in data["issues"] if i["severity"] == "P0"]
        print(f"📋 加载了 {len(self.issues)} 个P0问题")

    def backup_file(self, file_path: Path):
        """备份文件"""
        if not self.dry_run:
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            shutil.copy2(file_path, backup_path)
            print(f"  💾 备份: {backup_path}")

    def fix_all(self):
        """修复所有问题"""
        print("\n🔧 开始修复...\n")

        # 按类型分组处理
        for issue in self.issues:
            issue_type = issue["type"]

            if issue_type == "class_name_conflict":
                self.fix_class_name_conflict(issue)
            elif issue_type == "back_populates_asymmetry":
                self.fix_back_populates_asymmetry(issue)
            elif issue_type == "missing_foreign_keys":
                self.fix_missing_foreign_keys(issue)

        print(f"\n✅ 完成！共应用 {len(self.fixes_applied)} 个修复")

    def fix_class_name_conflict(self, issue: Dict):
        """修复类名冲突 - 手动处理，只记录"""
        print(f"⚠️  类名冲突: {issue['class']}")
        print(f"   涉及文件: {issue['files']}")
        print(f"   需要手动重命名其中一个类")
        self.fixes_applied.append(
            {"type": "class_name_conflict", "status": "manual_required", "issue": issue}
        )

    def fix_back_populates_asymmetry(self, issue: Dict):
        """修复back_populates不对称"""
        model = issue["model"]
        relationship_attr = issue["relationship"]
        target_model = issue["target_model"]
        expected_back_populates = issue["expected_back_populates"]
        file_path = Path(issue["file"])

        print(f"🔧 修复 {model}.{relationship_attr} -> {target_model}.{expected_back_populates}")

        # 找到目标模型文件
        target_file = self._find_model_file(target_model)
        if not target_file:
            print(f"  ❌ 找不到目标模型文件: {target_model}")
            self.fixes_applied.append(
                {
                    "type": "back_populates_asymmetry",
                    "status": "failed",
                    "reason": "target_file_not_found",
                    "issue": issue,
                }
            )
            return

        # 读取目标文件
        content = target_file.read_text(encoding="utf-8")

        # 找到目标类定义
        class_pattern = rf"class {target_model}\([^)]+\):"
        class_match = re.search(class_pattern, content)

        if not class_match:
            print(f"  ❌ 找不到类定义: {target_model}")
            self.fixes_applied.append(
                {
                    "type": "back_populates_asymmetry",
                    "status": "failed",
                    "reason": "class_not_found",
                    "issue": issue,
                }
            )
            return

        # 检查是否已经存在该relationship
        existing_rel_pattern = rf"{expected_back_populates}\s*=\s*relationship\s*\("
        if re.search(existing_rel_pattern, content):
            print(f"  ℹ️  关系已存在: {expected_back_populates}")
            self.fixes_applied.append(
                {"type": "back_populates_asymmetry", "status": "already_exists", "issue": issue}
            )
            return

        # 找到类的最后一个属性定义位置（插入新的relationship）
        # 策略：在类定义中找到最后一个赋值语句的位置
        class_start = class_match.end()

        # 找到下一个类定义或文件结束
        next_class_match = re.search(r"\nclass\s+\w+\s*\([^)]+\):", content[class_start:])
        if next_class_match:
            class_end = class_start + next_class_match.start()
        else:
            class_end = len(content)

        class_body = content[class_start:class_end]

        # 找到最后一个缩进的赋值行
        lines = class_body.split("\n")
        insert_line_idx = -1
        for i, line in enumerate(lines):
            if line.strip() and (line.startswith("    ") or line.startswith("\t")):
                if "=" in line and not line.strip().startswith("#"):
                    insert_line_idx = i

        if insert_line_idx == -1:
            print(f"  ❌ 找不到合适的插入位置")
            self.fixes_applied.append(
                {
                    "type": "back_populates_asymmetry",
                    "status": "failed",
                    "reason": "no_insert_position",
                    "issue": issue,
                }
            )
            return

        # 生成新的relationship代码
        indent = "    "  # 标准4空格缩进

        # 判断是否需要foreign_keys参数（检查原始relationship是否有）
        source_file_content = Path(issue["file"]).read_text(encoding="utf-8")
        source_rel_pattern = rf"{relationship_attr}\s*=\s*relationship\([^)]+\)"
        source_rel_match = re.search(source_rel_pattern, source_file_content)

        has_foreign_keys = False
        if source_rel_match:
            has_foreign_keys = "foreign_keys" in source_rel_match.group(0)

        if has_foreign_keys:
            # 需要猜测外键列名（通常是 target_model_id）
            fk_guess = f"{model.lower()}_id"
            new_relationship = f"{indent}{expected_back_populates} = relationship('{model}', foreign_keys=[{fk_guess}], back_populates='{relationship_attr}')\n"
            warning = f"{indent}# ⚠️ 请验证 foreign_keys 参数是否正确\n"
            new_code = warning + new_relationship
        else:
            new_relationship = f"{indent}{expected_back_populates} = relationship('{model}', back_populates='{relationship_attr}')\n"
            new_code = new_relationship

        # 插入代码
        insert_position = class_start + sum(len(line) + 1 for line in lines[: insert_line_idx + 1])
        new_content = content[:insert_position] + new_code + content[insert_position:]

        # 保存修复
        if not self.dry_run:
            self.backup_file(target_file)
            target_file.write_text(new_content, encoding="utf-8")
            print(f"  ✅ 已修复: {target_file}")
        else:
            print(f"  🔍 [DRY RUN] 将修复: {target_file}")
            print(f"     添加: {new_code.strip()}")

        self.fixes_applied.append(
            {
                "type": "back_populates_asymmetry",
                "status": "success",
                "file": str(target_file),
                "code_added": new_code,
                "issue": issue,
            }
        )

    def fix_missing_foreign_keys(self, issue: Dict):
        """修复缺少foreign_keys参数"""
        model = issue["model"]
        relationship_attr = issue["relationship"]
        available_fks = issue["available_fks"]
        file_path = Path(issue["file"])

        print(f"🔧 修复 {model}.{relationship_attr} - 添加 foreign_keys 参数")
        print(f"   可用外键: {available_fks}")

        content = file_path.read_text(encoding="utf-8")

        # 找到该relationship定义
        rel_pattern = rf"({relationship_attr}\s*=\s*relationship\s*\([^)]+)\)"
        match = re.search(rel_pattern, content)

        if not match:
            print(f"  ❌ 找不到relationship定义")
            self.fixes_applied.append(
                {
                    "type": "missing_foreign_keys",
                    "status": "failed",
                    "reason": "relationship_not_found",
                    "issue": issue,
                }
            )
            return

        # 选择第一个外键（或让用户选择）
        chosen_fk = available_fks[0]

        # 添加foreign_keys参数
        original = match.group(0)
        modified = match.group(1) + f", foreign_keys=[{chosen_fk}])"

        new_content = content.replace(original, modified)

        if not self.dry_run:
            self.backup_file(file_path)
            file_path.write_text(new_content, encoding="utf-8")
            print(f"  ✅ 已修复: {file_path}")
        else:
            print(f"  🔍 [DRY RUN] 将修复: {file_path}")
            print(f"     从: {original}")
            print(f"     到: {modified}")

        self.fixes_applied.append(
            {
                "type": "missing_foreign_keys",
                "status": "success",
                "file": str(file_path),
                "chosen_fk": chosen_fk,
                "issue": issue,
            }
        )

    def _find_model_file(self, model_name: str) -> Path:
        """查找模型文件"""
        models_dir = Path(__file__).parent.parent / "app" / "models"

        # 遍历所有Python文件
        for py_file in models_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            # 查找类定义
            pattern = rf"class {model_name}\s*\([^)]+\):"
            if re.search(pattern, content):
                return py_file

        return None

    def generate_report(self, output_file: Path):
        """生成修复报告"""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# SQLAlchemy Relationship 修复报告\n\n")
            f.write(f"生成时间: {datetime.now()}\n\n")

            f.write("## 修复统计\n\n")
            total = len(self.fixes_applied)
            success = len([f for f in self.fixes_applied if f["status"] == "success"])
            failed = len([f for f in self.fixes_applied if f["status"] == "failed"])
            manual = len([f for f in self.fixes_applied if f["status"] == "manual_required"])
            already_exists = len([f for f in self.fixes_applied if f["status"] == "already_exists"])

            f.write(f"- 总计: {total}\n")
            f.write(f"- 成功: {success}\n")
            f.write(f"- 失败: {failed}\n")
            f.write(f"- 需手动处理: {manual}\n")
            f.write(f"- 已存在: {already_exists}\n\n")

            # 详细列表
            f.write("## 修复详情\n\n")
            for i, fix in enumerate(self.fixes_applied, 1):
                f.write(f"### 修复 {i}: {fix['type']} - {fix['status']}\n\n")

                if fix["type"] == "back_populates_asymmetry":
                    issue = fix["issue"]
                    f.write(f"**模型**: {issue['model']}.{issue['relationship']}\n\n")
                    f.write(
                        f"**目标**: {issue['target_model']}.{issue['expected_back_populates']}\n\n"
                    )

                    if fix["status"] == "success":
                        f.write(f"**文件**: `{fix['file']}`\n\n")
                        f.write("**添加代码**:\n```python\n")
                        f.write(fix["code_added"])
                        f.write("```\n\n")
                    elif fix["status"] == "failed":
                        f.write(f"**失败原因**: {fix.get('reason', 'unknown')}\n\n")

                elif fix["type"] == "class_name_conflict":
                    issue = fix["issue"]
                    f.write(f"**类名**: {issue['class']}\n\n")
                    f.write(f"**涉及文件**:\n")
                    for file in issue["files"]:
                        f.write(f"- `{file}`\n")
                    f.write("\n**操作**: 需要手动重命名其中一个类\n\n")

                elif fix["type"] == "missing_foreign_keys":
                    issue = fix["issue"]
                    f.write(f"**模型**: {issue['model']}.{issue['relationship']}\n\n")
                    if fix["status"] == "success":
                        f.write(f"**选择的外键**: {fix['chosen_fk']}\n\n")
                        f.write(f"**文件**: `{fix['file']}`\n\n")

        print(f"\n📄 修复报告: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="修复SQLAlchemy relationship问题")
    parser.add_argument("--auto-fix", action="store_true", help="自动修复（默认是dry-run）")
    parser.add_argument(
        "--issues-file", default="data/sqlalchemy_relationship_issues.json", help="问题报告文件路径"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    issues_file = project_root / args.issues_file

    if not issues_file.exists():
        print(f"❌ 问题报告不存在: {issues_file}")
        print("   请先运行: python3 scripts/validate_sqlalchemy_relationships.py")
        return

    dry_run = not args.auto_fix

    if dry_run:
        print("🔍 DRY RUN 模式 - 不会实际修改文件")
        print("   使用 --auto-fix 参数来应用修复\n")

    fixer = RelationshipFixer(issues_file, dry_run=dry_run)
    fixer.fix_all()

    # 生成报告
    report_file = project_root / "data" / "sqlalchemy_fixes_applied.md"
    fixer.generate_report(report_file)


if __name__ == "__main__":
    main()
