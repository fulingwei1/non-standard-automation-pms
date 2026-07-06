# -*- coding: utf-8 -*-
"""兼容旧导入路径：实现已迁至 app.modules.presale.api.quotes.quote_delivery（P2 模块化批D）。"""
import sys

import app.modules.presale.api.quotes.quote_delivery as _impl

sys.modules[__name__] = _impl
