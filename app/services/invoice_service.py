# -*- coding: utf-8 -*-
"""
发票服务 - 存根实现
用于解决模块依赖问题
"""

from datetime import datetime


class InvoiceService:
    """发票服务类 - 存根实现"""

    @staticmethod
    async def generate_code() -> str:
        """生成发票代码"""
        return f"INV{datetime.now().strftime('%Y%m%d%H%M%S')}"