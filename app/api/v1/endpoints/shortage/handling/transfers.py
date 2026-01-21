"""
物料调拨 - transfers.py

路由:
- GET    /                          调拨列表
- POST   /                          创建调拨
- GET    /{id}                      调拨详情
- PUT    /{id}/approve              审批
- PUT    /{id}/execute              执行
"""
from fastapi import APIRouter

router = APIRouter()

# TODO: Phase 2 实现
