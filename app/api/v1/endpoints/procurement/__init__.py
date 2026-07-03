# -*- coding: utf-8 -*-
"""采购分析包。

2026-07-03 去重：原聚合 router（suppliers/price-analysis/kitting-analysis）从未挂载于活动注册表，
其中 suppliers 与顶层 /suppliers 重复且已标 deprecated，price/kitting 分析无消费方，均已下线。
现仅保留被 api.py 直连挂载的 analysis（/procurement-analysis）与 supplier_price_trend（/supplier-price）。
"""
