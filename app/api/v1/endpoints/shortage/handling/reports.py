"""
缺料上报 - reports.py

路由:
- GET    /                          上报列表
- POST   /                          创建上报
- GET    /{id}                      上报详情
- PUT    /{id}/confirm              确认
- PUT    /{id}/handle               处理中
- PUT    /{id}/resolve              解决
"""
from fastapi import APIRouter

router = APIRouter()

# TODO: Phase 2 实现
