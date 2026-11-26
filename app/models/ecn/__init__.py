# -*- coding: utf-8 -*-
"""兼容旧导入路径：实现已迁至 app.modules.ecn.models（P2 模块化，一个迭代周期后删除本 shim）。"""
import importlib
import pkgutil
import sys

_impl = importlib.import_module("app.modules.ecn.models")
sys.modules[__name__] = _impl

for _m in pkgutil.walk_packages(_impl.__path__, prefix="app.modules.ecn.models."):
    try:
        _mod = importlib.import_module(_m.name)
    except Exception:
        continue
    sys.modules[_m.name.replace("app.modules.ecn.models", "app.models.ecn")] = _mod
