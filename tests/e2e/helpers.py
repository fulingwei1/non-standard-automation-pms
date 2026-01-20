# -*- coding: utf-8 -*-
"""
E2E测试辅助工具
"""

import json
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """处理Decimal类型的JSON编码器"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def json_dumps_decimal(obj):
    """带Decimal处理的json.dumps"""
    return json.dumps(obj, cls=DecimalEncoder)
