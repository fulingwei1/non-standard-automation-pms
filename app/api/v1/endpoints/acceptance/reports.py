# -*- coding: utf-8 -*-
"""
验收报告与签字管理端点 - 路由聚合

已拆分为模块化结构：
- signatures.py: 验收签字管理（list, create）
- report_generation.py: 报告生成和下载（generate, download, list）
- signed_documents.py: 客户签署文件管理（upload, download）
- bonus_trigger.py: 奖金计算触发
"""

from fastapi import APIRouter

from . import bonus_trigger, report_generation, report_generation_unified, signatures, signed_documents

router = APIRouter()

# 聚合所有子路由
router.include_router(signatures.router)
router.include_router(report_generation.router)
router.include_router(signed_documents.router)
router.include_router(bonus_trigger.router)
