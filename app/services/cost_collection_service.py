# -*- coding: utf-8 -*-
"""兼容旧导入路径：app.services.cost_collection_service。"""

import sys

from app.services.cost import cost_collection_service as _impl

sys.modules[__name__] = _impl
