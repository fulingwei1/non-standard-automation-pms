# -*- coding: utf-8 -*-
"""
商务支持模块 API 路由聚合
"""

from fastapi import APIRouter

from app.api.v1.endpoints.business_support import (
    bidding,
    contract_review,
    contract_seal,
    dashboard,
    document_archive,
    payment_reminders,
)

router = APIRouter()

# 注册子模块路由
router.include_router(dashboard.router, tags=["商务支持-工作台"])
router.include_router(bidding.router, prefix="/bidding", tags=["商务支持-投标管理"])
router.include_router(contract_review.router, prefix="/contracts", tags=["商务支持-合同审核"])
router.include_router(contract_seal.router, prefix="/contracts", tags=["商务支持-合同盖章"])
router.include_router(payment_reminders.router, prefix="/payment-reminders", tags=["商务支持-回款催收"])
router.include_router(document_archive.router, prefix="/archives", tags=["商务支持-文件归档"])
