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
