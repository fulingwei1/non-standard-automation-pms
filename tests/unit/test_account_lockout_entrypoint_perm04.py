# -*- coding: utf-8 -*-
"""PERM-04: 账号锁定只能保留真实登录链路使用的 Service 入口。"""

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _import_sources(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_core_in_memory_account_lockout_module_removed():
    assert not (PROJECT_ROOT / "app/core/account_lockout.py").exists()


def test_auth_login_uses_service_account_lockout_entrypoint_only():
    imports = _import_sources(PROJECT_ROOT / "app/api/v1/endpoints/auth.py")

    assert "app.services.account_lockout_service" in imports
    assert "app.core.account_lockout" not in imports
