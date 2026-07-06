#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 装饰器存在性扫描测试

此测试在 CI 中运行，确保:
1. 审计脚本可正确执行并生成结果
2. 关键安全指标不退化 (无保护端点数不增加, 权限覆盖率不下降)
3. 已知危险端点清单保持准确
4. 白名单路由数量不意外增长

这是一个"棘轮测试" — 只允许情况改善，不允许退化。
"""

import json
import os
import subprocess
import sys
import pytest
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent


class TestAuditScriptRunnable:
    """审计脚本基础可执行性"""

    def test_audit_script_exists(self):
        script = ROOT / "scripts" / "audit_permission_coverage.py"
        assert script.exists(), "审计脚本不存在"

    def test_audit_script_runs_without_error(self):
        """脚本应可正常执行并生成 JSON"""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_permission_coverage.py"), "--json-only"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=60,
        )
        assert result.returncode == 0, f"脚本执行失败: {result.stderr}"
        assert (ROOT / "PERMISSION_COVERAGE_AUDIT.json").exists()

    def test_json_output_valid(self):
        """生成的 JSON 应可解析且结构完整"""
        json_path = ROOT / "PERMISSION_COVERAGE_AUDIT.json"
        if not json_path.exists():
            pytest.skip("需要先运行审计脚本")

        with open(json_path) as f:
            data = json.load(f)

        assert "summary" in data
        assert "all_endpoints" in data
        assert "top20_risk" in data
        assert "module_breakdown" in data
        assert data["summary"]["total_endpoints"] > 0


class TestPermissionCoverageRatchet:
    """棘轮测试: 权限覆盖率只能改善，不能退化"""

    @pytest.fixture(autouse=True)
    def load_audit(self):
        json_path = ROOT / "PERMISSION_COVERAGE_AUDIT.json"
        if not json_path.exists():
            # 执行审计脚本
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "audit_permission_coverage.py"), "--json-only"],
                cwd=str(ROOT),
                timeout=60,
            )
        with open(json_path) as f:
            self.audit = json.load(f)

    # ── 基线值 (修正后口径) ────────────────────────────────────
    # 这些值基于当前审计结果，只允许改善
    BASELINE_MAX_NONE = 180          # NONE (完全无保护) 端点上限
    BASELINE_MIN_PERM_PCT = 25.0     # PERMISSION 覆盖率下限 (%)
    BASELINE_MAX_WRITE_NAKED = 860   # AUTH_ONLY+NONE 写端点上限

    def test_none_endpoints_not_increasing(self):
        """NONE 保护级别端点数不应增加"""
        none_count = self.audit["summary"]["by_protection"].get("NONE", 0)
        assert none_count <= self.BASELINE_MAX_NONE, (
            f"完全无保护端点增加到 {none_count} (基线: {self.BASELINE_MAX_NONE})。"
            f"新端点必须至少有 get_current_active_user 认证。"
        )

    def test_permission_coverage_not_declining(self):
        """PERMISSION 覆盖率不应下降"""
        pct = self.audit["summary"]["permission_coverage_pct"]
        assert pct >= self.BASELINE_MIN_PERM_PCT, (
            f"权限覆盖率下降到 {pct}% (基线: {self.BASELINE_MIN_PERM_PCT}%)。"
            f"新写操作端点必须添加 require_permission。"
        )

    def test_write_naked_not_increasing(self):
        """无权限码的写操作端点不应增加"""
        write_naked = 0
        for mod, stats in self.audit["module_breakdown"].items():
            write_naked += stats["write_unprotected"]
        assert write_naked <= self.BASELINE_MAX_WRITE_NAKED, (
            f"无权限码写端点增加到 {write_naked} (基线: {self.BASELINE_MAX_WRITE_NAKED})"
        )


class TestCriticalEndpointProtection:
    """关键端点必须有权限保护 (不允许退化为 AUTH_ONLY 或 NONE)"""

    @pytest.fixture(autouse=True)
    def load_audit(self):
        json_path = ROOT / "PERMISSION_COVERAGE_AUDIT.json"
        if not json_path.exists():
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "audit_permission_coverage.py"), "--json-only"],
                cwd=str(ROOT),
                timeout=60,
            )
        with open(json_path) as f:
            self.audit = json.load(f)
        # Build lookup: (file_module, method, function) -> protection
        self.endpoints = {}
        for ep in self.audit["all_endpoints"]:
            key = (ep["file"], ep["method"], ep["function"])
            self.endpoints[key] = ep

    def _find_endpoints_in_file(self, file_pattern, method=None):
        """在审计数据中查找匹配的端点"""
        results = []
        for ep in self.audit["all_endpoints"]:
            if file_pattern in ep["file"]:
                if method is None or ep["method"] == method:
                    results.append(ep)
        return results

    def test_user_crud_has_permission(self):
        """用户 CRUD 必须有 PERMISSION 级别保护"""
        user_writes = self._find_endpoints_in_file("users.py", "POST")
        user_writes += self._find_endpoints_in_file("users.py", "PUT")
        user_writes += self._find_endpoints_in_file("users.py", "DELETE")

        for ep in user_writes:
            assert ep["protection"] == "PERMISSION", (
                f"用户写端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )

    def test_role_crud_has_permission(self):
        """角色 CRUD 必须有 PERMISSION 级别保护"""
        role_writes = self._find_endpoints_in_file("roles/", "POST")
        role_writes += self._find_endpoints_in_file("roles/", "PUT")
        role_writes += self._find_endpoints_in_file("roles/", "DELETE")

        for ep in role_writes:
            assert ep["protection"] == "PERMISSION", (
                f"角色写端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )

    def test_permission_crud_has_permission(self):
        """权限管理 CRUD 必须有 PERMISSION 级别保护"""
        perm_writes = self._find_endpoints_in_file("permissions/", "POST")
        perm_writes += self._find_endpoints_in_file("permissions/", "PUT")
        perm_writes += self._find_endpoints_in_file("permissions/", "DELETE")

        for ep in perm_writes:
            assert ep["protection"] == "PERMISSION", (
                f"权限管理写端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )

    def test_super_admin_dependency_counts_as_permission(self):
        """deps.require_super_admin 应计入 PERMISSION，避免租户管理误报裸奔。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(str(ROOT / "app/api/v1/endpoints/tenants.py"))
        tenant_writes = [
            ep for ep in endpoints if ep["method"] in {"POST", "PUT", "DELETE"}
        ]

        assert tenant_writes
        assert all(ep["protection"] == "PERMISSION" for ep in tenant_writes)

    def test_router_level_permission_dependency_counts_for_endpoints(self):
        """APIRouter(dependencies=[Depends(require_permission(...))]) 应覆盖本文件路由。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/organization/employees.py")
        )
        by_function = {ep["function"]: ep for ep in endpoints}

        assert by_function["read_employees"]["protection"] == "PERMISSION"
        assert by_function["read_employees"]["perm_code"] == "hr:read"
        assert by_function["read_employee"]["protection"] == "PERMISSION"
        assert by_function["read_employee"]["perm_code"] == "hr:read"
        assert by_function["get_employee_assignments"]["protection"] == "PERMISSION"
        assert by_function["get_employee_assignments"]["perm_code"] == "hr:read"
        assert by_function["create_employee"]["perm_code"] == "hr:create"

    def test_backup_admin_endpoints_have_permission(self):
        """备份/恢复/删除是高危运维动作，必须是 PERMISSION 级别。"""
        backup_endpoints = self._find_endpoints_in_file("endpoints/backup.py")

        assert backup_endpoints
        for ep in backup_endpoints:
            assert ep["protection"] == "PERMISSION", (
                f"备份端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )

    def test_company_certification_endpoints_have_permission(self):
        """公司资质证书接口属于售前资料库，不能无认证/无权限裸露。"""
        cert_endpoints = self._find_endpoints_in_file("company_certifications.py")

        assert cert_endpoints
        for ep in cert_endpoints:
            assert ep["protection"] == "PERMISSION", (
                f"公司资质证书端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )

    def test_presale_ai_knowledge_endpoints_have_permission(self):
        """售前 AI 知识库会读写案例/问答反馈，不能匿名裸露。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(str(ROOT / "app/api/v1/presale_ai_knowledge.py"))

        assert endpoints
        for ep in endpoints:
            assert ep["protection"] == "PERMISSION", (
                f"售前AI知识库端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )

    def test_presale_ai_emotion_endpoints_have_permission(self):
        """售前 AI 情绪分析会生成分析/提醒，不能匿名裸露。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(str(ROOT / "app/api/presale_ai_emotion.py"))

        assert endpoints
        for ep in endpoints:
            assert ep["protection"] == "PERMISSION", (
                f"售前AI情绪端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )

    def test_project_risk_endpoints_use_standard_project_permissions(self):
        """项目风险 CRUD/扫描应使用已初始化的 project:* 权限码。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/projects/risks.py")
        )
        expected_permissions = {
            "create_risk": "project:create",
            "get_risks": "project:read",
            "get_risk": "project:read",
            "update_risk": "project:update",
            "delete_risk": "project:delete",
            "get_risk_matrix": "project:read",
            "get_risk_summary": "project:read",
            "auto_scan_risks": "project:create",
        }

        by_function = {ep["function"]: ep for ep in endpoints}
        assert set(expected_permissions).issubset(by_function)

        for function_name, permission_code in expected_permissions.items():
            ep = by_function[function_name]
            assert ep["protection"] == "PERMISSION", (
                f"项目风险端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )
            assert ep["perm_code"] == permission_code, (
                f"项目风险端点权限码不匹配: {function_name} 当前 {ep['perm_code']}，"
                f"应为 {permission_code}"
            )

    def test_schedule_optimization_fallback_routes_have_permissions(self):
        """排程优化 fallback 路由已挂载到主 API，不能裸露自动写动作。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/schedule_optimization.py")
        )
        expected_permissions = {
            "read_root": "project:read",
            "get_optimization_analysis": "project:read",
            "auto_generate_bom": "material:update",
            "auto_create_purchase": "purchase:create",
        }

        by_function = {ep["function"]: ep for ep in endpoints}
        assert set(expected_permissions).issubset(by_function)

        for function_name, permission_code in expected_permissions.items():
            ep = by_function[function_name]
            assert ep["protection"] == "PERMISSION", (
                f"排程优化端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )
            assert ep["perm_code"] == permission_code, (
                f"排程优化端点权限码不匹配: {function_name} 当前 {ep['perm_code']}，"
                f"应为 {permission_code}"
            )

    def test_assembly_kit_scheduling_routes_have_write_permissions(self):
        """齐套排产建议生成/处理会写建议状态，不能裸露或只挂 read 权限。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/assembly_kit/scheduling.py")
        )
        expected_permissions = {
            "generate_scheduling_suggestions": "assembly_kit:create",
            "get_scheduling_suggestions": "assembly_kit:read",
            "accept_suggestion": "assembly_kit:update",
            "reject_suggestion": "assembly_kit:update",
        }

        by_function = {ep["function"]: ep for ep in endpoints}
        assert set(expected_permissions).issubset(by_function)

        for function_name, permission_code in expected_permissions.items():
            ep = by_function[function_name]
            assert ep["protection"] == "PERMISSION", (
                f"齐套排产建议端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )
            assert ep["perm_code"] == permission_code, (
                f"齐套排产建议端点权限码不匹配: {function_name} 当前 {ep['perm_code']}，"
                f"应为 {permission_code}"
            )

    def test_production_capacity_calculation_routes_have_manage_permission(self):
        """OEE/工人效率计算会落库生产记录，必须要求生产管理权限。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/production/capacity/calculation.py")
        )
        expected_permissions = {
            "calculate_oee": "production:manage",
            "calculate_worker_efficiency": "production:manage",
        }

        by_function = {ep["function"]: ep for ep in endpoints}
        assert set(expected_permissions).issubset(by_function)

        for function_name, permission_code in expected_permissions.items():
            ep = by_function[function_name]
            assert ep["protection"] == "PERMISSION", (
                f"产能计算端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )
            assert ep["perm_code"] == permission_code, (
                f"产能计算端点权限码不匹配: {function_name} 当前 {ep['perm_code']}，"
                f"应为 {permission_code}"
            )

    def test_organization_departments_refactored_routes_have_hr_permissions(self):
        """部门组织架构接口必须使用明确 HR 权限，不能只要求登录。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/organization/departments_refactored.py")
        )
        expected_permissions = {
            "read_departments": "hr:read",
            "get_department_tree": "hr:read",
            "get_department_statistics": "hr:read",
            "create_department": "hr:create",
            "read_department": "hr:read",
            "update_department": "hr:update",
            "delete_department": "hr:update",
            "get_department_users": "hr:read",
        }

        by_function = {ep["function"]: ep for ep in endpoints}
        assert set(expected_permissions).issubset(by_function)

        for function_name, permission_code in expected_permissions.items():
            ep = by_function[function_name]
            assert ep["protection"] == "PERMISSION", (
                f"部门端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )
            assert ep["perm_code"] == permission_code, (
                f"部门端点权限码不匹配: {function_name} 当前 {ep['perm_code']}，"
                f"应为 {permission_code}"
            )

    def test_organization_employee_import_routes_have_hr_permissions(self):
        """员工批量导入会新增/更新人事数据，必须使用明确 HR 权限。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/organization/employee_import.py")
        )
        expected_permissions = {
            "import_employees_from_excel": "hr:create",
            "download_import_template": "hr:read",
        }

        by_function = {ep["function"]: ep for ep in endpoints}
        assert set(expected_permissions).issubset(by_function)

        for function_name, permission_code in expected_permissions.items():
            ep = by_function[function_name]
            assert ep["protection"] == "PERMISSION", (
                f"员工导入端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )
            assert ep["perm_code"] == permission_code, (
                f"员工导入端点权限码不匹配: {function_name} 当前 {ep['perm_code']}，"
                f"应为 {permission_code}"
            )

    def test_gantt_dependency_routes_have_project_permissions(self):
        """甘特依赖会读写项目排期关系，不能只有登录态。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/gantt_dependency.py")
        )
        expected_permissions = {
            "get_gantt_data": "project:read",
            "add_dependency": "project:update",
            "delete_dependency": "project:update",
            "get_critical_path": "project:read",
        }

        by_function = {ep["function"]: ep for ep in endpoints}
        assert set(expected_permissions).issubset(by_function)

        for function_name, permission_code in expected_permissions.items():
            ep = by_function[function_name]
            assert ep["protection"] == "PERMISSION", (
                f"甘特依赖端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )
            assert ep["perm_code"] == permission_code, (
                f"甘特依赖端点权限码不匹配: {function_name} 当前 {ep['perm_code']}，"
                f"应为 {permission_code}"
            )

    def test_global_milestone_routes_have_milestone_permissions(self):
        """全局里程碑兼容路由已挂主 API，必须使用 milestone:* 权限。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(str(ROOT / "app/api/v1/endpoints/milestones.py"))
        expected_permissions = {
            "list_milestones": "milestone:read",
            "list_project_milestones_compat": "milestone:read",
            "get_milestone": "milestone:read",
            "create_milestone": "milestone:create",
            "update_milestone": "milestone:update",
            "complete_milestone": "milestone:update",
            "delete_milestone": "milestone:delete",
        }

        by_function = {ep["function"]: ep for ep in endpoints}
        assert set(expected_permissions).issubset(by_function)

        for function_name, permission_code in expected_permissions.items():
            ep = by_function[function_name]
            assert ep["protection"] == "PERMISSION", (
                f"里程碑端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )
            assert ep["perm_code"] == permission_code, (
                f"里程碑端点权限码不匹配: {function_name} 当前 {ep['perm_code']}，"
                f"应为 {permission_code}"
            )

    def test_lessons_learned_compat_routes_have_project_evaluation_permissions(self):
        """经验教训兼容路由读写 ProjectLesson，应使用项目复盘权限。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/lessons_learned.py")
        )
        expected_permissions = {
            "list_lessons": "project_evaluation:read",
            "lesson_stats": "project_evaluation:read",
            "search_lessons": "project_evaluation:read",
            "lesson_detail": "project_evaluation:read",
            "create_lesson": "project_evaluation:create",
            "update_lesson": "project_evaluation:update",
            "delete_lesson": "project_evaluation:update",
        }

        by_function = {ep["function"]: ep for ep in endpoints}
        assert set(expected_permissions).issubset(by_function)

        for function_name, permission_code in expected_permissions.items():
            ep = by_function[function_name]
            assert ep["protection"] == "PERMISSION", (
                f"经验教训端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )
            assert ep["perm_code"] == permission_code, (
                f"经验教训端点权限码不匹配: {function_name} 当前 {ep['perm_code']}，"
                f"应为 {permission_code}"
            )

    def test_engineer_scheduling_routes_have_task_permissions(self):
        """工程师排产路由会读写任务分配/能力/预警，应使用 task:* 权限。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/engineer_scheduling.py")
        )
        expected_permissions = {
            "create_assignment": "task:create",
            "update_assignment": "task:update",
            "delete_assignment": "task:delete",
            "get_workload_board": "task:read",
            "get_engineer_availability": "task:read",
            "get_engineer_capacity": "task:read",
            "update_engineer_capacity": "task:update",
            "analyze_workload": "task:read",
            "detect_conflicts": "task:read",
            "generate_warnings": "task:update",
            "get_scheduling_report": "task:read",
            "evaluate_ai_capability": "task:read",
            "update_ai_capability": "task:update",
            "evaluate_core_capabilities": "task:read",
            "update_core_capabilities": "task:update",
        }

        by_function = {ep["function"]: ep for ep in endpoints}
        assert set(expected_permissions).issubset(by_function)

        for function_name, permission_code in expected_permissions.items():
            ep = by_function[function_name]
            assert ep["protection"] == "PERMISSION", (
                f"工程师排产端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )
            assert ep["perm_code"] == permission_code, (
                f"工程师排产端点权限码不匹配: {function_name} 当前 {ep['perm_code']}，"
                f"应为 {permission_code}"
            )

    def test_progress_compat_routes_have_task_permissions(self):
        """旧进度兼容路由已挂 /progress，任务/WBS/自动处理必须使用 task:* 权限。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/progress_compat.py")
        )
        expected_permissions = {
            "list_project_tasks": "task:read",
            "create_project_task": "task:create",
            "get_task": "task:read",
            "get_project_progress_forecast": "task:read",
            "check_project_dependencies": "task:read",
            "preview_auto_processing": "task:read",
            "apply_forecast_auto_processing": "task:update",
            "fix_dependencies_auto_processing": "task:update",
            "run_complete_auto_processing": "task:update",
            "batch_auto_process": "task:update",
            "list_wbs_templates": "task:read",
            "create_wbs_template": "task:create",
            "get_wbs_template": "task:read",
            "update_wbs_template": "task:update",
            "delete_wbs_template": "task:delete",
            "list_wbs_template_tasks": "task:read",
            "create_wbs_template_task": "task:create",
            "update_wbs_template_task": "task:update",
            "get_milestone_rate_report": "task:read",
            "get_delay_reasons_report": "task:read",
        }

        by_function = {ep["function"]: ep for ep in endpoints}
        assert set(expected_permissions).issubset(by_function)

        for function_name, permission_code in expected_permissions.items():
            ep = by_function[function_name]
            assert ep["protection"] == "PERMISSION", (
                f"进度兼容端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )
            assert ep["perm_code"] == permission_code, (
                f"进度兼容端点权限码不匹配: {function_name} 当前 {ep['perm_code']}，"
                f"应为 {permission_code}"
            )

    def test_admin_compat_routes_have_admin_permissions(self):
        """行政兼容路由是后台管理面，不能只校验登录态。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/admin_compat.py")
        )
        expected_permissions = {
            "get_admin_stats": "user:read",
            "list_supplies": "user:read",
            "get_supplies_inventory": "user:read",
            "create_supply_request": "user:create",
            "approve_supply_request": "user:update",
            "reject_supply_request": "user:update",
            "get_supply": "user:read",
            "list_vehicles": "user:read",
            "list_available_vehicles": "user:read",
            "create_vehicle_request": "user:create",
            "approve_vehicle_request": "user:update",
            "reject_vehicle_request": "user:update",
            "get_vehicle": "user:read",
            "list_assets": "user:read",
            "get_asset_statistics": "user:read",
            "create_asset": "user:create",
            "update_asset": "user:update",
            "delete_asset": "user:delete",
            "get_asset": "user:read",
            "list_expenses": "user:read",
            "get_expense_statistics": "user:read",
        }

        by_function = {ep["function"]: ep for ep in endpoints}
        assert set(expected_permissions).issubset(by_function)

        for function_name, permission_code in expected_permissions.items():
            ep = by_function[function_name]
            assert ep["protection"] == "PERMISSION", (
                f"行政兼容端点缺少权限保护: {ep['method']} {ep['path']} "
                f"in {ep['file']}:{ep['line']} (当前: {ep['protection']})"
            )
            assert ep["perm_code"] == permission_code, (
                f"行政兼容端点权限码不匹配: {function_name} 当前 {ep['perm_code']}，"
                f"应为 {permission_code}"
            )


class TestWhitelistMinimality:
    """白名单路由应该尽可能少"""

    def test_auth_middleware_whitelist_size(self):
        """认证中间件白名单数量不应超过预期"""
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware

        # 严格限制白名单大小
        assert len(GlobalAuthMiddleware.WHITE_LIST) <= 10, (
            f"白名单过大: {len(GlobalAuthMiddleware.WHITE_LIST)} 条目。"
            f"当前白名单: {GlobalAuthMiddleware.WHITE_LIST}"
        )

    def test_whitelist_no_api_endpoints(self):
        """白名单中不应有 /api/v1/ 业务端点 (除 login/refresh)"""
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware

        allowed_api = {"/api/v1/auth/login", "/api/v1/auth/refresh", "/api/health"}
        for path in GlobalAuthMiddleware.WHITE_LIST:
            if path.startswith("/api/"):
                assert path in allowed_api, (
                    f"白名单中发现非预期 API 端点: {path}"
                )


class TestEndpointScanConsistency:
    """扫描结果内部一致性"""

    def test_unmounted_async_crud_router_factory_is_not_scanned_as_endpoint(self):
        """未挂载的异步 CRUD route factory 不应污染真实 API 权限风险列表。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        endpoints = extract_endpoints_from_file(
            str(ROOT / "app/api/v1/endpoints/base_crud_router.py")
        )

        assert endpoints == []

    def test_lazy_only_material_fusion_files_are_not_scanned_as_strict_endpoints(self):
        """未挂主应用的 material legacy/lazy 文件不应进入当前严格路由审计。"""
        from scripts.audit_permission_coverage import extract_endpoints_from_file

        for relative_path in (
            "app/api/v1/endpoints/material/tracking.py",
            "app/api/v1/endpoints/material/project_fusion.py",
        ):
            endpoints = extract_endpoints_from_file(str(ROOT / relative_path))
            assert endpoints == []

    @pytest.fixture(autouse=True)
    def load_audit(self):
        json_path = ROOT / "PERMISSION_COVERAGE_AUDIT.json"
        if not json_path.exists():
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "audit_permission_coverage.py"), "--json-only"],
                cwd=str(ROOT),
                timeout=60,
            )
        with open(json_path) as f:
            self.audit = json.load(f)

    def test_protection_values_valid(self):
        """所有端点的 protection 字段必须是已知值"""
        valid = {"PERMISSION", "AUTH_ONLY", "NONE"}
        for ep in self.audit["all_endpoints"]:
            assert ep["protection"] in valid, (
                f"未知 protection 值: {ep['protection']} in {ep['file']}:{ep['line']}"
            )

    def test_method_values_valid(self):
        """所有端点的 method 字段必须是标准 HTTP 方法"""
        valid = {"GET", "POST", "PUT", "DELETE", "PATCH"}
        for ep in self.audit["all_endpoints"]:
            assert ep["method"] in valid, (
                f"未知 HTTP 方法: {ep['method']} in {ep['file']}:{ep['line']}"
            )

    def test_permission_code_format(self):
        """权限码格式应为 module:action 或 UPPER_CASE"""
        import re
        for ep in self.audit["all_endpoints"]:
            code = ep.get("perm_code")
            if code:
                valid = (
                    re.match(r'^[a-z][a-z0-9_]*:[a-z][a-z0-9_:]*$', code) or
                    re.match(r'^[A-Z][A-Z0-9_]+$', code)
                )
                assert valid, (
                    f"权限码格式异常: '{code}' in {ep['file']}:{ep['line']}"
                )

    def test_total_matches_breakdown(self):
        """总数应等于各保护级别之和"""
        s = self.audit["summary"]
        total = s["total_endpoints"]
        breakdown = sum(s["by_protection"].values())
        assert total == breakdown, f"总数 {total} != 各级别之和 {breakdown}"
