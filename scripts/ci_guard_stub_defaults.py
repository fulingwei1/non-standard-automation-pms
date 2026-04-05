#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI guard: 防止把 Stub 默认配置改回危险状态。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = ROOT / ".env.example"
API_FILE = ROOT / "app" / "api" / "v1" / "api.py"

errors: list[str] = []

if not ENV_EXAMPLE.exists():
    errors.append("缺少 .env.example")
else:
    env_text = ENV_EXAMPLE.read_text(encoding="utf-8")
    if "ENABLE_STUB_ENDPOINTS=false" not in env_text:
        errors.append(".env.example 必须默认 ENABLE_STUB_ENDPOINTS=false")
    if "ALLOW_STUB_SUCCESS=false" not in env_text:
        errors.append(".env.example 必须默认 ALLOW_STUB_SUCCESS=false")

if not API_FILE.exists():
    errors.append("缺少 app/api/v1/api.py")
else:
    api_text = API_FILE.read_text(encoding="utf-8")
    if 'ENABLE_STUB_ENDPOINTS = os.getenv("ENABLE_STUB_ENDPOINTS", "false")' not in api_text:
        errors.append("api.py 中 ENABLE_STUB_ENDPOINTS 默认值必须为 false")

if errors:
    print("❌ Stub 默认配置检查失败:")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)

print("✅ Stub 默认配置检查通过")
