# -*- coding: utf-8 -*-
"""兼容旧导入路径：实现已迁至 app.modules.presale.api（P2 模块化，一个迭代周期后删除本 shim）。

将新包及其全部子模块别名到旧路径，避免同一文件在两个模块名下被二次执行
（否则 ORM 表会重复注册）。
"""
import importlib
import pkgutil
import sys

_impl = importlib.import_module("app.modules.presale.api")
sys.modules[__name__] = _impl

for _m in pkgutil.walk_packages(_impl.__path__, prefix="app.modules.presale.api."):
    try:
        _mod = importlib.import_module(_m.name)
    except Exception:  # 子模块自身的可选依赖问题不应破坏别名层
        continue
    sys.modules[_m.name.replace("app.modules.presale.api", "app.api.v1.endpoints.presale")] = _mod
