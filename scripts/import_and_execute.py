#!/usr/bin/env python
"""导入所有 app 模块，验证导入链是否可用。"""

import importlib
import os
import sys
import traceback

sys.path.insert(0, ".")

modules = []
for root, dirs, files in os.walk("app"):
    dirs[:] = [d for d in dirs if d not in ["tests", "__pycache__", "migrations"]]
    for f in files:
        if f.endswith(".py") and not f.startswith("test_"):
            path = os.path.join(root, f)
            mod = path.replace("/", ".").replace(".py", "")
            modules.append(mod)

modules.sort()
print(f"Total: {len(modules)}")

success = 0
failures = []
for mod in modules:
    try:
        importlib.import_module(mod)
        success += 1
    except Exception as exc:
        failures.append((mod, exc))
        print(f"IMPORT_FAIL {mod}: {exc}")

print(f"Success: {success}/{len(modules)}")
if failures:
    print(f"Failures: {len(failures)}")
    for mod, exc in failures:
        print(f"- {mod}: {exc}")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
else:
    print("Failures: 0")
