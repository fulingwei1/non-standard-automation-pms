# -*- coding: utf-8 -*-
"""兼容旧导入路径：实现已迁至 app.modules.presale.models.advantage_product（P2 模块化批C）。"""
import sys

from app.modules.presale.models import advantage_product as _impl

sys.modules[__name__] = _impl
