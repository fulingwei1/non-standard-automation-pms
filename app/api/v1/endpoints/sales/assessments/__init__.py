# -*- coding: utf-8 -*-
"""兼容旧导入路径：实现已迁至 app.modules.presale.api.assessments（P2 模块化批D）。"""
import importlib
import pkgutil
import sys

_impl = importlib.import_module("app.modules.presale.api.assessments")
sys.modules[__name__] = _impl

for _m in pkgutil.walk_packages(_impl.__path__, prefix="app.modules.presale.api.assessments."):
    try:
        _mod = importlib.import_module(_m.name)
    except Exception:
        continue
    sys.modules[_m.name.replace("app.modules.presale.api.assessments", "app.api.v1.endpoints.sales.assessments")] = _mod
