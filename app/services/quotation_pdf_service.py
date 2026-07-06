# -*- coding: utf-8 -*-
"""兼容旧导入路径：实现已迁至 app.modules.presale.services.quotation_pdf_service（P2 模块化）。"""
import sys

from app.modules.presale.services import quotation_pdf_service as _impl

sys.modules[__name__] = _impl
