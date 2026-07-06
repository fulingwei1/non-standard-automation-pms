# -*- coding: utf-8 -*-
"""presale 模块（售前）：评估/AI 报价/方案/技术评估/需求提取。

模块化单体首个试点模块（迁移记录见 docs/refactor/MODULE_MAP.md §9 P2）。
公共接口按 MODULE_CONVENTIONS §3 从本文件导出；其他模块只许 import 这里
导出的名字，不许深入 services/models 内部。
"""

from app.modules.presale.manifest import MANIFEST  # noqa: F401
