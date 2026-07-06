# -*- coding: utf-8 -*-
"""兼容旧导入路径：实现已迁至 app.modules.presale.models.presale_emotion_trend（P2 模块化批C）。"""
import sys

from app.modules.presale.models import presale_emotion_trend as _impl

sys.modules[__name__] = _impl
