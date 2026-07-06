# -*- coding: utf-8 -*-
"""兼容旧导入路径：实现已迁至 app.modules.presale.services.ai_emotion_service（P2 模块化）。"""
import sys

from app.modules.presale.services import ai_emotion_service as _impl

sys.modules[__name__] = _impl
