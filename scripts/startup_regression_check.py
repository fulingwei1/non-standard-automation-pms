#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动回归检查（不依赖 HTTP 请求）。

用途：
1) 快速验证 strict 模式下路由是否可完整加载
2) 输出路由数量和失败摘要

用法：
  python scripts/startup_regression_check.py --strict true
  python scripts/startup_regression_check.py --strict false --enable-stub false
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
import traceback


def parse_bool(v: str) -> bool:
    return v.strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", default="true", help="STRICT_API_ROUTER")
    parser.add_argument("--enable-stub", default="false", help="ENABLE_STUB_ENDPOINTS")
    parser.add_argument("--allow-stub-success", default="false", help="ALLOW_STUB_SUCCESS")
    args = parser.parse_args()

    os.environ["STRICT_API_ROUTER"] = "true" if parse_bool(args.strict) else "false"
    os.environ["ENABLE_STUB_ENDPOINTS"] = "true" if parse_bool(args.enable_stub) else "false"
    os.environ["ALLOW_STUB_SUCCESS"] = "true" if parse_bool(args.allow_stub_success) else "false"

    print("[startup-regression] env:")
    print(f"  STRICT_API_ROUTER={os.environ['STRICT_API_ROUTER']}")
    print(f"  ENABLE_STUB_ENDPOINTS={os.environ['ENABLE_STUB_ENDPOINTS']}")
    print(f"  ALLOW_STUB_SUCCESS={os.environ['ALLOW_STUB_SUCCESS']}")

    try:
        # 触发路由加载
        api_mod = importlib.import_module("app.api.v1.api")
        api_router = getattr(api_mod, "api_router", None)
        route_count = len(api_router.routes) if api_router else -1

        # 触发主应用加载
        main_mod = importlib.import_module("app.main")
        app = getattr(main_mod, "app", None)
        app_routes = len(app.routes) if app else -1

        print("[startup-regression] OK")
        print(f"  api_router.routes={route_count}")
        print(f"  app.routes={app_routes}")
        return 0
    except Exception as e:  # noqa: BLE001
        print("[startup-regression] FAILED")
        print(f"  error={e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
