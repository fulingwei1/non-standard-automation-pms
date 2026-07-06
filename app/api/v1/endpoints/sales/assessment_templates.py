# -*- coding: utf-8 -*-
"""兼容旧导入路径：实现已迁至 app.modules.presale.api.assessments.assessment_templates（P2 模块化批D）。"""
import sys

import app.modules.presale.api.assessments.assessment_templates as _impl

sys.modules[__name__] = _impl
