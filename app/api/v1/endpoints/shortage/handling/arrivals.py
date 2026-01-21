"""
到货跟踪 - arrivals.py

路由:
- GET    /                          到货列表
- POST   /                          创建到货记录
- GET    /{id}                      到货详情
- PUT    /{id}/status               更新状态
- POST   /{id}/follow-up            创建跟催
- POST   /{id}/receive              确认收货
"""
from fastapi import APIRouter

router = APIRouter()

# TODO: Phase 2 实现
