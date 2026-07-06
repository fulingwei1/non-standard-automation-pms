# -*- coding: utf-8 -*-
"""兼容旧导入路径：实现已迁至 app.modules.presale.services.technical_assessment_service（P2 模块化）。"""
import sys

from app.modules.presale.services import technical_assessment_service as _impl

sys.modules[__name__] = _impl
