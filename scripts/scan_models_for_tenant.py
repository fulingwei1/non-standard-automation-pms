#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描所有数据模型，识别缺少 tenant_id 的核心业务表
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set

# 工作目录
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "app" / "models"

# 排除列表（基础设施表、枚举表等不需要租户隔离的表）
EXCLUDE_TABLES = {
    "tenants",  # 租户表本身
    "sessions",  # 会话表
    "login_attempts",  # 登录尝试（全局）
    "two_factor_secrets",  # 2FA密钥
    "two_factor_backup_codes",  # 2FA备份码
    "scheduler_config",  # 调度器配置
    "alembic_version",  # 迁移版本
}

# 排除的文件模式
EXCLUDE_FILES = {
    "__init__.py",
    "base.py",
    "enums.py",
    "encrypted_types.py",
}


class ModelScanner:
    """模型扫描器"""

    def __init__(self):
        self.models: List[Dict] = []
        self.tables_with_tenant: Set[str] = set()
        self.tables_without_tenant: Set[str] = set()

    def scan_file(self, file_path: Path):
        """扫描单个Python文件"""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # 检查是否是SQLAlchemy模型类
                    if self._is_model_class(node):
                        model_info = self._extract_model_info(node, file_path, content)
                        if model_info:
                            self.models.append(model_info)

        except Exception as e:
            print(f"⚠️  扫描文件失败 {file_path}: {e}")

    def _is_model_class(self, node: ast.ClassDef) -> bool:
        """判断是否是SQLAlchemy模型类"""
        # 检查是否继承自 Base
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Base":
                return True
        return False

    def _extract_model_info(self, node: ast.ClassDef, file_path: Path, content: str) -> Dict:
        """提取模型信息"""
        class_name = node.name
        table_name = None
        has_tenant_id = False
        relationships = []

        # 遍历类体
        for item in node.body:
            # 查找 __tablename__
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.name == "__tablename__":
                        if isinstance(item.value, ast.Constant):
                            table_name = item.value.value

            # 查找 Column 定义
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        col_name = target.name
                        if col_name == "tenant_id":
                            has_tenant_id = True

            # 查找 relationship 定义
            if isinstance(item, ast.Assign):
                if isinstance(item.value, ast.Call):
                    if isinstance(item.value.func, ast.Name):
                        if item.value.func.id == "relationship":
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    relationships.append(target.name)

        # 如果没有 __tablename__，跳过
        if not table_name:
            return None

        # 检查是否在排除列表
        if table_name in EXCLUDE_TABLES:
            return None

        # 记录到集合
        if has_tenant_id:
            self.tables_with_tenant.add(table_name)
        else:
            self.tables_without_tenant.add(table_name)

        return {
            "class_name": class_name,
            "table_name": table_name,
            "file_path": str(file_path.relative_to(PROJECT_ROOT)),
            "has_tenant_id": has_tenant_id,
            "relationships": relationships,
        }

    def scan_all_models(self):
        """扫描所有模型文件"""
        for root, dirs, files in os.walk(MODELS_DIR):
            # 跳过 __pycache__ 和 exports
            dirs[:] = [d for d in dirs if not d.startswith("__") and d != "exports"]

            for file in files:
                if not file.endswith(".py"):
                    continue
                if file in EXCLUDE_FILES:
                    continue

                file_path = Path(root) / file
                self.scan_file(file_path)

    def generate_report(self) -> str:
        """生成扫描报告"""
        lines = []
        lines.append("# 数据模型租户隔离扫描报告\n")
        lines.append(f"扫描时间: {os.popen('date').read().strip()}\n")
        lines.append("=" * 80 + "\n")

        # 统计
        total_tables = len(self.tables_with_tenant) + len(self.tables_without_tenant)
        lines.append(f"\n## 统计摘要\n")
        lines.append(f"- 总表数: {total_tables}\n")
        lines.append(f"- 已包含 tenant_id: {len(self.tables_with_tenant)}\n")
        lines.append(f"- 缺少 tenant_id: {len(self.tables_without_tenant)}\n")

        # 已包含 tenant_id 的表
        if self.tables_with_tenant:
            lines.append(f"\n## ✅ 已包含 tenant_id 的表 ({len(self.tables_with_tenant)})\n")
            for table in sorted(self.tables_with_tenant):
                lines.append(f"- {table}\n")

        # 缺少 tenant_id 的表（按模块分组）
        if self.tables_without_tenant:
            lines.append(
                f"\n## ⚠️  缺少 tenant_id 的核心业务表 ({len(self.tables_without_tenant)})\n"
            )

            # 按模块分组
            models_by_module = {}
            for model in self.models:
                if not model["has_tenant_id"] and model["table_name"] in self.tables_without_tenant:
                    file_path = model["file_path"]
                    # 提取模块名
                    if "production/" in file_path:
                        module = "生产管理"
                    elif "project/" in file_path:
                        module = "项目管理"
                    elif "sales/" in file_path:
                        module = "销售管理"
                    elif "approval/" in file_path:
                        module = "审批流程"
                    elif "business_support/" in file_path:
                        module = "商务支撑"
                    elif "performance/" in file_path:
                        module = "绩效管理"
                    elif "service/" in file_path:
                        module = "售后服务"
                    elif "shortage/" in file_path:
                        module = "缺料管理"
                    elif "strategy/" in file_path:
                        module = "战略管理"
                    elif "pmo/" in file_path:
                        module = "PMO管理"
                    elif "ecn/" in file_path:
                        module = "工程变更"
                    elif "engineer_performance/" in file_path:
                        module = "工程师绩效"
                    elif "ai_planning/" in file_path:
                        module = "AI规划"
                    else:
                        module = "核心模块"

                    if module not in models_by_module:
                        models_by_module[module] = []
                    models_by_module[module].append(model)

            # 输出分组结果
            for module in sorted(models_by_module.keys()):
                lines.append(f"\n### {module} ({len(models_by_module[module])})\n")
                for model in sorted(models_by_module[module], key=lambda x: x["table_name"]):
                    lines.append(
                        f"- `{model['table_name']}` ({model['class_name']}) - {model['file_path']}\n"
                    )

        # 详细模型信息
        lines.append(f"\n## 📊 完整模型清单\n")
        for model in sorted(self.models, key=lambda x: x["table_name"]):
            status = "✅" if model["has_tenant_id"] else "❌"
            lines.append(
                f"{status} `{model['table_name']}` - {model['class_name']} - {model['file_path']}\n"
            )

        return "".join(lines)


def main():
    """主函数"""
    print("🔍 开始扫描数据模型...")
    scanner = ModelScanner()
    scanner.scan_all_models()

    print(f"📊 扫描完成，共发现 {len(scanner.models)} 个模型")
    print(f"✅ 已包含 tenant_id: {len(scanner.tables_with_tenant)}")
    print(f"❌ 缺少 tenant_id: {len(scanner.tables_without_tenant)}")

    # 生成报告
    report = scanner.generate_report()
    report_path = PROJECT_ROOT / "data" / "tenant_scan_report.md"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"\n📝 报告已保存: {report_path}")

    # 输出缺少 tenant_id 的表清单（用于后续处理）
    if scanner.tables_without_tenant:
        tables_file = PROJECT_ROOT / "data" / "tables_need_tenant_id.txt"
        tables_file.write_text("\n".join(sorted(scanner.tables_without_tenant)), encoding="utf-8")
        print(f"📋 待处理表清单: {tables_file}")

    return scanner


if __name__ == "__main__":
    main()
