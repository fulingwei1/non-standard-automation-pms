"""
物料替代 - substitutions.py

路由:
- GET    /                          替代列表
- POST   /                          创建替代申请
- GET    /{id}                      替代详情
- PUT    /{id}/tech-approve         技术审批
- PUT    /{id}/prod-approve         生产审批
- PUT    /{id}/execute              执行替代
"""
from fastapi import APIRouter

router = APIRouter()

# TODO: Phase 2 实现
