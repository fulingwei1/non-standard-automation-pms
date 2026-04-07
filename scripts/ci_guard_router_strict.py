#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI guard: 确保 api.py 的 except 块不会悄悄回退为“只打印不处理”。

规则：
- 每个 `except Exception as e:` 块都必须包含以下之一：
  1) `if STRICT_API_ROUTER:`（严格模式分支）
  2) 直接 `raise RuntimeError(`

目的：避免新增/回退为吞错启动。
"""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "app" / "api" / "v1" / "api.py"


def main() -> int:
    if not TARGET.exists():
        print(f"❌ 文件不存在: {TARGET}")
        return 1

    lines = TARGET.read_text(encoding="utf-8").splitlines()
    issues: list[str] = []

    for i, line in enumerate(lines):
        if line.strip().startswith("except Exception as e:"):
            indent = len(line) - len(line.lstrip(" "))
            block = []
            j = i + 1
            while j < len(lines):
                cur = lines[j]
                # 到同级或更低缩进，认为 except block 结束
                if cur.strip() and (len(cur) - len(cur.lstrip(" "))) <= indent:
                    break
                block.append(cur)
                j += 1

            block_text = "\n".join(block)
            has_strict = "if STRICT_API_ROUTER:" in block_text
            has_raise = bool(re.search(r"\braise\s+RuntimeError\(", block_text))

            if not (has_strict or has_raise):
                # 找最近的分段注释方便定位
                sec = "(unknown section)"
                for k in range(i - 1, max(i - 30, -1), -1):
                    s = lines[k].strip()
                    if s.startswith("# ===================="):
                        sec = s.strip("# ")
                        break
                issues.append(f"line {i+1} [{sec}]")

    if issues:
        print("❌ api.py 发现可能吞错的 except 块（缺少 STRICT_API_ROUTER/RuntimeError）:")
        for item in issues:
            print(f"  - {item}")
        return 1

    print("✅ api.py except 块严格策略检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
