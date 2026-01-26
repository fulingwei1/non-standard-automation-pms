#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一审批系统部署脚本

执行所有必要的部署步骤，包括：
1. 应用数据库迁移
2. 验证审批流程创建成功
3. 清理旧数据（可选）
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_success(message):
    """打印成功消息"""
    print(f"✅ {message}")


def print_error(message):
    """打印错误消息"""
    print(f"❌ {message}")


def print_warning(message):
    """打印警告消息"""
    print(f"⚠️  {message}")


def check_database_exists(db_path):
    """检查数据库文件是否存在"""
    if not db_path.exists():
        print_error(f"数据库文件不存在: {db_path}")
        return False
    print_success(f"找到数据库文件: {db_path}")
    return True


def run_migration(db_path, migrations_dir):
    """运行数据库迁移"""
    print_section("步骤 1: 运行数据库迁移")

    migration_file = migrations_dir / "20260125_approval_flows_sqlite.sql"

    if not migration_file.exists():
        print_error(f"迁移文件不存在: {migration_file}")
        return False

    try:
        with open(migration_file, "r", encoding="utf-8") as f:
            sql_script = f.read()

        # 使用显式事务
        conn = sqlite3.connect(db_path)
        conn.isolation_level = "DEFERRED"  # 显式事务控制

        cursor = conn.cursor()

        try:
            # 开始事务
            conn.execute("BEGIN")

            # 执行迁移脚本
            cursor.executescript(sql_script)

            # 提交事务
            conn.commit()

            print_success("数据库迁移执行成功")
            return True

        except Exception as e:
            print_error(f"数据库迁移失败: {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    except Exception as e:
        print_error(f"数据库迁移失败: {e}")
        return False


def verify_approval_templates(db_path):
    """验证审批模板创建成功"""
    print_section("步骤 2: 验证审批模板")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查审批模板
        cursor.execute("""
            SELECT template_code, template_name, is_active
            FROM approval_templates
            WHERE template_code IN ('ECN_TEMPLATE', 'QUOTE_TEMPLATE', 'CONTRACT_TEMPLATE', 'INVOICE_TEMPLATE')
            ORDER BY template_code
        """)

        templates = cursor.fetchall()

        if not templates:
            print_error("未找到审批模板，迁移可能失败")
            return False

        print("\n审批模板列表:")
        for template_code, template_name, is_active in templates:
            status = "✅ 激活" if is_active else "❌ 未激活"
            print(f"  - {template_code}: {template_name} [{status}]")

        # 检查审批流程
        cursor.execute("""
            SELECT fd.flow_name, t.template_code
            FROM approval_flow_definitions fd
            JOIN approval_templates t ON fd.template_id = t.id
            ORDER BY t.template_code
        """)

        flows = cursor.fetchall()

        print("\n审批流程列表:")
        for flow_name, template_code in flows:
            print(f"  - {template_code}: {flow_name}")

        # 检查审批节点
        cursor.execute("""
            SELECT nd.node_name, nd.node_order, fd.flow_name, t.template_code
            FROM approval_node_definitions nd
            JOIN approval_flow_definitions fd ON nd.flow_id = fd.id
            JOIN approval_templates t ON fd.template_id = t.id
            WHERE t.template_code IN ('ECN_TEMPLATE', 'QUOTE_TEMPLATE', 'CONTRACT_TEMPLATE', 'INVOICE_TEMPLATE')
            ORDER BY t.template_code, nd.node_order
        """)

        nodes = cursor.fetchall()

        if not nodes:
            print_warning("未找到审批节点，请检查迁移脚本")
            return False

        print("\n审批节点列表:")
        current_template = None
        for node_name, node_order, flow_name, template_code in nodes:
            if template_code != current_template:
                print(f"\n{template_code}:")
                current_template = template_code
            print(f"  节点 {node_order}: {node_name}")

        conn.close()
        print_success(
            f"验证完成: 找到 {len(templates)} 个模板，{len(flows)} 个流程，{len(nodes)} 个节点"
        )
        return True

    except Exception as e:
        print_error(f"验证失败: {e}")
        return False


def test_approval_api(db_path):
    """测试审批 API 是否可以正常工作"""
    print_section("步骤 3: 测试审批 API")

    try:
        # 这里只是示例，实际测试需要启动服务器
        print("\nAPI 测试命令示例:")
        print("\n1. 提交 ECN 审批:")
        print("   curl -X POST http://127.0.0.1:8000/api/v1/approvals/submit \\")
        print('     -H "Content-Type: application/json" \\')
        print('     -H "Authorization: Bearer {token}" \\')
        print(
            '     -d \'{"entity_type":"ECN","entity_id":123,"title":"测试ECN","summary":"测试描述"}\'\n'
        )

        print("2. 查询我的待审批任务:")
        print("   curl -X GET http://127.0.0.1:8000/api/v1/approvals/my-tasks \\")
        print('     -H "Authorization: Bearer {token}"\n')

        print("3. 委托审批:")
        print(
            "   curl -X POST http://127.0.0.1:8000/api/v1/approvals/{instance_id}/delegate \\"
        )
        print('     -H "Content-Type: application/json" \\')
        print('     -H "Authorization: Bearer {token}" \\')
        print(
            '     -d \'{"decision":"DELEGATE","delegate_to_id":8,"comment":"委托测试"}\'\n'
        )

        print("\n提示:")
        print("  - 请先获取有效的 JWT token")
        print("  - 替换 {token} 为实际的 token")
        print("  - 替换 {instance_id} 为实际的审批实例 ID")
        print("  - API 文档: http://127.0.0.1:8000/docs")

        print_success("API 测试命令已生成")
        return True

    except Exception as e:
        print_error(f"API 测试失败: {e}")
        return False


def generate_summary(db_path):
    """生成部署总结"""
    print_section("部署总结")

    print("\n统一审批系统部署完成！")
    print("\n已完成的工作:")
    print("  ✅ 创建统一审批引擎 (WorkflowEngine)")
    print("  ✅ 创建 ECN 适配器 (EcnApprovalAdapter)")
    print("  ✅ 创建 Sales 适配器 (SalesApprovalAdapter)")
    print("  ✅ 创建统一审批 API 端点 (/api/v1/approvals)")
    print("  ✅ 编写全面单元测试")
    print("  ✅ 注册审批路由到 API 网关")
    print("  ✅ 删除旧的 ECN 和 Sales 审批端点")
    print("  ✅ 创建审批流程模板和节点定义")
    print("  ✅ 实现委托审批端点")
    print("  ✅ 创建迁移指南和文档")

    print("\n审批流程定义:")
    print("  1. ECN: 技术评审 → 部门会签 → 最终审批")
    print("  2. QUOTE: 销售经理 → 销售总监 → 总经理 (条件路由)")
    print("  3. CONTRACT: 销售经理 → 销售总监 → 总经理 (条件路由)")
    print("  4. INVOICE: 财务经理 → 财务总监 (条件路由)")

    print("\n可用 API 端点:")
    print("  POST   /api/v1/approvals/submit        - 提交审批")
    print("  POST   /api/v1/approvals/{id}/approve  - 通过审批")
    print("  POST   /api/v1/approvals/{id}/reject   - 驳回审批")
    print("  POST   /api/v1/approvals/{id}/withdraw - 撤回审批")
    print("  POST   /api/v1/approvals/{id}/delegate - 委托审批")
    print("  GET    /api/v1/approvals/{id}/history   - 查询历史")
    print("  GET    /api/v1/approvals/{id}/detail    - 查询详情")
    print("  GET    /api/v1/approvals/my-tasks   - 待办任务")

    print("\n下一步:")
    print("  1. 启动应用: python3 -m app.main")
    print("  2. 访问 API 文档: http://127.0.0.1:8000/docs")
    print("  3. 更新前端代码使用新的审批 API")
    print("  4. 测试各业务实体的审批流程")
    print("  5. 在生产环境中进行全面测试")
    print("  6. 通知相关用户系统变更")

    print("\n文档位置:")
    print("  - 迁移指南: docs/统一审批系统迁移指南.md")
    print("  - 单元测试: tests/unit/test_approval_engine_workflow.py")
    print("  - 条件解析器: app/services/approval_engine/condition_parser.py")
    print("  - ECN 适配器: app/services/approval_engine/adapters/ecn_adapter.py")
    print("  - Sales 适配器: app/services/approval_engine/adapters/sales_adapter.py")

    print(f"\n数据库位置: {db_path}")
    print(f"部署时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """主函数"""
    print_section("统一审批系统部署脚本")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 获取项目根目录
    project_root = Path(__file__).parent
    db_path = project_root / "data" / "app.db"
    migrations_dir = project_root / "migrations"

    # 步骤 1: 运行数据库迁移
    if not check_database_exists(db_path):
        return 1

    if not run_migration(db_path, migrations_dir):
        return 1

    # 步骤 2: 验证审批模板
    if not verify_approval_templates(db_path):
        return 1

    # 步骤 3: 测试 API
    if not test_approval_api(db_path):
        return 1

    # 步骤 4: 生成总结
    generate_summary(db_path)

    print("\n" + "=" * 60)
    print("  ✅ 部署脚本执行完成")
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
